"""Step 6 — 스캔한 느낌 내기 (적응형 이진화).  설명: GUIDE.md §6"""
from __future__ import annotations

import numpy as np


def adaptive_threshold(gray: np.ndarray, block_size: int = 31, C: float = 10) -> np.ndarray:
    """cv2.adaptiveThreshold(gray, 255, ADAPTIVE_THRESH_MEAN_C, THRESH_BINARY, block_size, C) 직접 구현.

    gray:       uint8 그레이 이미지
    block_size: 주변 평균을 구할 정사각형 한 변 (홀수)
    C:          평균에서 빼는 값. 클수록 흰색이 늘어난다
    규칙: 픽셀 > (주변 block_size×block_size 평균 − C) 이면 255, 아니면 0
    가장자리: 이미지 바깥은 가장자리 픽셀을 복제한 것으로 본다 (BORDER_REPLICATE)
    돌려주는 값: uint8 (0 또는 255)
    """
    raise NotImplementedError("Step 6: adaptive_threshold 를 구현하세요 (GUIDE.md §6)")
