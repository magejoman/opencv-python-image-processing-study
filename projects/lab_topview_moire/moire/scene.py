"""합성 장면: 수식으로 정의한 바닥, 그 바닥을 찍은 어안 영상, 정답 톱뷰.

바닥 무늬를 '수식'으로 정의하면 어느 좌표든 값을 바로 계산할 수 있다.
그래서 카메라 영상과 정답 톱뷰를 같은 바닥에서 만들고, 둘을 화소 단위로 비교할 수 있다.

무늬 (크기는 전부 실제 바닥처럼 m 단위)
  - 30 cm 체커보드 타일 + 1.5 cm 줄눈        : 저주파. 어떤 방법이든 살아남아야 한다
  - 8 mm 미끄럼 방지 홈 (사인파)             : 톱뷰 1 cm/px 의 나이퀴스트(2 cm)보다 촘촘 → 모아레의 원인
  - 12 mm 배수구 그레이팅 (사인파, 근거리)    : 대비가 커서 모아레가 가장 잘 보이는 곳
  - 10 cm 줄무늬 표시 두 곳 (사인파)         : 톱뷰로 표현 가능한 무늬. 흐려지면 손해 → '선명도' 측정용
      중거리: Y 방향으로 반복 (카메라에서 멀어지는 방향, 비등방 필터의 이득이 보이는 곳)
      원거리: X 방향으로 반복 (균일 블러의 손해가 보이는 곳)
  - 12 cm 흰 주차선 두 줄

fine=0 으로 부르면 미세 무늬(홈·그레이팅)만 평균값으로 바꾼 '깨끗한' 바닥이 나온다.
같은 방법으로 두 바닥을 톱뷰로 보내 차이를 보면, 미세 무늬가 톱뷰에 남긴 흔적(= 모아레)만 따로 잴 수 있다.

시뮬레이터도 앨리어싱을 피해야 한다
  먼 바닥에서는 센서 화소 하나가 몇 cm 를 덮는다. 그 화소를 몇 점으로만 찍으면 8 mm 홈이 '카메라 안에서'
  거짓 무늬로 바뀌어 버린다 (실제 센서는 화소 면적 전체로 빛을 모으므로 그런 일이 거의 없다).
  그래서 사인파 무늬는 찍기 전에 수식으로 흐린다: 가우시안 블러(σ)는 주기 P 인 사인파의 진폭을
  exp(-2π²σ²/P²) 배로 줄인다 (chap09 의 '가우시안의 주파수 응답도 가우시안').
  '샘플링 전에 거른다' — 이 실험이 톱뷰에서 확인하려는 원칙을 시뮬레이터에도 똑같이 적용한 것이다.
"""
from __future__ import annotations

import cv2
import numpy as np

from .camera import FisheyeCamera

TILE = 0.30
GROUT = 0.015
RIB_PERIOD = 0.008
GRATING_BOX = (0.6, 1.6, 0.5, 1.1)          # (x0, x1, y0, y1) m
GRATING_PERIOD = 0.012
MID_BARS_BOX = (-0.8, 0.8, 2.0, 3.2)        # X = 0 근처: Y 방향 = 카메라에서 멀어지는 방향(반경)
FAR_BARS_BOX = (-0.8, 0.8, 4.3, 5.7)        # X 방향 = 반경에 수직(접선) → 카메라가 아직 잘 분해하는 방향
BARS_PERIOD = 0.10
LINE_W = 0.12
CAR_BODY = 0.12                             # Y < 0 (차 밑) 으로 가는 광선은 차체에 가린다
SKY = 0.7


def inside(X, Y, box) -> np.ndarray:
    x0, x1, y0, y1 = box
    return (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)


def _sine(t, period, sigma):
    """cos(2πt/P) 를 가우시안(σ)으로 미리 흐린 값. σ=0 이면 원래 사인파."""
    return np.exp(-2 * np.pi**2 * (np.asarray(sigma) / period) ** 2) * np.cos(2 * np.pi * t / period)


