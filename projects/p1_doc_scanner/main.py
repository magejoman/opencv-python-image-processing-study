"""P1. 문서 스캐너 — 비스듬히 찍은 종이 사진 → 반듯한 스캔본

실행 (어느 폴더에서 실행해도 된다):
    python main.py                  # config 의 input.folder 전부 처리 → results/
    python main.py --input 사진.jpg  # 특정 파일 또는 폴더만
    python main.py --manual         # 자동 검출 실패 시 마우스로 꼭짓점 찍기 (Step 7)
    python main.py --tune           # 첫 이미지로 검출 파라미터 튜닝 (Step 2)
    python main.py --compare        # 직접 구현 vs OpenCV 정확도·속도 비교 (Step 4~6)
    python main.py --show           # 이미지마다 중간 결과를 창으로 보기

결과:
    results/stages/*.jpg   이미지별 중간 결과 모자이크 (어디서 망가졌는지 보기)
    results/scans/*.png    최종 스캔본
    results/summary.csv    이미지별 지표 (성공 여부, 꼭짓점 오차, 시간 …)

이 파일은 '조립' 만 한다. 알고리즘은 scanner/ 에서 직접 구현한다 (GUIDE.md).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from cvkit import (Param, Project, Stages, Table, Timer, benchmark, compare, imread, imwrite, list_images,
                   speed_table, tune)
from scanner.corners import order_corners, quad_size
from scanner.detect import find_document_quad
from scanner.enhance import adaptive_threshold
from scanner.evaluate import corner_error, load_gt
from scanner.homography import homography_dlt
from scanner.ui import pick_corners
from scanner.warp import warp_perspective

proj = Project(__file__)
cfg = proj.config

# config 의 impl 설정으로 직접 구현과 OpenCV 를 바꿔 끼운다
HOMOGRAPHY = {"mine": homography_dlt, "opencv": cv2.getPerspectiveTransform}
WARP = {"mine": warp_perspective, "opencv": lambda img, H, size: cv2.warpPerspective(img, H, size)}
THRESHOLD = {
    "mine": adaptive_threshold,
    "opencv": lambda gray, block, C: cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                           cv2.THRESH_BINARY, block, C),
}


# ---------------------------------------------------------------------------------------------- 조립
def shrink(img: np.ndarray) -> tuple[np.ndarray, float]:
    """검출용으로 줄인 이미지와 배율. 검출은 작게, 펼치기는 원본 해상도로 한다."""
    scale = min(1.0, cfg.input.max_side / max(img.shape[:2]))
    if scale == 1.0:
        return img, scale
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA), scale


def draw_quads(img: np.ndarray, quad=None, gt=None) -> np.ndarray:
    """검출 결과(초록)와 정답(빨강 점선 느낌의 얇은 선)을 겹쳐 그린다. 좌표는 img 기준."""
    out = img.copy()
    if gt is not None:
        cv2.polylines(out, [np.round(gt).astype(np.int32)], True, (0, 0, 255), 1, cv2.LINE_AA)
    if quad is not None:
        cv2.polylines(out, [np.round(quad).astype(np.int32)], True, (0, 255, 0), 2, cv2.LINE_AA)
        for name, (x, y) in zip(["TL", "TR", "BR", "BL"], quad):
            cv2.circle(out, (round(x), round(y)), 5, (0, 255, 0), -1)
            cv2.putText(out, name, (round(x) + 6, round(y) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return out


def target_rect(quad: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    """펼칠 목표 직사각형의 네 꼭짓점과 크기 (w, h)."""
    w, h = quad_size(quad)
    s = min(1.0, cfg.output.max_side / max(w, h))
    w, h = max(2, round(w * s)), max(2, round(h * s))
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], np.float32)
    return dst, (w, h)


def process(img: np.ndarray, gt=None, manual: bool = False):
    """사진 한 장 처리. 돌려주는 값: (Stages, 결과표 한 줄 dict, 스캔본 또는 None)"""
    st = Stages()
    small, scale = shrink(img)
    st.add("원본 (검출용 축소)", small)

    row = {"how": "auto"}
    quad_small = find_document_quad(small, **cfg.detect, stages=st)                       # Step 2
    if quad_small is None and manual:                                                      # Step 7
        picked = pick_corners(small, window="manual")
        if isinstance(picked, str):
            raise KeyboardInterrupt
        quad_small, row["how"] = picked, "manual"
    row["found"] = quad_small is not None
    if quad_small is None:
        st.add("검출 실패", draw_quads(small, gt=None if gt is None else gt * scale))
        return st, row, None

    quad = order_corners(quad_small) / scale                                               # Step 3
    st.add("검출 (초록) / 정답 (빨강)", draw_quads(small, quad * scale, None if gt is None else gt * scale))
    if gt is not None:
        row.update(corner_error(quad, gt))
        row["success"] = row["err_mean_px"] <= cfg.eval.success_px

    dst, size = target_rect(quad)
    H = HOMOGRAPHY[cfg.impl.homography](quad.astype(np.float32), dst)                     # Step 4
    warped = st.add(f"펼침 {size[0]}x{size[1]}", WARP[cfg.impl.warp](img, H, size))         # Step 5
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    scan = st.add("스캔", THRESHOLD[cfg.impl.threshold](gray, cfg.output.threshold_block,   # Step 6
                                                         cfg.output.threshold_C))
    return st, row, scan


# ---------------------------------------------------------------------------------------------- 모드
def run_batch(paths: list[Path], manual: bool, show: bool):
    table = Table()
    gt_cache, meta_cache = {}, {}
    for path in paths:
        folder = path.parent
        if folder not in gt_cache:
            gt_cache[folder] = load_gt(folder)
            meta_file = folder / "meta.json"
            meta_cache[folder] = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.is_file() else {}
        gt = gt_cache[folder].get(path.name)

        img = imread(path)
        with Timer(verbose=False) as t:
            st, row, scan = process(img, gt, manual)
        if cfg.output.save_stages:
            st.save(proj.result_path("stages", f"{path.stem}.jpg"))
        if scan is not None:
            imwrite(proj.result_path("scans", f"{path.stem}.png"), scan)
        if show and st.show(path.name) == 27:
            show = False
        table.add(file=path.name, **row, ms=t.ms, **meta_cache[folder].get(path.name, {}))
        if not row["found"]:
            status = "검출 실패"
        elif "success" in row:
            status = f"{'성공' if row['success'] else '부정확'} (평균 오차 {row['err_mean_px']:.1f}px)"
        else:
            status = "검출 (정답 없음)"
        print(f"  {path.name}: {status}")

    print("\n" + str(table))
    table.save_csv(proj.result_path("summary.csv"))
    table.save_markdown(proj.result_path("summary.md"))
    print(f"\n== 요약: {len(table)}장, 검출률 {table.mean('found'):.0%}", end="")
    if "success" in table.columns:
        print(f", 성공률 {table.mean('success'):.0%} (평균 오차 {cfg.eval.success_px}px 이하)", end="")
    print(f"\n결과: {proj.results}")


def run_tune(path: Path):
    small, _ = shrink(imread(path))

    def view(im, **params):
        st = Stages()
        quad = find_document_quad(im, **params, stages=st)
        st.add("결과" if quad is not None else "결과: 못 찾음", draw_quads(im, None if quad is None else quad))
        return st

    tune(small, view, Param.from_config(cfg.detect, cfg.tune),
         fixed={k: v for k, v in cfg.detect.items() if k not in cfg.tune},
         save_path=proj.result_path("tuned_params.yaml"))
    print("마음에 드는 값을 config.yaml 의 detect 에 옮겨 적으세요.")


def run_compare(path: Path):
    """직접 구현과 OpenCV 를 같은 입력으로 돌려 정확도·속도를 비교한다."""
    img = imread(path)
    gt = load_gt(path.parent).get(path.name)
    if gt is None:
        small, scale = shrink(img)
        q = find_document_quad(small, **cfg.detect)
        if q is None:
            sys.exit("정답도 없고 검출도 실패해서 비교할 사각형이 없습니다.")
        gt = order_corners(q) / scale
    quad = np.asarray(gt, np.float32)
    dst, size = target_rect(quad)
    out = proj.result_path("compare", "x").parent
    print(f"입력: {path.name}, 출력 크기 {size}\n")

    try:                                                                                   # Step 4
        H_cv = cv2.getPerspectiveTransform(quad, dst)
        H_my = homography_dlt(quad, dst)
        print(f"[호모그래피] 최대 원소 차이 {np.abs(H_my / H_my[2, 2] - H_cv).max():.3e}")
        print(speed_table(benchmark(homography_dlt, quad, dst, name="mine", verbose=False),
                          benchmark(cv2.getPerspectiveTransform, quad, dst, name="opencv", verbose=False)), "\n")
    except NotImplementedError as e:
        print(f"[호모그래피] 건너뜀 — {e}\n")
        H_cv = cv2.getPerspectiveTransform(quad, dst)

    try:                                                                                   # Step 5
        w_my, w_cv = warp_perspective(img, H_cv, size), cv2.warpPerspective(img, H_cv, size)
        r = compare(w_my, w_cv, tol=1, name="워핑 mine vs opencv")
        imwrite(out / "warp_diff.png", r.heatmap())
        print(speed_table(benchmark(warp_perspective, img, H_cv, size, name="mine", repeat=3, warmup=1, verbose=False),
                          benchmark(cv2.warpPerspective, img, H_cv, size, name="opencv", repeat=10, verbose=False)), "\n")
    except NotImplementedError as e:
        print(f"[워핑] 건너뜀 — {e}\n")
        w_cv = cv2.warpPerspective(img, H_cv, size)

    try:                                                                                   # Step 6
        gray = cv2.cvtColor(w_cv, cv2.COLOR_BGR2GRAY)
        b, C = cfg.output.threshold_block, cfg.output.threshold_C
        t_my, t_cv = adaptive_threshold(gray, b, C), THRESHOLD["opencv"](gray, b, C)
        r = compare(t_my, t_cv, tol=0, name="적응형 이진화 mine vs opencv")
        imwrite(out / "threshold_diff.png", r.heatmap())
        print(speed_table(benchmark(adaptive_threshold, gray, b, C, name="mine", repeat=5, verbose=False),
                          benchmark(THRESHOLD["opencv"], gray, b, C, name="opencv", verbose=False)))
    except NotImplementedError as e:
        print(f"[이진화] 건너뜀 — {e}")
    print(f"\n차이 히트맵: {out}")


def main():
    ap = argparse.ArgumentParser(description="P1. 문서 스캐너")
    ap.add_argument("--input", help="이미지 파일 또는 폴더 (생략하면 config 의 input.folder)")
    ap.add_argument("--manual", action="store_true", help="자동 검출 실패 시 마우스로 꼭짓점 찍기")
    ap.add_argument("--tune", action="store_true", help="첫 이미지로 검출 파라미터 튜닝")
    ap.add_argument("--compare", action="store_true", help="첫 이미지로 직접 구현 vs OpenCV 비교")
    ap.add_argument("--show", action="store_true", help="이미지마다 중간 결과를 창으로 보기")
    args = ap.parse_args()

    if args.input:
        p = Path(args.input)
        paths = list_images(p) if p.is_dir() else [p]
    else:
        folder = proj.path(cfg.input.folder)
        paths = list_images(folder) if folder.is_dir() else []
    if not paths:
        print(f"처리할 이미지가 없습니다 ({proj.path(cfg.input.folder)}).\n"
              f"합성 데이터 만들기: python {proj.name}/tools/make_synthetic.py  (GUIDE.md §1)")
        return

    try:
        if args.tune:
            run_tune(paths[0])
        elif args.compare:
            run_compare(paths[0])
        else:
            run_batch(paths, args.manual, args.show)
    except NotImplementedError as e:
        print(f"\n아직 구현하지 않은 단계가 있습니다 → {e}")
    except KeyboardInterrupt:
        print("\n중단했습니다.")


if __name__ == "__main__":
    main()
