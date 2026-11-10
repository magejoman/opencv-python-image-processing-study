"""리샘플링 방법들. 입력은 모두 같다: 어안 영상(float32) + 톱뷰 LUT. 다른 건 '읽는 방법' 뿐이다.

    양선형           cv2.remap 그대로. 이웃 4개만 읽는다 (축소 구간에서 나머지는 버려짐)
    ISP 샤프닝       원본을 언샤프 마스크로 날카롭게 한 뒤 양선형 (ISP 엣지 강조를 흉내)
    균일 프리블러     원본 전체에 같은 가우시안을 건 뒤 양선형 (위치 불변 = 회선)
    슈퍼샘플링       톱뷰를 n배 해상도로 만든 뒤 넓이 평균으로 줄인다
    피라미드         원본을 1/2, 1/4 … 로 줄여 두고, 발자국이 큰 곳은 작은 레벨에서 읽는다 (밉맵)
    비등방           피라미드 + 긴 축을 따라 여러 번 읽어 평균 (GPU 비등방 필터링을 소프트웨어로)
"""
from __future__ import annotations

import cv2
import numpy as np

from .lut import Footprint


def blur(src: np.ndarray, sigma: float) -> np.ndarray:
    return cv2.GaussianBlur(src, (0, 0), sigma) if sigma > 0 else src


def remap_bilinear(src: np.ndarray, map_x: np.ndarray, map_y: np.ndarray) -> np.ndarray:
    return cv2.remap(src, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def sharpen(src: np.ndarray, amount: float, sigma: float) -> np.ndarray:
    """언샤프 마스크: 원본 + amount × (원본 − 블러). 나이퀴스트 근처 고주파를 키운다."""
    return np.clip(src + amount * (src - blur(src, sigma)), 0, 1)


def supersample(src: np.ndarray, map_x_fine: np.ndarray, map_y_fine: np.ndarray, factor: int) -> np.ndarray:
    """gsd/factor 로 만든 LUT 로 크게 그린 뒤 INTER_AREA(넓이 평균)로 factor 배 줄인다.
    출력 화소 하나를 factor×factor 점으로 읽는 셈이라, factor 배 축소까지만 막아 준다."""
    big = remap_bilinear(src, map_x_fine, map_y_fine)
    h, w = big.shape[0] // factor, big.shape[1] // factor
    return cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA)


def build_pyramid(src: np.ndarray, levels: int) -> list[np.ndarray]:
    """[원본, 1/2, 1/4, …]. 각 단계 = 5×5 가우시안 블러 + 짝수 화소만 남기기 (위치 불변 회선 + 다운샘플)."""
    pyr = [src]
    for _ in range(levels):
        pyr.append(cv2.pyrDown(pyr[-1]))
    return pyr


def trilinear_lod(rho: np.ndarray, bias: float = 0.0) -> np.ndarray:
    """GPU 식 밉맵 레벨: log2(ρ) + bias. 0 이하(확대 구간)는 원본 레벨 0."""
    return np.maximum(np.log2(np.maximum(rho, 1e-6)) + bias, 0)


def _sample_levels(pyr, map_x, map_y, lod, blend: bool) -> np.ndarray:
    """화소마다 lod 에 해당하는 레벨에서 읽는다.

    pyrDown 의 레벨 k 화소 i 는 원본 좌표 i·2^k 에 놓인다 → 레벨 k 에서는 LUT 좌표를 2^k 로 나눠 읽는다.
    blend=True  (trilinear): 이웃한 두 레벨을 lod 의 소수부로 섞는다. 레벨 L 의 가중치 = max(0, 1 − |lod − L|)
    blend=False (최근접):     반올림한 레벨 하나만 → 레벨이 바뀌는 곳에서 선명도가 툭 끊긴다
    """
    lod = np.clip(lod, 0, len(pyr) - 1)
    out = np.zeros(map_x.shape, np.float32)
    for L, level in enumerate(pyr):
        w = np.maximum(0, 1 - np.abs(lod - L)) if blend else (np.rint(lod) == L).astype(np.float32)
        if not w.any():
            continue
        s = 0.5 ** L
        out += w.astype(np.float32) * remap_bilinear(level, map_x * s, map_y * s)
    return out


def pyramid_sample(src, map_x, map_y, lod, levels: int, *, blend: bool = True) -> np.ndarray:
    return _sample_levels(build_pyramid(src, levels), map_x, map_y, lod, blend)


def anisotropic(src, map_x, map_y, fp: Footprint, levels: int, max_probes: int, bias: float = 0.0) -> np.ndarray:
    """긴 축을 따라 N 번 읽어 평균한다 (EXT_texture_filter_anisotropic 와 같은 생각).

    등방 밉맵은 긴 축(s_max)에 맞춰 레벨을 고르므로 짧은 축 방향까지 흐려진다.
    여기서는 발자국을 긴 축 방향으로 N 조각 내고, 조각 하나(크기 s_max/N)에 맞는 레벨에서 읽는다.
      N   = ceil(s_max / max(s_min, 1))   짧은 축은 원본 1 화소보다 촘촘히 볼 필요가 없다
      lod = log2(max(s_max / N, s_min))   단, 짧은 축보다 덜 거르면 안 된다
              (거의 원인 발자국 s_max/s_min = 1.1 이면 N = 2 → s_max/2 는 짧은 축보다 작아서 앨리어싱이 남는다)
    """
    ratio = fp.s_max / np.maximum(fp.s_min, 1.0)
    n = np.clip(np.ceil(ratio - 1e-3), 1, max_probes)
    lod = np.maximum(np.log2(np.maximum(np.maximum(fp.s_max / n, fp.s_min), 1e-6)) + bias, 0)
    pyr = build_pyramid(src, levels)
    out = np.zeros(map_x.shape, np.float32)
    for i in range(max_probes):
        used = i < n                                       # 이 화소가 i 번째 탭을 쓰는가
        if not used.any():
            break
        t = (i + 0.5) / n - 0.5                            # 긴 축 위의 위치: −0.5 ~ +0.5
        px = (map_x + t * fp.major[..., 0]).astype(np.float32)
        py = (map_y + t * fp.major[..., 1]).astype(np.float32)
        out += np.where(used, _sample_levels(pyr, px, py, lod, True), 0)
    return out / n.astype(np.float32)
