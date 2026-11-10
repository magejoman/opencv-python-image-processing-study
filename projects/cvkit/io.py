"""이미지 입출력.

cv2.imread / cv2.imwrite 는 Windows 에서 경로에 한글이 있으면 조용히 실패한다
(imread 는 None, imwrite 는 False 를 돌려줄 뿐 에러를 내지 않는다).
그래서 파일은 numpy 로 바이트째 읽고/쓰고, 인코딩·디코딩만 OpenCV 에 맡긴다.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def imread(path, flags: int = cv2.IMREAD_COLOR, *, max_side: int | None = None) -> np.ndarray:
    """이미지를 읽는다. 실패하면 None 대신 이유가 담긴 예외를 던진다.

    max_side: 긴 변이 이 값보다 크면 비율을 유지하며 줄인다.
              폰 사진(4000px 안팎)을 그대로 처리하면 느리고 화면에도 안 들어온다.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"이미지 파일이 없습니다: {path}")
    buf = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(buf, flags)
    if img is None:
        raise ValueError(f"이미지로 디코딩할 수 없습니다 (손상됐거나 지원하지 않는 형식): {path}")
    if max_side:
        h, w = img.shape[:2]
        scale = max_side / max(h, w)
        if scale < 1:
            img = cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def imwrite(path, img: np.ndarray, params: list[int] | None = None) -> Path:
    """이미지를 저장한다. 상위 폴더가 없으면 만든다. 확장자로 형식을 정한다."""
    path = Path(path)
    if not path.suffix:
        raise ValueError(f"확장자가 없어 저장 형식을 알 수 없습니다: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(path.suffix, img, params or [])
    if not ok:
        raise ValueError(f"인코딩 실패 (dtype={img.dtype}, shape={img.shape}): {path}")
    buf.tofile(str(path))
    return path


def list_images(folder, *, recursive: bool = False) -> list[Path]:
    """폴더 안의 이미지 파일을 이름순으로 돌려준다."""
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"폴더가 없습니다: {folder}")
    entries = folder.rglob("*") if recursive else folder.iterdir()
    return sorted(p for p in entries if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
