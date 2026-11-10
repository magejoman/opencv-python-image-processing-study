"""{{TITLE}}

실행 (어느 폴더에서 실행해도 된다):
    python main.py                      # config.yaml 의 input.folder 이미지 전부 처리 → results/
    python main.py --input 사진.jpg      # 특정 파일 또는 폴더만
    python main.py --tune               # 첫 이미지로 트랙바 튜닝 (s 저장, ESC 종료)
    python main.py --show               # 이미지마다 중간 결과 창으로 보기 (아무 키나 → 다음)

지금 들어 있는 pipeline 은 '그레이 → 블러 → Canny' 예시다. 프로젝트에 맞게 바꿔 쓴다.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from cvkit import Param, Project, Stages, Table, Timer, check_image, imread, list_images, tune

proj = Project(__file__)
cfg = proj.config


def pipeline(img: np.ndarray, *, blur_ksize: int, canny_low: int, canny_high: int):
    """이미지 한 장을 처리한다.

    돌려주는 값: (Stages, 지표 dict)
      - Stages: 단계별 중간 결과 → 모자이크로 저장되어 어디서 망가졌는지 바로 보인다
      - 지표:   결과표(summary.csv)의 한 줄이 된다
    """
    check_image(img, "img", dtype=np.uint8, channels=3)
    st = Stages()
    st.add("원본", img)
    gray = st.add("그레이", cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    blur = st.add(f"블러 k={blur_ksize}", cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0))
    edges = st.add(f"Canny {canny_low}/{canny_high}", cv2.Canny(blur, canny_low, canny_high))
    return st, {"edge_ratio": float((edges > 0).mean())}


def collect_inputs(arg: str | None) -> list[Path]:
    if arg is None:
        return proj.images(cfg.input.folder)
    p = Path(arg)
    return list_images(p) if p.is_dir() else [p]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", help="이미지 파일 또는 폴더 (생략하면 config 의 input.folder)")
    ap.add_argument("--tune", action="store_true", help="첫 이미지로 트랙바 튜닝")
    ap.add_argument("--show", action="store_true", help="이미지마다 중간 결과를 창으로 보기")
    args = ap.parse_args()

    paths = collect_inputs(args.input)
    if not paths:
        print(f"처리할 이미지가 없습니다. {proj.path(cfg.input.folder)} 에 사진을 넣거나 --input 을 주세요.")
        return

    if args.tune:
        img = imread(paths[0], max_side=cfg.input.max_side)
        tune(img, lambda im, **p: pipeline(im, **p)[0], Param.from_config(cfg.params, cfg.tune),
             fixed={k: v for k, v in cfg.params.items() if k not in cfg.tune},
             save_path=proj.result_path("tuned_params.yaml"))
        print("마음에 드는 값을 config.yaml 의 params 에 옮겨 적으세요.")
        return

    table = Table()
    for path in paths:
        img = imread(path, max_side=cfg.input.max_side)
        with Timer(verbose=False) as t:
            stages, metrics = pipeline(img, **cfg.params)
        if cfg.output.save_stages:
            stages.save(proj.result_path("stages", f"{path.stem}.jpg"))
        if args.show and stages.show(path.name) == 27:      # ESC 면 창 보기 중단
            args.show = False
        table.add(file=path.name, ms=t.ms, **metrics)

    print(table)
    table.save_csv(proj.result_path("summary.csv"))
    table.save_markdown(proj.result_path("summary.md"))
    print(f"\n{len(table)}장 처리 → {proj.results}")


if __name__ == "__main__":
    main()
