"""Step 5 — 역매핑 + 양선형 보간으로 원근 변환.  설명: GUIDE.md §5"""
from __future__ import annotations

import numpy as np


def warp_perspective(img: np.ndarray, H: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """cv2.warpPerspective(img, H, size) 를 numpy 로 직접 구현한다 (INTER_LINEAR, 바깥은 0).

    img:  uint8, (h, w) 또는 (h, w, c)
    H:    원본 → 출력 으로 보내는 3×3 행렬
    size: 출력 크기 (width, height)  ← OpenCV 관례대로 가로가 먼저!
    돌려주는 값: img 와 같은 dtype·채널 수, shape (height, width[, c])

    방법 (역매핑):
      1) 출력의 모든 픽셀 (u, v) 좌표 격자를 만든다
      2) H 의 역행렬로 원본 좌표 (x, y) 를 구한다 (w 로 나누는 것 잊지 말기)
      3) (x, y) 주변 네 픽셀을 양선형 보간한다. 원본 바깥의 이웃은 0 으로 본다
    for 문 없이 numpy 배열 연산으로. (먼저 for 문 버전을 짜 보는 것도 좋다)
    """
    raise NotImplementedError("Step 5: warp_perspective 를 구현하세요 (GUIDE.md §5)")
