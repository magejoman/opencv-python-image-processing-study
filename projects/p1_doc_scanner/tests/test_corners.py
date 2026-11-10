"""Step 3 채점: order_corners, quad_size"""
import itertools

import numpy as np

from scanner.corners import order_corners, quad_size


def _rotated_rect(angle_deg, w=200, h=300, center=(500, 400)):
    a = np.deg2rad(angle_deg)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    rect = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]])  # 좌상 우상 우하 좌하
    return rect @ R.T + center


def test_axis_aligned_any_order():
    expected = np.array([[10, 20], [110, 20], [110, 220], [10, 220]], np.float32)
    for perm in itertools.permutations(range(4)):
        got = order_corners(expected[list(perm)])
        assert np.allclose(got, expected), f"입력 순서 {perm} 에서 실패: {got.tolist()}"


def test_rotated_up_to_40_degrees():
    for angle in range(-40, 41, 5):
        expected = _rotated_rect(angle)
        for perm in itertools.permutations(range(4)):
            got = order_corners(expected[list(perm)])
            assert np.allclose(got, expected, atol=1e-3), \
                f"{angle}° 기울어진 사각형, 입력 순서 {perm}: {np.round(got, 1).tolist()}"


def test_perspective_quad():
    expected = np.array([[120, 80], [400, 110], [430, 500], [90, 470]], np.float32)   # 사다리꼴 비슷한 모양
    assert np.allclose(order_corners(expected[[2, 0, 3, 1]]), expected)


def test_strong_perspective_breaks_sum_diff_trick():
    """x+y / y−x 트릭은 여기서 좌하 점을 두 번 고른다 (GUIDE.md §3.3). 각도로 정렬해야 통과한다."""
    expected = np.array([[100, 100], [200, 90], [210, 200], [20, 160]], np.float32)
    for perm in itertools.permutations(range(4)):
        got = order_corners(expected[list(perm)])
        assert np.allclose(got, expected), f"입력 순서 {perm}: {got.tolist()}"


def test_accepts_approxpolydp_shape_and_returns_float32():
    pts = np.array([[[110, 220]], [[10, 20]], [[10, 220]], [[110, 20]]], np.int32)    # (4, 1, 2) int32
    got = order_corners(pts)
    assert got.shape == (4, 2) and got.dtype == np.float32
    assert got.tolist() == [[10, 20], [110, 20], [110, 220], [10, 220]]


def test_quad_size():
    rect = np.array([[0, 0], [100, 0], [100, 50], [0, 50]], np.float32)
    assert tuple(quad_size(rect)) == (100, 50)
    trapezoid = np.array([[20, 0], [100, 0], [120, 60], [0, 60]], np.float32)       # 위 80, 아래 120
    w, h = quad_size(trapezoid)
    assert (w, h) == (120, 63), f"너비는 긴 쪽(120), 높이는 긴 쪽(√(20²+60²)≈63.2 → 63): {(w, h)}"
    assert all(isinstance(v, (int, np.integer)) for v in (w, h)), "정수여야 한다 (출력 이미지 크기)"