def ground_texture(X, Y, sx=0.0, sy=0.0, fine: float = 1.0) -> np.ndarray:
    """월드 좌표 (m) → 밝기 [0, 1] (float32).

    sx, sy: 사인파 무늬를 X, Y 방향으로 미리 흐릴 가우시안 σ (m). 스칼라 또는 X 와 같은 모양의 배열.
    fine:   미세 무늬(홈·그레이팅)의 세기. 0 이면 그 자리를 평균 밝기로 채운다.
    """
    X = np.asarray(X, np.float64)
    Y = np.asarray(Y, np.float64)
    light = (np.floor(X / TILE) + np.floor(Y / TILE)) % 2 == 0          # 체커보드
    # 미끄럼 방지 홈: 밝은 타일은 X 방향, 어두운 타일은 Y 방향으로 반복
    rib = np.where(light, _sine(X, RIB_PERIOD, sx), _sine(Y, RIB_PERIOD, sy))
    lum = np.where(light, 0.62, 0.42) + fine * 0.16 * rib
    lum = np.where((np.mod(X, TILE) < GROUT) | (np.mod(Y, TILE) < GROUT), 0.22, lum)   # 줄눈

    lum = np.where(inside(X, Y, GRATING_BOX), 0.45 + fine * 0.35 * _sine(Y, GRATING_PERIOD, sy), lum)
    lum = np.where(inside(X, Y, MID_BARS_BOX), 0.55 + 0.30 * _sine(Y, BARS_PERIOD, sy), lum)
    lum = np.where(inside(X, Y, FAR_BARS_BOX), 0.55 + 0.30 * _sine(X, BARS_PERIOD, sx), lum)

    line = ((Y >= 3.4) & (Y < 3.4 + LINE_W)) | ((X >= 1.2) & (X < 1.2 + LINE_W) & (Y >= 1.2))
    lum = np.where(line, 0.92, lum)
    return lum.astype(np.float32)


def render_fisheye(cam: FisheyeCamera, views=((0.0, 1.0),), *, ss: int = 4,
                   lens_sigma: float = 0.6) -> list[np.ndarray]:
    """바닥을 어안 카메라로 찍은 영상들 (float32, [0, 1]).

    views:  영상마다 (차가 X 방향으로 움직인 거리 m, 미세 무늬 세기 fine) 의 목록.
            기하(광선 → 지면 점)는 영상마다 같으므로 한 번만 계산하고 무늬만 바꿔 읽는다.
    ss:     센서 화소는 점이 아니라 면적으로 빛을 모은다 → 화소 하나를 ss×ss 점으로 나눠 평균 (박스 적분).
    lens_sigma: 렌즈 번짐 (화소 단위 가우시안).
    """
    v, u = np.mgrid[0:cam.height, 0:cam.width].astype(np.float64)
    # 센서 화소 하나가 덮는 바닥 크기 (m/화소) → 한 샘플이 덮는 크기의 절반을 무늬의 사전 블러 σ 로 쓴다
    X0, Y0, _ = cam.image_to_ground(u, v)
    sx = 0.5 * np.hypot(np.gradient(X0, axis=1), np.gradient(X0, axis=0)) / ss
    sy = 0.5 * np.hypot(np.gradient(Y0, axis=1), np.gradient(Y0, axis=0)) / ss
    # 아주 먼 바닥은 몇 점으로 적분을 흉내 낼 수 없다 → 평균 밝기로 바랜다.
    # 시작점 16 mm 는 기본 설정의 톱뷰 범위 안 최댓값(약 15 mm)보다 커서 톱뷰에는 영향이 없다.
    fade = np.clip((np.maximum(sx, sy) - 0.016) / 0.016, 0, 1)

    acc = [np.zeros((cam.height, cam.width), np.float64) for _ in views]
    for i in range(ss):
        for j in range(ss):
            X, Y, ok = cam.image_to_ground(u + (j + 0.5) / ss - 0.5, v + (i + 0.5) / ss - 0.5)
            for a, (shift, fine) in zip(acc, views):
                ground = (1 - fade) * ground_texture(X + shift, Y, sx, sy, fine) + fade * 0.5
                a += np.where(ok, np.where(Y >= 0, ground, CAR_BODY), SKY)
    frames = []
    for a in acc:
        img = (a / (ss * ss)).astype(np.float32)
        frames.append(cv2.GaussianBlur(img, (0, 0), lens_sigma) if lens_sigma > 0 else img)
    return frames


def render_truth(X, Y, gsd: float, *, ss: int = 4, shift: float = 0.0, fine: float = 1.0) -> np.ndarray:
    """정답 톱뷰: 카메라를 거치지 않고 바닥 무늬에서 바로 계산한 '이상적인' 톱뷰.

    출력 화소 하나가 덮는 gsd×gsd 정사각형을 ss×ss 점으로 평균하고, 사인파 무늬는 σ = gsd/2 로 미리 흐린다.
    → 출력 나이퀴스트(주기 2 화소)보다 촘촘한 홈·그레이팅은 고른 회색이 되고, 10 cm 줄무늬는 남는다.
    """
    acc = np.zeros(np.shape(X), np.float64)
    for i in range(ss):
        for j in range(ss):
            acc += ground_texture(X + ((j + 0.5) / ss - 0.5) * gsd + shift,
                                  Y + ((i + 0.5) / ss - 0.5) * gsd, gsd / 2, gsd / 2, fine)
    return (acc / (ss * ss)).astype(np.float32)
