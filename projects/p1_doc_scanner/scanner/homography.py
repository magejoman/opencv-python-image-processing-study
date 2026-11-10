"""Step 4 — 대응점으로 호모그래피 행렬 풀기 (DLT).  설명: GUIDE.md §4"""
from __future__ import annotations

import numpy as np


def homography_dlt(src, dst) -> np.ndarray:
    """src[i] 를 dst[i] 로 보내는 3×3 호모그래피 H 를 구한다 (H[2, 2] = 1 로 고정).

    src, dst: (N, 2) 배열, N ≥ 4. 각 행이 (x, y)
              N == 4 이면 8×8 연립방정식을 정확히 풀고 (np.linalg.solve 또는 cv2.solve)
              N > 4 이면 2N×8 방정식을 최소제곱으로 푼다 (np.linalg.lstsq)
    돌려주는 값: (3, 3) float64

    확인: cv2.getPerspectiveTransform(src, dst) (N=4), cv2.findHomography(src, dst, 0) (N>4) 와 같아야 한다.
    """
    raise NotImplementedError("Step 4: homography_dlt 를 구현하세요 (GUIDE.md §4)")


def apply_homography(H: np.ndarray, pts) -> np.ndarray:
    """(제공) 점들에 H 를 적용한다. pts: (N, 2) → (N, 2). 검산용."""
    pts = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
    homog = np.hstack([pts, np.ones((len(pts), 1))]) @ H.T      # (N, 3): 각 행 = H @ [x, y, 1]
    return homog[:, :2] / homog[:, 2:3]                            # w 로 나눠 다시 2D 로
