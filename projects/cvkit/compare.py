"""직접 구현한 결과와 기준(OpenCV) 결과를 비교한다.

"비슷해 보인다" 대신 최대 오차, 평균 오차, PSNR, 다른 픽셀 수로 말한다.
차이가 '어디에' 몰려 있는지는 diff_heatmap 으로 본다 (예: 가장자리만 다르면 경계 처리 차이).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class CompareResult:
    name: str
    shape: tuple
    max_abs: float          # 가장 많이 다른 픽셀의 차이
    mean_abs: float         # 평균 차이
    psnr: float             # 클수록 비슷함 (같으면 inf, 40dB 이상이면 눈으로 구별하기 어려움)
    n_diff: int             # 차이가 tol 을 넘는 원소 수
    total: int
    tol: float
    diff: np.ndarray = field(repr=False)

    @property
    def ok(self) -> bool:
        """모든 원소의 차이가 tol 이하인가."""
        return self.max_abs <= self.tol

    def __str__(self) -> str:
        verdict = "OK" if self.ok else "다름"
        psnr = "inf (완전히 같음)" if np.isinf(self.psnr) else f"{self.psnr:.2f} dB"
        return (
            f"[비교] {self.name}  shape={self.shape}  → {verdict} (허용 오차 {self.tol})\n"
            f"       최대 차이 {self.max_abs:.4g}, 평균 차이 {self.mean_abs:.4g}, PSNR {psnr}\n"
            f"       허용 오차를 넘는 원소 {self.n_diff:,} / {self.total:,} ({100 * self.n_diff / self.total:.3f}%)"
        )

    def heatmap(self, **kwargs) -> np.ndarray:
        return _heatmap_from_diff(self.diff, **kwargs)


def compare(mine, ref, *, tol: float = 1.0, peak: float = 255.0, name: str = "mine vs ref",
            verbose: bool = True) -> CompareResult:
    """mine 과 ref 의 원소별 차이를 잰다.

    tol:  이 값 이하의 차이는 '같다' 로 본다. 보간·반올림 때문에 uint8 결과는 ±1 차이가 흔하다.
    peak: PSNR 계산의 최댓값 (uint8 이면 255, [0,1] float 이면 1).
    """
    a = np.asarray(mine, dtype=np.float64)
    b = np.asarray(ref, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(
            f"{name}: 모양이 다릅니다 mine={a.shape}, ref={b.shape}. "
            f"(가로·세로가 뒤바뀌었다면 (x, y) 와 (row, col) 순서를 확인하세요.)"
        )
    diff = np.abs(a - b)
    mse = float(np.mean(diff ** 2))
    psnr = float("inf") if mse == 0 else 10 * np.log10(peak ** 2 / mse)
    result = CompareResult(
        name=name, shape=a.shape, max_abs=float(diff.max()), mean_abs=float(diff.mean()),
        psnr=psnr, n_diff=int((diff > tol).sum()), total=diff.size, tol=tol, diff=diff,
    )
    if verbose:
        print(result)
    return result


def _heatmap_from_diff(diff: np.ndarray, *, vmax: float | None = None) -> np.ndarray:
    if diff.ndim == 3:
        diff = diff.max(axis=2)              # 채널 중 가장 큰 차이로 본다
    vmax = vmax if vmax is not None else float(diff.max())
    scaled = np.zeros(diff.shape, np.uint8) if vmax <= 0 else \
        np.clip(diff * (255.0 / vmax), 0, 255).astype(np.uint8)
    return cv2.applyColorMap(scaled, cv2.COLORMAP_INFERNO)


def diff_heatmap(mine, ref, *, vmax: float | None = None) -> np.ndarray:
    """차이 크기를 색으로 칠한 BGR 이미지. 검정 = 같음, 밝은 노랑 = 가장 많이 다름.

    vmax: 이 차이를 가장 밝은 색으로 칠한다. 생략하면 최대 차이 기준
          (그래서 차이가 1 뿐이어도 밝게 보인다 → 숫자와 함께 봐야 한다).
    """
    a = np.asarray(mine, dtype=np.float64)
    b = np.asarray(ref, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError(f"모양이 다릅니다 mine={a.shape}, ref={b.shape}")
    return _heatmap_from_diff(np.abs(a - b), vmax=vmax)
