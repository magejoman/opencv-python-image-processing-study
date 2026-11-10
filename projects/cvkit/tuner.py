"""트랙바 튜너 (chap04 트랙바 이벤트의 실전판).

파라미터를 트랙바로 움직이며 결과를 실시간으로 보고, 마음에 드는 값을 찾으면 's' 로 저장한다.
저장된 값은 바로 쓰이지 않는다. 직접 확인한 뒤 config.yaml 에 옮겨 적어 '고정' 한다.

    params = Param.from_config(cfg.params, cfg.tune)     # config.yaml 의 params + tune 범위
    best = tune(img, lambda im, **p: pipeline(im, **p), params,
                save_path=proj.result_path("tuned_params.yaml"))

트랙바는 정수만 다루므로, Param 이 '정수 위치 ↔ 실제 값' 을 바꿔 준다.
    값 = lo + 위치 × step     (예: lo=1, step=2 → 1, 3, 5, … 홀수만 → GaussianBlur ksize 에 딱 맞음)
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .viz import Stages, _fit, mosaic, to_display


@dataclass
class Param:
    name: str           # 트랙바 이름 (영문으로: OpenCV 창은 한글이 깨진다)
    init: float
    lo: float
    hi: float
    step: float = 1

    def __post_init__(self):
        if self.step <= 0 or self.hi < self.lo:
            raise ValueError(f"{self.name}: 범위가 잘못됐습니다 (lo={self.lo}, hi={self.hi}, step={self.step})")
        self.is_int = all(float(v).is_integer() for v in (self.init, self.lo, self.hi, self.step))

    @property
    def count(self) -> int:
        """트랙바 최대 위치."""
        return int(round((self.hi - self.lo) / self.step))

    def to_pos(self, value: float) -> int:
        return int(np.clip(round((value - self.lo) / self.step), 0, self.count))

    def to_value(self, pos: int):
        value = self.lo + pos * self.step
        return int(round(value)) if self.is_int else round(value, 6)

    @staticmethod
    def from_config(params: dict, ranges: dict) -> list["Param"]:
        """params: {이름: 초깃값}, ranges: {이름: [최소, 최대, 간격]} → ranges 에 있는 것만 Param 으로."""
        out = []
        for name, rng in ranges.items():
            if name not in params:
                raise KeyError(f"tune 에 '{name}' 범위는 있는데 params 에 초깃값이 없습니다.")
            lo, hi, *rest = rng
            out.append(Param(name, params[name], lo, hi, rest[0] if rest else 1))
        return out


def tune(image: np.ndarray, process, params: list[Param], *, window: str = "tuner",
         save_path=None, fixed: dict | None = None, max_side: int = 1200) -> dict:
    """트랙바로 params 를 바꿔가며 process(image, **값) 결과를 보여준다.

    process 는 이미지 하나, [(라벨, 이미지), ...], 또는 Stages 를 돌려주면 된다.
    fixed:  트랙바로 움직이지 않을 나머지 인자 (예: config 의 다른 params)
    키:     s = save_path 에 현재 값 저장,  ESC / q = 종료 (창을 닫아도 종료)
    돌려주는 값: 마지막 파라미터 값 dict
    """
    from .config import save_config

    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    for p in params:
        cv2.createTrackbar(p.name, window, p.to_pos(p.init), p.count, lambda _pos: None)
    print(f"[튜너] 트랙바를 움직여 보세요. s = 저장{'' if save_path else ' (save_path 없음)'}, ESC/q = 종료")

    last, values = None, {}
    while True:
        values = {p.name: p.to_value(cv2.getTrackbarPos(p.name, window)) for p in params}
        if values != last:
            try:
                out = process(image, **(fixed or {}), **values)
                view = mosaic(out) if isinstance(out, (list, tuple, dict, Stages)) else to_display(out)
            except Exception as e:      # 잘못된 조합(예: low > high)이어도 튜너가 죽지 않게
                view = np.zeros((200, 600, 3), np.uint8)
                cv2.putText(view, f"error: {type(e).__name__}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                print(f"[튜너] {values} → {type(e).__name__}: {e}")
            if max(view.shape[:2]) > max_side:
                view = _fit(view, max_side, max_side)
            cv2.imshow(window, view)
            last = values

        key = cv2.waitKey(30) & 0xFF
        if key in (27, ord("q")) or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break
        if key == ord("s"):
            if save_path:
                print(f"[튜너] 저장: {save_config(values, save_path)} ← {values}")
            else:
                print(f"[튜너] 현재 값: {values}")

    cv2.destroyWindow(window)
    print(f"[튜너] 최종 값: {values}")
    return values
