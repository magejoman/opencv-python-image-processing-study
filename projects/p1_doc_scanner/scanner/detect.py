"""Step 2 — 사진에서 종이(볼록 사각형)를 찾는다.  설명: GUIDE.md §2"""
from __future__ import annotations

import cv2
import numpy as np

from cvkit import Stages


def find_document_quad(img: np.ndarray, *, blur_ksize: int = 5, canny_low: int = 50, canny_high: int = 150,
                       morph_ksize: int = 5, approx_eps: float = 0.02, min_area_ratio: float = 0.1,
                       stages: Stages | None = None) -> np.ndarray | None:
    """img (uint8 BGR) 에서 종이의 네 꼭짓점을 찾는다.

    돌려주는 값: shape (4, 2) float32 배열 [[x, y], ...] (순서는 아무래도 됨, Step 3 에서 정렬)
                 못 찾으면 None
    파라미터:
        blur_ksize       GaussianBlur 커널 크기 (홀수)
        canny_low/high   Canny 히스테리시스 임계값
        morph_ksize      끊어진 엣지를 잇는 닫힘(close) 연산 커널 크기
        approx_eps       approxPolyDP 허용 오차 = approx_eps × 윤곽선 둘레
        min_area_ratio   사각형 넓이가 이미지 넓이의 이 비율보다 작으면 종이로 보지 않는다
        stages           None 이 아니면 중간 결과를 stages.add(...) 로 기록한다 (디버깅용)

    순서: 그레이 → 블러 → Canny → 닫힘 → 외곽 윤곽선 → 넓이 큰 순으로
          다각형 근사 → '꼭짓점 4개 + 볼록 + 충분히 큼' 인 첫 번째를 돌려준다
    """
    raise NotImplementedError("Step 2: find_document_quad 를 구현하세요 (GUIDE.md §2)")
