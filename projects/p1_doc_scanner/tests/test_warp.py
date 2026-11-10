"""Step 5 채점: warp_perspective"""
import cv2
import numpy as np

from cvkit import compare
from scanner.warp import warp_perspective


def _test_image(h=120, w=160):
    rng = np.random.default_rng(0)
    smooth = cv2.GaussianBlur(rng.integers(0, 256, (h, w, 3), np.uint8), (0, 0), 2)
    cv2.putText(smooth, "AB", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)   # 날카로운 엣지도
    return smooth


def test_identity_is_exact():
    img = _test_image()
    out = warp_perspective(img, np.eye(3), (img.shape[1], img.shape[0]))
    assert out.dtype == np.uint8 and np.array_equal(out, img), "항등 변환이면 원본과 완전히 같아야 한다"


def test_output_shape_uses_width_height_order():
    img = _test_image()
    out = warp_perspective(img, np.eye(3), (90, 50))       # size = (width, height)
    assert out.shape == (50, 90, 3), f"shape 은 (height, width, c) 여야 한다: {out.shape}"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    assert warp_perspective(gray, np.eye(3), (90, 50)).shape == (50, 90), "그레이 입력이면 그레이 출력"


def test_matches_opencv_perspective():
    img = _test_image()
    src = np.float32([[10, 8], [150, 20], [140, 110], [5, 100]])
    dst = np.float32([[0, 0], [199, 0], [199, 149], [0, 149]])
    H = cv2.getPerspectiveTransform(src, dst)
    mine = warp_perspective(img, H, (200, 150))
    ref = cv2.warpPerspective(img, H, (200, 150))
    r = compare(mine, ref, tol=1, verbose=False)
    # OpenCV 는 원본 좌표를 1/32 픽셀 단위로 반올림한다 (GUIDE.md §5.6).
    # 그래서 글자 테두리처럼 밝기가 급변하는 곳에서 최대 4~5 정도 차이는 정상이다.
    # 평균 차이가 크거나 다른 픽셀이 많으면 보간식·좌표 순서·경계 처리 중 하나가 틀린 것.
    assert r.max_abs <= 6 and r.mean_abs < 0.2 and r.n_diff / r.total < 0.02, str(r)


def test_outside_is_black():
    img = np.full((50, 50, 3), 200, np.uint8)
    H = np.array([[1, 0, 30], [0, 1, 0], [0, 0, 1]], np.float64)         # 오른쪽으로 30 이동
    out = warp_perspective(img, H, (60, 50))                              # 출력 u → 원본 x = u − 30
    assert out[:, :30].max() == 0, "원본 바깥(x < 0)에서 온 픽셀은 0 이어야 한다"
    assert out[:, 30:].min() == 200, "원본 안쪽은 그대로"
