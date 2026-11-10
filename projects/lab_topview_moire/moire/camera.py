"""등거리 어안 카메라 모델: 지면 ↔ 영상 대응.

좌표계
  월드:   X = 차가 달리는 방향, Y = 차에서 바깥쪽, Z = 위.  카메라는 (0, 0, h) 에 있다 (사이드 미러 카메라).
  카메라: x = 오른쪽, y = 아래, z = 광축(앞).  광축은 수평에서 pitch 만큼 아래로 기울어 있다.
  영상:   (u, v) = (가로, 세로) 화소 좌표.  cv2.remap 과 같은 관례 (화소 중심이 정수 좌표).

등거리 어안: 광축에서 θ 만큼 벗어난 광선은 영상 중심에서 r = f·θ 만큼 떨어진 곳에 맺힌다.
핀홀은 r = f·tanθ 라서 θ → 90° 면 r → ∞ 이지만, 어안은 θ 에 비례하니 180° 넘게도 한 장에 담는다.
대신 같은 1 화소가 가까운 바닥에서는 몇 mm, 먼 바닥에서는 몇 cm 를 덮게 된다 → 이 실험의 출발점.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FisheyeCamera:
    width: int
    height: int
    hfov_deg: float      # 가로 화각. 영상 가로 끝(width/2 화소)이 hfov/2 에 오도록 f 를 정한다
    height_m: float      # 카메라 높이
    pitch_deg: float     # 수평에서 아래로 기운 각도

    @property
    def f(self) -> float:
        """화소/라디안. 1280 px · 190° 면 약 386 → 1 화소 ≈ 2.6 mrad."""
        return (self.width / 2) / np.deg2rad(self.hfov_deg / 2)

    @property
    def center(self) -> tuple[float, float]:
        return (self.width - 1) / 2, (self.height - 1) / 2

    def axes(self) -> np.ndarray:
        """카메라의 x, y, z 축을 월드 좌표로 쓴 3×3 (행 하나가 축 하나). 회전 행렬이라 역행렬 = 전치."""
        p = np.deg2rad(self.pitch_deg)
        return np.array([[1.0, 0.0, 0.0],                  # x: 오른쪽 = 월드 +X
                         [0.0, -np.sin(p), -np.cos(p)],    # y: 아래
                         [0.0, np.cos(p), -np.sin(p)]])    # z: 광축 (바깥쪽 아래)

    def ground_to_image(self, X, Y):
        """지면 점 (X, Y, 0) → 영상 좌표 (u, v) 와 '센서 안에 맺히는지' (valid).

        톱뷰 LUT 를 만들 때 쓴다: 톱뷰 화소 → 지면 점 → 이 함수 → 어안에서 읽을 위치.
        """
        X = np.asarray(X, np.float64)
        Y = np.asarray(Y, np.float64)
        d = np.stack([X, Y, np.full_like(X, -self.height_m)], -1)    # 카메라 → 지면 점 벡터
        xc, yc, zc = np.moveaxis(d @ self.axes().T, -1, 0)           # 월드 → 카메라 좌표
        rho = np.hypot(xc, yc)
        theta = np.arctan2(rho, zc)                                  # 광축과 이루는 각
        r = self.f * theta                                           # 등거리 어안: r = f·θ
        cx, cy = self.center
        safe = np.maximum(rho, 1e-12)
        u = cx + r * xc / safe
        v = cy + r * yc / safe
        valid = ((theta < np.deg2rad(self.hfov_deg / 2))
                 & (u >= 0) & (u <= self.width - 1) & (v >= 0) & (v <= self.height - 1))
        return u, v, valid

    def image_to_ground(self, u, v):
        """영상 좌표 → 그 화소로 들어오는 광선이 지면과 만나는 점 (X, Y) 와 '지면에 닿는지' (valid).

        합성 어안 영상을 렌더링할 때 쓴다: 센서 화소마다 광선을 쏴서 바닥 무늬를 읽는다.
        """
        cx, cy = self.center
        du, dv = np.asarray(u, np.float64) - cx, np.asarray(v, np.float64) - cy
        theta = np.hypot(du, dv) / self.f
        phi = np.arctan2(dv, du)
        ray_cam = np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], -1)
        ray = ray_cam @ self.axes()                                  # 카메라 → 월드 (전치 = 역회전)
        down = -ray[..., 2]                                          # 아래로 향하는 성분
        valid = (down > 1e-6) & (theta < np.deg2rad(self.hfov_deg / 2))
        t = np.where(valid, self.height_m / np.where(valid, down, 1.0), 0.0)   # 높이 h 를 내려가는 데 걸리는 길이
        return t * ray[..., 0], t * ray[..., 1], valid
