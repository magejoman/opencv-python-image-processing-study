"""지표. 전부 회색조 0~255 단위로 돌려준다 (dB 보다 감이 오도록).

모아레   미세 무늬가 있는 영상과 없는 영상을 '같은 방법'으로 톱뷰로 보내고, 두 결과의 차이를 잰다 (RMS).
         홈(8 mm)·그레이팅(12 mm)은 톱뷰 1 cm/px 의 나이퀴스트(주기 2 cm)보다 촘촘해서 톱뷰로 표현할 수 없다.
         그러니 이상적인 결과는 '흔적 없음(0)'. 남은 것은 접혀 들어온 가짜 무늬이거나 걸러지지 않은 잔무늬다.
         두 영상은 타일 경계·줄눈이 똑같으므로, 방법이 경계를 얼마나 흐리든 그 영향은 차이에서 상쇄된다.
대비 유지 10 cm 줄무늬(톱뷰로 표현 가능한 무늬)의 표준편차 비율 (결과 / 정답 × 100 %). 흐리게 만든 방법은 여기서 손해.
깜빡임   차가 움직일 때, 움직임을 보정한 프레임들이 화소마다 얼마나 흔들리는가 (시간 방향 표준편차).
         정답이 평평한 곳(타일 안쪽, 그레이팅 안쪽)만 잰다. 경계는 프레임마다 화소 위상이 달라 조금씩 흔들리기 때문.
"""
from __future__ import annotations

import cv2
import numpy as np


def moire_rms(out: np.ndarray, out_clean: np.ndarray, mask: np.ndarray) -> float:
    return float(np.sqrt(np.mean((out - out_clean)[mask] ** 2)) * 255)


def contrast_kept(out: np.ndarray, truth: np.ndarray, mask: np.ndarray) -> float:
    return float(out[mask].std() / truth[mask].std() * 100)


def flat_mask(truth: np.ndarray, margin_px: int = 3, tol: float = 0.01) -> np.ndarray:
    """정답이 평평한 곳: 밝기가 변하는 경계에서 margin_px 이상 떨어진 화소."""
    grad = cv2.morphologyEx(truth, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))     # 3×3 안의 최대 − 최소
    edge = cv2.dilate((grad > tol).astype(np.uint8), np.ones((2 * margin_px + 1,) * 2, np.uint8))
    return edge == 0


def align_frames(frames: list[np.ndarray], shift_px: int) -> tuple[list[np.ndarray], slice]:
    """프레임 k 는 바닥이 k·shift_px 화소 옮겨진 장면이다. 같은 바닥 지점끼리 맞도록 잘라 낸다.

    프레임 k 의 열 c 에는 '기준 프레임의 열 c + k·shift_px' 에 있던 바닥이 보인다.
    → 바닥 열 w 는 프레임 k 의 열 w − k·shift_px.  모든 프레임에 공통인 w 범위만 남긴다.
    돌려주는 값: 맞춘 프레임들, 그 프레임들이 기준 격자에서 차지하는 열 범위
    """
    n, W = len(frames), frames[0].shape[1]
    lo, hi = (n - 1) * shift_px, W
    aligned = [f[:, lo - k * shift_px: hi - k * shift_px] for k, f in enumerate(frames)]
    return aligned, slice(lo, hi)


def flicker(frames: list[np.ndarray], shift_px: int, mask: np.ndarray) -> float:
    aligned, cols = align_frames(frames, shift_px)
    std = np.stack(aligned).std(axis=0)
    return float(std[mask[:, cols]].mean() * 255)
