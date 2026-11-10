"""어안 → 톱뷰 모아레 실험

실행 (어느 폴더에서 실행해도 된다):
    python main.py              # 전체 실험 → results/
    python main.py --no-video   # 깜빡임(동영상) 실험을 빼고 빠르게
    python main.py --show       # 결과 그림을 창으로도 보기 (아무 키나 → 다음)
    python main.py --tune       # 균일 블러 σ 와 밉맵 lod_bias 를 트랙바로 움직여 보기

같은 어안 영상, 같은 톱뷰 LUT 에서 '읽는 방법' 만 바꿔 모아레·선명도·깜빡임을 비교한다.
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np
from PIL import Image

from cvkit import Param, Project, Table, Timer, imwrite, mosaic, show, tune
from moire import scene
from moire.camera import FisheyeCamera
from moire.lut import Footprint, TopView, footprint, make_topview
from moire.methods import anisotropic, blur, pyramid_sample, remap_bilinear, sharpen, supersample, trilinear_lod
from moire.metrics import contrast_kept, flat_mask, flicker, moire_rms

proj = Project(__file__)
cfg = proj.config

NEAR_CROP = (-1.0, 2.0, 0.2, 1.4)       # 근거리 확대 영역: 그레이팅 + 미끄럼 방지 홈 (x0, x1, y0, y1) m
FAR_CROP = (-2.0, 2.0, 1.8, 6.2)        # 중·원거리 확대 영역: 10 cm 줄무늬 두 곳
GIF_KEYS = ("bilinear", "trilinear", "aniso")


def u8(img: np.ndarray) -> np.ndarray:
    """[0, 1] float → uint8. cvkit.to_display 의 자동 정규화에 맡기지 않고 모든 방법을 같은 눈금으로 보여준다."""
    return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)


def build_methods(p, tv: TopView, tv_fine: TopView, fp: Footprint):
    """(키, 이름, 함수(어안 영상) → 톱뷰) 목록. 입력과 LUT 는 같고 '읽는 방법' 만 다르다."""
    mx, my = tv.map_x, tv.map_y
    lod = trilinear_lod(fp.rho, p.lod_bias)
    return [
        ("bilinear", "양선형 (지금 방식)", lambda s: remap_bilinear(s, mx, my)),
        ("sharpen", "ISP 샤프닝 + 양선형",
         lambda s: remap_bilinear(sharpen(s, p.sharpen_amount, p.sharpen_sigma), mx, my)),
        ("blur_weak", f"균일 블러 σ={p.blur_weak:g}", lambda s: remap_bilinear(blur(s, p.blur_weak), mx, my)),
        ("blur_strong", f"균일 블러 σ={p.blur_strong:g}", lambda s: remap_bilinear(blur(s, p.blur_strong), mx, my)),
        ("supersample", f"{p.supersample}× 슈퍼샘플링",
         lambda s: supersample(s, tv_fine.map_x, tv_fine.map_y, p.supersample)),
        ("pyr_nearest", "피라미드 최근접 레벨", lambda s: pyramid_sample(s, mx, my, lod, p.levels, blend=False)),
        ("trilinear", "피라미드 trilinear", lambda s: pyramid_sample(s, mx, my, lod, p.levels, blend=True)),
        ("aniso", "비등방 (밉맵 + 긴 축 탭)",
         lambda s: anisotropic(s, mx, my, fp, p.levels, p.max_probes, p.lod_bias)),
    ]


# ------------------------------------------------------------------ 그림

def colorize(values: np.ndarray, lo: float, hi: float, cmap: int, valid: np.ndarray) -> np.ndarray:
    out = cv2.applyColorMap(u8(np.clip((values - lo) / (hi - lo), 0, 1)), cmap)
    out[~valid] = 0
    return out


def _text(img, text, org, scale=0.5):
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3, cv2.LINE_AA)      # 테두리
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)


def annotate(img: np.ndarray, tv: TopView, values: np.ndarray, fmt: str) -> np.ndarray:
    """X = 0 열의 몇 지점에 값을 적고, 근/중/원 경계선을 긋는다."""
    out = img.copy()
    c = round((0 - tv.x0) / tv.gsd)
    for r_m in cfg.topview.near_far_m:
        r = tv.row_of(r_m)
        cv2.line(out, (0, r), (out.shape[1] - 1, r), (255, 255, 255), 1)
    for y in (0.4, 1.0, 2.0, 3.0, 5.0):
        r = tv.row_of(y)
        cv2.circle(out, (c, r), 3, (255, 255, 255), -1)
        _text(out, f"{fmt.format(values[r, c])} @{y:g}m", (c + 7, r + 5))
    return out


def fisheye_overlay(src: np.ndarray, cam: FisheyeCamera) -> np.ndarray:
    """어안 영상 위에 톱뷰 영역(초록)과 근/중/원 경계(노랑)를 그린다."""
    img = cv2.cvtColor(u8(src), cv2.COLOR_GRAY2BGR)
    (x0, x1), (y0, y1) = cfg.topview.x_range_m, cfg.topview.y_range_m
    t = np.linspace(0, 1, 300)

    def poly(X, Y, color, closed):
        u, v, _ = cam.ground_to_image(X, Y)
        cv2.polylines(img, [np.round(np.stack([u, v], -1)).astype(np.int32)], closed, color, 2, cv2.LINE_AA)

    one = np.ones_like(t)
    border_X = np.concatenate([x0 + (x1 - x0) * t, x1 * one, x1 - (x1 - x0) * t, x0 * one])
    border_Y = np.concatenate([y0 * one, y0 + (y1 - y0) * t, y1 * one, y1 - (y1 - y0) * t])
    poly(border_X, border_Y, (0, 255, 0), True)
    for y in cfg.topview.near_far_m:
        poly(x0 + (x1 - x0) * t, y * one, (0, 255, 255), False)
    return img


def save_gif(path, frames_bgr: list[np.ndarray], ms: int = 120):
    imgs = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames_bgr]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=ms, loop=0)


# ------------------------------------------------------------------ 튜너

def run_tuner(src, tv: TopView, fp: Footprint, truth):
    """근거리(모아레)와 원거리(선명도)를 나란히 보며 '하나의 블러 σ' 와 '위치마다 다른 밉맵 레벨' 을 비교한다."""
    p = cfg.params
    near = tv.rows_cols(NEAR_CROP)
    x0, x1, y0, y1 = scene.FAR_BARS_BOX
    far = tv.rows_cols((x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1))

    def process(img, *, blur_strong, lod_bias, levels, **_):
        b = remap_bilinear(blur(img, blur_strong), tv.map_x, tv.map_y)
        t = pyramid_sample(img, tv.map_x, tv.map_y, trilinear_lod(fp.rho, lod_bias), levels)
        return [(f"균일 블러 σ={blur_strong:g} · 근거리", u8(b[near])),
                (f"trilinear bias={lod_bias:+g} · 근거리", u8(t[near])),
                ("정답 · 근거리", u8(truth[near])),
                (f"균일 블러 σ={blur_strong:g} · 원거리", u8(b[far])),
                (f"trilinear bias={lod_bias:+g} · 원거리", u8(t[far])),
                ("정답 · 원거리", u8(truth[far]))]

    tune(src, process, Param.from_config(p, cfg.tune),
         fixed={k: v for k, v in p.items() if k not in cfg.tune},
         save_path=proj.result_path("tuned_params.yaml"))
    print("마음에 드는 값을 config.yaml 의 params 에 옮겨 적으세요.")


# ------------------------------------------------------------------ 실행

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-video", action="store_true", help="깜빡임(동영상) 실험 생략")
    ap.add_argument("--show", action="store_true", help="결과 그림을 창으로도 보기")
    ap.add_argument("--tune", action="store_true", help="트랙바 튜너")
    args = ap.parse_args()

    c, p, tvc = cfg.camera, cfg.params, cfg.topview
    cam = FisheyeCamera(c.width, c.height, c.hfov_deg, c.height_m, c.pitch_deg)
    gsd = tvc.gsd_m
    tv = make_topview(cam, gsd, tvc.x_range_m, tvc.y_range_m)
    tv_fine = make_topview(cam, gsd / p.supersample, tvc.x_range_m, tvc.y_range_m)
    fp = footprint(tv.map_x, tv.map_y)

    n_frames = 1 if (args.no_video or args.tune) else cfg.video.frames
    shift_px = round(cfg.video.step_m / gsd)
    if n_frames > 1 and (shift_px < 1 or abs(cfg.video.step_m / gsd - shift_px) > 1e-6):
        raise SystemExit("video.step_m 은 topview.gsd_m 의 정수배여야 합니다 (움직임 보정을 정확히 하려고).")
    shifts = [k * shift_px * gsd for k in range(n_frames)]

    # 마지막 한 장은 미세 무늬를 뺀 '깨끗한' 바닥 (모아레 지표용)
    with Timer(f"어안 렌더링 {n_frames}+1장"):
        *frames, src_clean = scene.render_fisheye(cam, [(s, 1.0) for s in shifts] + [(0.0, 0.0)],
                                                  ss=cfg.render.ss, lens_sigma=cfg.render.lens_sigma)
    with Timer("정답 톱뷰"):
        truths = [scene.render_truth(tv.X, tv.Y, gsd, shift=s) for s in shifts]
        truth_clean = scene.render_truth(tv.X, tv.Y, gsd, fine=0.0)
    src, truth = frames[0], truths[0]

    if args.tune:
        run_tuner(src, tv, fp, truth)
        return

    r_near, r_far = tvc.near_far_m
    near = tv.valid & (tv.Y < r_near)
    mid = tv.valid & (tv.Y >= r_near) & (tv.Y < r_far)
    near_flat = near & flat_mask(truth, cfg.metrics.flat_margin_px)
    mid_bars = tv.box_mask(scene.MID_BARS_BOX, inset=0.05)
    far_bars = tv.box_mask(scene.FAR_BARS_BOX, inset=0.05)

    table, outputs, videos = Table(), {}, {}
    for key, label, fn in build_methods(p, tv, tv_fine, fp):
        with Timer(verbose=False) as t:
            out = fn(src)
        out_clean = fn(src_clean)
        outputs[key] = (label, out)
        row = {"방법": label,
               "근거리 모아레↓": moire_rms(out, out_clean, near),
               "중거리 모아레↓": moire_rms(out, out_clean, mid),
               "중거리 줄무늬 대비%↑": contrast_kept(out, truth, mid_bars),
               "원거리 줄무늬 대비%↑": contrast_kept(out, truth, far_bars)}
        if n_frames > 1:
            videos[key] = [out] + [fn(f) for f in frames[1:]]
            row["깜빡임↓"] = flicker(videos[key], shift_px, near_flat)
        row["ms (CPU)"] = t.ms
        table.add(**row)
        print(f"  {label:<24} 근거리 모아레 {row['근거리 모아레↓']:5.1f}")
    truth_row = {"방법": "정답 (바닥에서 직접 계산)",
                 "근거리 모아레↓": moire_rms(truth, truth_clean, near),
                 "중거리 모아레↓": moire_rms(truth, truth_clean, mid),
                 "중거리 줄무늬 대비%↑": 100.0, "원거리 줄무늬 대비%↑": 100.0}
    if n_frames > 1:
        truth_row["깜빡임↓"] = flicker(truths, shift_px, near_flat)
    table.add(**truth_row)

    # ---- 결과표
    v = tv.valid
    stats = (f"축소율 ρ: 톱뷰 면적의 {np.mean(fp.rho[v] > 1) * 100:.0f}% 가 축소 구간 (ρ>1), "
             f"{np.mean(fp.rho[v] > 2) * 100:.0f}% 가 2배 이상, 최대 {fp.rho[v].max():.1f}배 · "
             f"이방성 최대 {fp.aniso[v].max():.1f}")
    print("\n" + table.to_markdown(".1f") + "\n\n" + stats)
    table.save_csv(proj.result_path("summary.csv"))
    proj.result_path("summary.md").write_text(table.to_markdown(".1f") + "\n\n" + stats + "\n", encoding="utf-8")

    # ---- 그림
    near_rc, far_rc = tv.rows_cols(NEAR_CROP), tv.rows_cols(FAR_CROP)
    rows = {r["방법"]: r for r in table.rows}
    figs = {
        "01_scene.jpg": mosaic([
            ("어안 입력 (초록: 톱뷰 영역, 노랑: 1.5 m · 3.5 m)", fisheye_overlay(src, cam)),
            ("정답 톱뷰 (위 = 차에서 먼 쪽)", u8(truth)),
            ("축소율 ρ (파랑 = 확대, 빨강 = 8배 축소)",
             annotate(colorize(np.log2(fp.rho), -2, 3, cv2.COLORMAP_TURBO, v), tv, fp.rho, "x{:.1f}")),
            ("이방성 s_max/s_min (1 ~ 8)",
             annotate(colorize(fp.aniso, 1, 8, cv2.COLORMAP_VIRIDIS, v), tv, fp.aniso, "{:.1f}")),
        ], cols=2, cell_height=420),
        "02_topviews.jpg": mosaic([(lb, u8(o)) for lb, o in outputs.values()] + [("정답", u8(truth))],
                                  cols=3, cell_height=360),
        "03_near.jpg": mosaic([(f"{lb} · 모아레 {rows[lb]['근거리 모아레↓']:.1f}", u8(o[near_rc]))
                               for lb, o in outputs.values()] + [("정답", u8(truth[near_rc]))],
                              cols=3, cell_height=240),
        "04_mid_far.jpg": mosaic([(f"{lb} · 중 {rows[lb]['중거리 줄무늬 대비%↑']:.0f}% · "
                                   f"원 {rows[lb]['원거리 줄무늬 대비%↑']:.0f}%", u8(o[far_rc]))
                                  for lb, o in outputs.values()] + [("정답", u8(truth[far_rc]))],
                                 cols=3, cell_height=440),
    }
    for name, img in figs.items():
        imwrite(proj.result_path(name), img)

    if n_frames > 1:
        gif = [mosaic([(outputs[k][0], u8(videos[k][i][near_rc])) for k in GIF_KEYS]
                      + [("정답", u8(truths[i][near_rc]))], cols=2, cell_height=240)
               for i in range(n_frames)]
        save_gif(proj.result_path("05_flicker.gif"), gif)

    print(f"\n결과 → {proj.results}")
    if args.show:
        for name, img in figs.items():
            if show(img, name.split(".")[0]) == 27:
                break


if __name__ == "__main__":
    main()
