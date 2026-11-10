"""시각화: 어떤 배열이든 화면에 보이게 바꾸고, 중간 결과를 한 장에 모은다.

디버깅의 대부분은 "어느 단계에서 망가졌나" 를 찾는 일이다.
Stages 로 단계마다 결과를 기록해 두고 mosaic 한 장으로 저장하면 그 답이 바로 보인다.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from .io import imwrite

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgun.ttf",                        # Windows: 맑은 고딕
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",         # macOS
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",    # Linux (나눔고딕)
]
_SUPERSAMPLE = 3


def to_display(img, *, normalize: str = "auto") -> np.ndarray:
    """어떤 배열이든 화면 표시용 uint8 BGR 3채널로 바꾼다.

    normalize:
      "auto"   bool → 0/255, uint8 → 그대로,
               그 밖의 dtype 은 값이 [0, 1] 안이면 ×255, [0, 255] 안이면 그대로, 아니면 min-max 정규화
               (Sobel 결과처럼 음수가 있는 값은 min-max 로 펴서 보여준다)
      "minmax" 항상 최솟값→0, 최댓값→255
      "clip"   0~255 밖은 잘라낸다
    """
    a = np.asarray(img)
    if a.dtype == bool:
        a = a.astype(np.uint8) * 255
    elif a.dtype != np.uint8:
        a = np.nan_to_num(a.astype(np.float32))
        lo, hi = float(a.min()), float(a.max())
        mode = normalize
        if mode == "auto":
            if lo >= 0 and hi <= 1:
                a = a * 255
                mode = "clip"
            elif lo >= 0 and hi <= 255:
                mode = "clip"
            else:
                mode = "minmax"
        if mode == "minmax":
            a = (a - lo) * (255.0 / (hi - lo)) if hi > lo else np.zeros_like(a)
        elif mode != "clip":
            raise ValueError(f"normalize 는 auto / minmax / clip 중 하나여야 합니다: {normalize!r}")
        a = np.clip(a + 0.5, 0, 255).astype(np.uint8)

    if a.ndim == 2 or (a.ndim == 3 and a.shape[2] == 1):
        return cv2.cvtColor(a.reshape(a.shape[:2]), cv2.COLOR_GRAY2BGR)
    if a.ndim == 3 and a.shape[2] == 4:
        return cv2.cvtColor(a, cv2.COLOR_BGRA2BGR)
    if a.ndim == 3 and a.shape[2] == 3:
        return a
    raise ValueError(f"표시할 수 없는 모양입니다: shape={a.shape}")


@lru_cache(maxsize=8)
def _font(size: int):
    from PIL import ImageFont
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return None


def put_label(img: np.ndarray, text: str, *, size: int = 18) -> np.ndarray:
    """왼쪽 위에 검은 바탕 흰 글씨 라벨을 붙인 사본을 돌려준다. 한글도 된다.

    cv2.putText 는 한글을 ??? 로 찍기 때문에, 한글이 있으면 Pillow 로 그린다.
    작은 글씨는 폰트 힌팅 때문에 획이 빠져 보이므로(예: '닫'), 3배 크게 그린 뒤 줄여서 붙인다.
    """
    out = to_display(img).copy()
    pad = 4
    font = None if text.isascii() else _font(size * _SUPERSAMPLE)
    if font is None:
        scale = size / 30
        (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        cv2.rectangle(out, (0, 0), (tw + 2 * pad, th + base + 2 * pad), (0, 0, 0), -1)
        cv2.putText(out, text, (pad, pad + th), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
        return out

    from PIL import Image, ImageDraw
    left, top, right, bottom = font.getbbox(text)
    big = Image.new("L", (right - left + 2, bottom - top + 2), 0)
    ImageDraw.Draw(big).text((1 - left, 1 - top), text, font=font, fill=255)
    tw, th = max(1, round(big.width / _SUPERSAMPLE)), max(1, round(big.height / _SUPERSAMPLE))
    alpha = cv2.resize(np.asarray(big), (tw, th), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255

    H, W = out.shape[:2]
    out[:min(H, th + 2 * pad), :min(W, tw + 2 * pad)] = 0                    # 검은 바탕
    h, w = min(th, H - pad), min(tw, W - pad)                                # 이미지 밖으로 나가는 부분은 자른다
    if h > 0 and w > 0:
        region = out[pad:pad + h, pad:pad + w].astype(np.float32)
        out[pad:pad + h, pad:pad + w] = (region * (1 - alpha[:h, :w]) + 255 * alpha[:h, :w]).astype(np.uint8)
    return out


def _fit(img: np.ndarray, max_w: int, max_h: int) -> np.ndarray:
    """비율을 유지하며 (max_w, max_h) 안에 맞춘다.
    줄일 때는 INTER_AREA, 키울 때는 INTER_NEAREST (작은 행렬도 픽셀이 또렷하게 보이도록)."""
    h, w = img.shape[:2]
    scale = min(max_w / w, max_h / h)
    size = (max(1, round(w * scale)), max(1, round(h * scale)))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_NEAREST
    return cv2.resize(img, size, interpolation=interp)


def mosaic(items, *, cols: int | None = None, cell_height: int = 240, gap: int = 4,
           bg: int = 40, label_size: int = 16) -> np.ndarray:
    """여러 이미지를 라벨을 붙여 격자 한 장으로 합친다.

    items: [(라벨, 이미지), ...] 또는 {라벨: 이미지} 또는 Stages
    cols:  열 개수. 생략하면 3장 이하는 한 줄, 그 이상은 정사각형에 가깝게.
    """
    if isinstance(items, Stages):
        items = items.items
    elif isinstance(items, dict):
        items = list(items.items())
    if not items:
        raise ValueError("mosaic 에 넣을 이미지가 없습니다.")

    n = len(items)
    cols = cols or (n if n <= 3 else math.ceil(math.sqrt(n)))
    rows = math.ceil(n / cols)
    max_w = cell_height * 3                       # 파노라마처럼 아주 긴 이미지가 격자를 망치지 않게
    cells = [put_label(_fit(to_display(img), max_w, cell_height), str(label), size=label_size)
             for label, img in items]
    cell_w = max(c.shape[1] for c in cells)

    canvas = np.full((rows * cell_height + (rows + 1) * gap, cols * cell_w + (cols + 1) * gap, 3), bg, np.uint8)
    for i, cell in enumerate(cells):
        r, c = divmod(i, cols)
        y = gap + r * (cell_height + gap)
        x = gap + c * (cell_w + gap)
        canvas[y:y + cell.shape[0], x:x + cell.shape[1]] = cell
    return canvas


def show(img_or_items, title: str = "view", *, wait: bool = True, max_side: int = 1400) -> int:
    """이미지(또는 이미지 목록)를 창에 띄운다. 화면보다 크면 줄여서 보여준다.

    title 은 영문으로 쓴다 (Windows 의 OpenCV 창 제목은 한글이 깨진다).
    돌려주는 값: 눌린 키 코드 (wait=False 면 -1)
    """
    if isinstance(img_or_items, (list, tuple, dict, Stages)):
        img = mosaic(img_or_items)
    else:
        img = to_display(img_or_items)
    if max(img.shape[:2]) > max_side:
        img = _fit(img, max_side, max_side)
    cv2.imshow(title, img)
    if not wait:
        return -1
    key = cv2.waitKey(0)
    cv2.destroyWindow(title)
    return key


class Stages:
    """파이프라인의 중간 결과를 순서대로 기록한다.

        st = Stages()
        gray = st.add("그레이", cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))   # 기록하고 그대로 돌려준다
        edge = st.add("엣지", cv2.Canny(gray, 50, 150))
        st.save("results/stages.jpg")      # 한 장으로 저장
        st.show()                          # 창으로 보기
        st.describe()                      # 단계별 shape/dtype/값 범위 출력
    """

    def __init__(self):
        self.items: list[tuple[str, np.ndarray]] = []

    def add(self, label: str, img: np.ndarray) -> np.ndarray:
        self.items.append((label, img))
        return img

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, label: str) -> np.ndarray:
        for name, img in self.items:
            if name == label:
                return img
        raise KeyError(f"'{label}' 단계가 없습니다. 있는 단계: {[n for n, _ in self.items]}")

    def mosaic(self, **kwargs) -> np.ndarray:
        return mosaic(self.items, **kwargs)

    def save(self, path, **kwargs) -> Path:
        return imwrite(path, self.mosaic(**kwargs))

    def show(self, title: str = "stages", **kwargs) -> int:
        return show(self.mosaic(**kwargs), title)

    def describe(self) -> None:
        from .check import describe
        for label, img in self.items:
            describe(np.asarray(img), label)
