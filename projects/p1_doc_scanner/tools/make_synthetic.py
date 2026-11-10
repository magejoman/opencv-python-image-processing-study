"""(제공) 정답이 있는 합성 문서 사진 만들기.

종이 이미지를 '알고 있는' 호모그래피로 배경 위에 붙이므로 네 꼭짓점의 정답 좌표를 정확히 안다.
→ 사진을 찍기 전에도 개발을 시작할 수 있고, 꼭짓점 오차(px)로 정량 평가할 수 있다.

    python p1_doc_scanner/tools/make_synthetic.py            # 20장 → data/synthetic/
    python p1_doc_scanner/tools/make_synthetic.py --n 50 --seed 1

난이도: 앞쪽 60% 는 보통, 뒤쪽 40% 는 어려움. 어려움에는 현실에서 흔한 문제를 1~2개 섞는다:
    low_contrast  밝은 책상 위의 흰 종이 (경계가 흐림)
    shadow        종이 경계를 가로지르는 선명한 그림자
    occluder      펜·손가락이 종이 테두리를 가림
    clutter       폰·포스트잇이 종이에 맞닿아 있음 (윤곽선이 합쳐짐)
각 이미지의 조건은 meta.json 에 남아서 main.py 결과표에 함께 찍힌다 (실패 원인 분석용).
"""
import argparse
import json
import string
from pathlib import Path

import cv2
import numpy as np

from cvkit import imwrite

PROJECT = Path(__file__).resolve().parents[1]
PAPER_W, PAPER_H = 600, 848                      # A4 비율 (1 : √2)


