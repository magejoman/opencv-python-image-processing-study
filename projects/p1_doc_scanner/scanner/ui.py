"""(제공) 마우스로 네 꼭짓점 찍기 — 자동 검출 실패 시 수동 보정, 그리고 정답 라벨링에 쓴다.

chap04 마우스 이벤트, chap08 11.perspective_event.py 의 응용이다.
"""
from __future__ import annotations

import cv2
import numpy as np

from cvkit import to_display

CORNER_NAMES = ["TL", "TR", "BR", "BL"]       # 좌상, 우상, 우하, 좌하
HELP = "click TL->TR->BR->BL | right-click: undo | Enter: OK | s: skip | ESC: quit"


def pick_corners(img: np.ndarray, *, window: str = "pick corners", max_side: int = 1000,
                 initial=None) -> np.ndarray | None | str:
    """창에 img 를 띄우고 좌상 → 우상 → 우하 → 좌하 순서로 네 점을 클릭받는다.

    화면에 맞게 줄여서 보여주지만, 돌려주는 좌표는 img 원래 크기 기준이다.
    initial: 처음부터 찍혀 있을 점들 (예: 자동 검출 결과를 고칠 때)
    돌려주는 값: (4, 2) float32 | None (s: 건너뜀) | "quit" (ESC)
    """
    base = to_display(img)
    scale = min(1.0, max_side / max(base.shape[:2]))
    view = cv2.resize(base, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else base.copy()
    pts: list[tuple[float, float]] = [] if initial is None else [tuple(p) for p in np.asarray(initial) * scale]

    def redraw():
        canvas = view.copy()
        for i, (x, y) in enumerate(pts):
            cv2.circle(canvas, (round(x), round(y)), 6, (0, 0, 255), -1)
            cv2.putText(canvas, CORNER_NAMES[i], (round(x) + 8, round(y) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        if len(pts) >= 2:
            cv2.polylines(canvas, [np.array(pts, np.int32)], len(pts) == 4, (0, 255, 0), 2)
        nxt = CORNER_NAMES[len(pts)] if len(pts) < 4 else "Enter to confirm"
        cv2.putText(canvas, f"next: {nxt}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(canvas, HELP, (10, canvas.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        cv2.imshow(window, canvas)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(pts) < 4:
            pts.append((x, y))
            redraw()
        elif event == cv2.EVENT_RBUTTONDOWN and pts:
            pts.pop()
            redraw()

    cv2.namedWindow(window)
    cv2.setMouseCallback(window, on_mouse)
    redraw()
    result = None
    while True:
        key = cv2.waitKey(30) & 0xFF
        if key == 13 and len(pts) == 4:                       # Enter
            result = (np.array(pts, np.float32) / scale).astype(np.float32)
            break
        if key == ord("s"):
            break
        if key == 27 or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            result = "quit"
            break
    cv2.destroyWindow(window)
    return result
