"""(제공) 정답(GT)과 비교하는 평가 도구.

정답 파일: 이미지 폴더 안의 gt.json
    { "001.jpg": [[x, y], [x, y], [x, y], [x, y]], ... }   ← 원본 해상도 기준, 좌상·우상·우하·좌하 순서
만드는 법: 합성 데이터는 tools/make_synthetic.py 가 자동 생성, 직접 찍은 사진은 tools/label_corners.py 로 클릭.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def load_gt(folder) -> dict[str, np.ndarray]:
    path = Path(folder) / "gt.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {name: np.asarray(pts, np.float32) for name, pts in data.items()}


def save_gt(folder, gt: dict) -> Path:
    path = Path(folder) / "gt.json"
    data = {name: np.asarray(pts).round(2).tolist() for name, pts in sorted(gt.items())}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def corner_error(pred: np.ndarray, gt: np.ndarray) -> dict:
    """정렬된 꼭짓점끼리의 거리(px). 순서가 틀리면 오차가 커지므로 Step 3 검증도 된다."""
    d = np.linalg.norm(np.asarray(pred, np.float64) - np.asarray(gt, np.float64), axis=1)
    return {"err_mean_px": float(d.mean()), "err_max_px": float(d.max())}
