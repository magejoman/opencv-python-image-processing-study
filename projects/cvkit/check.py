"""이미지 배열 검사.

현업 CV 버그 1~3위는 dtype(uint8 overflow), 채널(BGR/RGB/그레이), 좌표 순서((x,y) vs (row,col)) 다.
함수 입구에서 check_image 로 걸러 두면 엉뚱한 곳에서 터지는 대신 바로 원인이 보인다.
"""
from __future__ import annotations

import numpy as np


def _channels(img: np.ndarray) -> int:
    return 1 if img.ndim == 2 else img.shape[2]


def check_image(img, name: str = "image", *, dtype=None, channels: int | None = None) -> np.ndarray:
    """img 가 정상적인 이미지 배열인지 검사하고 그대로 돌려준다.

    dtype:    기대하는 자료형 (예: np.uint8). None 이면 검사하지 않는다.
    channels: 기대하는 채널 수 (그레이 1, 컬러 3). None 이면 검사하지 않는다.
    """
    if img is None:
        raise TypeError(f"{name}: None 입니다. 이미지 읽기(imread)나 이전 단계가 실패했을 수 있습니다.")
    if not isinstance(img, np.ndarray):
        raise TypeError(f"{name}: numpy 배열이 아닙니다 (type={type(img).__name__}).")
    if img.size == 0:
        raise ValueError(f"{name}: 빈 배열입니다 (shape={img.shape}). 슬라이싱 범위를 확인하세요.")
    if img.ndim not in (2, 3) or (img.ndim == 3 and img.shape[2] not in (1, 3, 4)):
        raise ValueError(f"{name}: 이미지 모양이 아닙니다 (shape={img.shape}). (H, W) 또는 (H, W, C) 여야 합니다.")
    if dtype is not None and img.dtype != np.dtype(dtype):
        raise TypeError(
            f"{name}: dtype 이 {img.dtype} 인데 {np.dtype(dtype)} 이어야 합니다. "
            f"(uint8 끼리 더하면 255 를 넘을 때 값이 0 부터 다시 돌아갑니다. 계산은 float32 로 하세요.)"
        )
    if channels is not None and _channels(img) != channels:
        raise ValueError(f"{name}: 채널 수가 {_channels(img)} 인데 {channels} 이어야 합니다 (shape={img.shape}).")
    return img


def describe(img: np.ndarray, name: str = "image", *, verbose: bool = True) -> str:
    """shape, dtype, 값 범위를 한 줄로 요약한다. 중간값을 눈으로 확인할 때 쓴다."""
    if img.size == 0:
        text = f"{name}: shape={img.shape} dtype={img.dtype} (비어 있음)"
    else:
        h, w = img.shape[:2]
        text = (
            f"{name}: shape={img.shape} (H={h}, W={w}, C={_channels(img) if img.ndim <= 3 else '?'}) "
            f"dtype={img.dtype} min={img.min():.4g} max={img.max():.4g} mean={img.mean():.4g}"
        )
        if img.ndim == 3 and img.shape[2] > 1:
            per_ch = ", ".join(f"{m:.4g}" for m in img.reshape(-1, img.shape[2]).mean(axis=0))
            text += f" (채널별 평균: {per_ch})"
    if verbose:
        print(text)
    return text