def make_paper(rng) -> np.ndarray:
    paper = np.full((PAPER_H, PAPER_W, 3), rng.integers(232, 250), np.uint8)
    ink = (40, 40, 40)
    cv2.rectangle(paper, (50, 50), (PAPER_W - 50, 110), (70, 70, 70), -1)           # 제목 띠
    cv2.putText(paper, "REPORT " + str(rng.integers(100, 999)), (70, 95), cv2.FONT_HERSHEY_DUPLEX, 1.2,
                (240, 240, 240), 2, cv2.LINE_AA)
    y = 160
    while y < PAPER_H - 80:
        if rng.random() < 0.12:                                                     # 가끔 표
            rows, h = rng.integers(3, 6), 26
            for r in range(rows + 1):
                cv2.line(paper, (60, y + r * h), (PAPER_W - 60, y + r * h), ink, 1)
            for x in np.linspace(60, PAPER_W - 60, 4).astype(int):
                cv2.line(paper, (int(x), y), (int(x), y + rows * h), ink, 1)
            y += rows * h + 30
            continue
        x = 60
        while True:                                                                 # 한 줄의 단어들
            word = "".join(rng.choice(list(string.ascii_lowercase), rng.integers(2, 9)))
            (tw, _), _ = cv2.getTextSize(word, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            if x + tw > PAPER_W - 60:
                break
            cv2.putText(paper, word, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, ink, 1, cv2.LINE_AA)
            x += tw + 10
        y += 28
    return paper


def make_background(rng, h, w, kind) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if kind == "wood":
        grain = np.sin(xx / rng.uniform(6, 14) + 3 * np.sin(yy / rng.uniform(40, 90)))
        base = np.stack([60 + 20 * grain, 90 + 25 * grain, 130 + 30 * grain], axis=2)
    elif kind == "dark_desk":
        base = np.full((h, w, 3), rng.integers(30, 70), np.float32)
    elif kind == "fabric":
        check = ((xx // 24 + yy // 24) % 2)[..., None]
        base = np.where(check > 0, np.array([120, 60, 50], np.float32), np.array([90, 40, 35], np.float32))
    elif kind == "light_table":                                                     # 어려움: 종이와 대비가 낮다
        base = np.full((h, w, 3), rng.integers(200, 222), np.float32)
    else:
        raise ValueError(kind)
    return base + rng.normal(0, 6, (h, w, 3)).astype(np.float32)


def random_quad(rng, w, h, max_angle, max_jitter) -> np.ndarray:
    """종이가 놓일 사각형 [좌상, 우상, 우하, 좌하]. 화면 밖으로 나가면 다시 뽑는다."""
    while True:
        ph = rng.uniform(0.55, 0.85) * h
        pw = ph * PAPER_W / PAPER_H
        rect = np.array([[-pw / 2, -ph / 2], [pw / 2, -ph / 2], [pw / 2, ph / 2], [-pw / 2, ph / 2]])
        a = np.deg2rad(rng.uniform(-max_angle, max_angle))
        R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        center = np.array([w / 2, h / 2]) + rng.uniform(-0.1, 0.1, 2) * [w, h]
        quad = rect @ R.T + center + rng.uniform(-max_jitter, max_jitter, (4, 2)) * ph   # 원근 느낌
        if quad.min() > 15 and quad[:, 0].max() < w - 15 and quad[:, 1].max() < h - 15:
            return quad.astype(np.float32), float(np.rad2deg(a))


def add_clutter(rng, img, quad):
    """종이 한 모서리 옆에 맞닿은 물건(폰 또는 포스트잇). 종이보다 먼저 그려서 종이 아래에 깔린다."""
    corner = quad[rng.integers(4)]
    outward = corner - quad.mean(axis=0)
    outward /= np.linalg.norm(outward)
    size = rng.uniform(140, 220)
    center = corner + outward * size * 0.35
    color = (35, 35, 40) if rng.random() < 0.5 else (90, 220, 245)                # 검은 폰 / 노란 포스트잇
    box = cv2.boxPoints(((float(center[0]), float(center[1])), (size, size * rng.uniform(0.6, 1.8)),
                         float(rng.uniform(0, 90))))
    cv2.fillPoly(img, [np.round(box).astype(np.int32)], color, cv2.LINE_AA)


def add_occluder(rng, img, quad):
    """종이 테두리 하나를 가로지르는 펜(가는 막대) 또는 손가락(굵은 살색 막대). 종이 위에 그린다."""
    i = rng.integers(4)
    a, b = quad[i], quad[(i + 1) % 4]
    on_edge = a + (b - a) * rng.uniform(0.25, 0.75)
    inward = quad.mean(axis=0) - on_edge
    inward /= np.linalg.norm(inward)
    tilt = np.deg2rad(rng.uniform(-35, 35))
    d = np.array([[np.cos(tilt), -np.sin(tilt)], [np.sin(tilt), np.cos(tilt)]]) @ inward
    p1, p2 = on_edge - d * rng.uniform(80, 160), on_edge + d * rng.uniform(40, 120)
    if rng.random() < 0.5:
        color, thick = (120, 60, 20), int(rng.integers(10, 16))                     # 펜
    else:
        color, thick = (120, 150, 200), int(rng.integers(34, 50))                   # 손가락
    cv2.line(img, tuple(np.round(p1).astype(int)), tuple(np.round(p2).astype(int)), color, thick, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(PROJECT / "data" / "synthetic"))
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    out = Path(args.out)
    gt, meta = {}, {}
    for i in range(args.n):
        hard = i >= round(args.n * 0.6)
        h, w = (1280, 960) if rng.random() < 0.5 else (960, 1280)
        issues = list(rng.choice(["low_contrast", "shadow", "occluder", "clutter"],
                                 size=rng.integers(1, 3), replace=False)) if hard else []
        bg_kind = "light_table" if "low_contrast" in issues else str(rng.choice(["wood", "dark_desk", "fabric"]))
        quad, angle = random_quad(rng, w, h, max_angle=30 if hard else 15, max_jitter=0.06 if hard else 0.03)

        background = make_background(rng, h, w, bg_kind)
        if "clutter" in issues:
            add_clutter(rng, background, quad)
        paper = make_paper(rng)
        src = np.array([[0, 0], [PAPER_W - 1, 0], [PAPER_W - 1, PAPER_H - 1], [0, PAPER_H - 1]], np.float32)
        H = cv2.getPerspectiveTransform(src, quad)
        warped = cv2.warpPerspective(paper, H, (w, h)).astype(np.float32)
        mask = cv2.warpPerspective(np.ones((PAPER_H, PAPER_W), np.float32), H, (w, h))[..., None]
        img = background * (1 - mask) + warped * mask
        if "occluder" in issues:
            add_occluder(rng, img, quad)

        # 조명: 한쪽이 어두운 그라디언트 + 그림자 (경계가 꽤 선명한 띠)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        direction = rng.uniform(0, 2 * np.pi)
        ramp = (np.cos(direction) * xx / w + np.sin(direction) * yy / h)
        img *= (0.85 + 0.25 * (ramp - ramp.min()) / (np.ptp(ramp) + 1e-6))[..., None]
        if "shadow" in issues:
            c = quad.mean(axis=0) + rng.uniform(-0.25, 0.25, 2) * [w, h]           # 종이를 가로지르게
            t = rng.uniform(0, np.pi)
            side = ((xx - c[0]) * np.cos(t) + (yy - c[1]) * np.sin(t)) > 0
            soft = cv2.GaussianBlur(side.astype(np.float32), (0, 0), rng.uniform(3, 10))
            img *= (1 - rng.uniform(0.4, 0.6) * soft)[..., None]

        img = cv2.GaussianBlur(img, (0, 0), rng.uniform(0.6, 1.4)) + rng.normal(0, 3, img.shape)
        img = np.clip(img, 0, 255).astype(np.uint8)

        name = f"syn_{i:03d}.jpg"
        imwrite(out / name, img, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(75, 95))])
        gt[name] = quad.round(2).tolist()
        meta[name] = {"level": "hard" if hard else "normal", "background": bg_kind,
                      "angle_deg": round(angle, 1), "issues": "+".join(issues)}

    (out / "gt.json").write_text(json.dumps(gt, indent=1), encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{args.n}장 생성 → {out}  (정답: gt.json, 조건: meta.json)")


if __name__ == "__main__":
    main()
