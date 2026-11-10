"""톱뷰 LUT 와 '발자국(footprint)': 출력 화소 하나가 원본에서 얼마나 넓은 영역을 덮는가.

LUT (map_x, map_y) 는 출력 화소마다 '어안 영상의 어디를 읽을지' 를 적어 둔 표다 (cv2.remap 입력).
이웃한 출력 화소의 LUT 값 차이(차분)가 곧 '출력 한 칸 = 원본 몇 화소' 다.

    J = | du/dx  du/dy |     u, v: 원본(어안) 좌표    x, y: 출력(톱뷰) 화소 좌표
        | dv/dx  dv/dy |

J 는 출력의 작은 정사각형을 원본의 평행사변형(대략 타원)으로 보낸다. 이 타원이 '발자국' 이다.
  - 특이값 s_max, s_min = 타원의 긴 반지름·짧은 반지름 (원본 화소 단위)
  - s > 1: 원본 화소를 건너뛴다 (축소, 앨리어싱 위험)    s < 1: 원본 화소를 늘려 쓴다 (확대, 흐림)
  - GPU 는 특이값 대신 더 싼 근사 ρ = max(|J 1열|, |J 2열|) 로 밉맵 레벨 log2(ρ) 를 고른다

AVM 은 캘리브레이션 뒤 LUT 가 고정이므로, 이 계산을 오프라인에서 한 번만 하면 된다.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .camera import FisheyeCamera


@dataclass
class TopView:
    """톱뷰 격자와 LUT. 위쪽 행 = 차에서 먼 곳, 아래쪽 행 = 차 바로 옆."""
    map_x: np.ndarray      # (H, W) float32 — cv2.remap 에 그대로 넣는다
    map_y: np.ndarray
    valid: np.ndarray      # bool, 어안 시야 안
    X: np.ndarray          # 출력 화소 중심의 월드 좌표 (m)
    Y: np.ndarray
    gsd: float             # 출력 화소 하나 = gsd m
    x0: float
    y1: float              # 맨 위 행의 위쪽 끝 Y

    @property
    def shape(self) -> tuple[int, int]:
        return self.map_x.shape

    def rows_cols(self, box) -> tuple[slice, slice]:
        """월드 영역 (x0, x1, y0, y1) m → 배열 슬라이스 (행, 열)."""
        x0, x1, y0, y1 = box
        c0, c1 = round((x0 - self.x0) / self.gsd), round((x1 - self.x0) / self.gsd)
        r0, r1 = round((self.y1 - y1) / self.gsd), round((self.y1 - y0) / self.gsd)
        H, W = self.shape
        return slice(max(r0, 0), min(r1, H)), slice(max(c0, 0), min(c1, W))

    def box_mask(self, box, inset: float = 0.0) -> np.ndarray:
        x0, x1, y0, y1 = box
        return ((self.X >= x0 + inset) & (self.X < x1 - inset)
                & (self.Y >= y0 + inset) & (self.Y < y1 - inset) & self.valid)

    def row_of(self, y: float) -> int:
        return round((self.y1 - y) / self.gsd)


def make_topview(cam: FisheyeCamera, gsd: float, x_range, y_range) -> TopView:
    """톱뷰 화소 → 지면 점 → 어안 좌표. 이 표가 제품의 '톱뷰 LUT' 와 같은 것이다."""
    x0, x1 = x_range
    y0, y1 = y_range
    W, H = round((x1 - x0) / gsd), round((y1 - y0) / gsd)
    xs = x0 + (np.arange(W) + 0.5) * gsd                 # 화소 중심
    ys = y1 - (np.arange(H) + 0.5) * gsd                 # 행이 내려갈수록 Y 가 작아진다 (차에 가까워짐)
    X, Y = np.meshgrid(xs, ys)
    u, v, valid = cam.ground_to_image(X, Y)
    return TopView(u.astype(np.float32), v.astype(np.float32), valid, X, Y, gsd, x0, y1)


@dataclass
class Footprint:
    step_x: np.ndarray     # 출력에서 오른쪽 한 칸 → 원본에서 몇 화소 이동
    step_y: np.ndarray     # 출력에서 아래쪽 한 칸 → 원본에서 몇 화소 이동
    rho: np.ndarray        # max(step_x, step_y) — GPU 가 밉맵 레벨을 고를 때 쓰는 값
    s_max: np.ndarray      # 발자국 타원의 긴 반지름 (원본 화소)
    s_min: np.ndarray      # 짧은 반지름
    major: np.ndarray      # (H, W, 2) 긴 축 방향 벡터 (원본 좌표, 길이 = s_max)

    @property
    def aniso(self) -> np.ndarray:
        """길쭉한 정도. 1 이면 원, 클수록 길쭉한 타원."""
        return self.s_max / np.maximum(self.s_min, 1e-6)


def footprint(map_x: np.ndarray, map_y: np.ndarray) -> Footprint:
    """LUT 의 차분으로 발자국을 구한다 (np.gradient = 가운데 차분)."""
    a = np.gradient(map_x.astype(np.float64), axis=1)    # du/dx
    b = np.gradient(map_x.astype(np.float64), axis=0)    # du/dy
    c = np.gradient(map_y.astype(np.float64), axis=1)    # dv/dx
    d = np.gradient(map_y.astype(np.float64), axis=0)    # dv/dy
    step_x, step_y = np.hypot(a, c), np.hypot(b, d)      # J 의 1열, 2열 길이

    # 2×2 의 특이값은 닫힌 식으로: JᵀJ = [[p, r], [r, q]] 의 고윳값의 제곱근
    p, q, r = a * a + c * c, b * b + d * d, a * b + c * d
    disc = np.sqrt((p - q) ** 2 + 4 * r * r)
    s_max = np.sqrt((p + q + disc) / 2)
    s_min = np.sqrt(np.maximum((p + q - disc) / 2, 0))
    # 긴 축: 출력에서 φ 방향으로 한 칸 가면 원본에서 가장 많이 움직인다. 그 원본 쪽 벡터 = J·(cosφ, sinφ)
    phi = 0.5 * np.arctan2(2 * r, p - q)
    major = np.stack([a * np.cos(phi) + b * np.sin(phi), c * np.cos(phi) + d * np.sin(phi)], -1)
    return Footprint(step_x, step_y, np.maximum(step_x, step_y), s_max, s_min, major)
