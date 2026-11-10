"""Step 3 — 꼭짓점 정렬과 출력 크기.  설명: GUIDE.md §3"""
from __future__ import annotations

import numpy as np


def order_corners(pts) -> np.ndarray:
    """아무 순서로 들어온 네 점을 [좌상, 우상, 우하, 좌하] 순서로 정렬한다.

    pts:  (4, 2) 배열 (또는 approxPolyDP 결과 같은 (4, 1, 2)) — 각 행이 (x, y)
    돌려주는 값: (4, 2) float32
    좌표계: 이미지 좌표 (x 는 오른쪽으로, y 는 아래로 증가)
    조건: 종이가 ±40° 까지 기울어져 있어도 맞게 정렬해야 한다.
    """
    raise NotImplementedError("Step 3: order_corners 를 구현하세요 (GUIDE.md §3)")


def quad_size(quad: np.ndarray) -> tuple[int, int]:
    """정렬된 사각형 [좌상, 우상, 우하, 좌하] 을 펼쳤을 때의 출력 크기 (width, height).

    width  = 위쪽 변 길이와 아래쪽 변 길이 중 큰 값 (반올림한 정수)
    height = 왼쪽 변 길이와 오른쪽 변 길이 중 큰 값 (반올림한 정수)
    """
    raise NotImplementedError("Step 3: quad_size 를 구현하세요 (GUIDE.md §3)")
