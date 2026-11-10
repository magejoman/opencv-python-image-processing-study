"""Step 4 채점: homography_dlt"""
import cv2
import numpy as np

from scanner.homography import apply_homography, homography_dlt


def _random_quad(rng):
    base = np.array([[0, 0], [600, 0], [600, 850], [0, 850]], np.float64)
    return (base + rng.uniform(-80, 80, (4, 2)) + rng.uniform(0, 300, 2)).astype(np.float32)


def test_four_points_match_opencv():
    rng = np.random.default_rng(0)
    dst = np.array([[0, 0], [599, 0], [599, 847], [0, 847]], np.float32)
    for _ in range(20):
        src = _random_quad(rng)
        H = homography_dlt(src, dst)
        assert H.shape == (3, 3)
        H = H / H[2, 2]
        H_cv = cv2.getPerspectiveTransform(src, dst)
        assert np.allclose(H, H_cv, rtol=1e-6, atol=1e-9), f"OpenCV 와 다릅니다:\n{H}\n{H_cv}"
        assert np.abs(apply_homography(H, src) - dst).max() < 1e-4, "src 를 변환하면 dst 가 나와야 한다"


def test_many_exact_points():
    """점이 4개보다 많아도 (잡음이 없으면) 정확히 맞아야 한다."""
    rng = np.random.default_rng(1)
    H_true = cv2.getPerspectiveTransform(_random_quad(rng), np.float32([[0, 0], [599, 0], [599, 847], [0, 847]]))
    src = rng.uniform(0, 900, (12, 2))
    dst = apply_homography(H_true, src)
    H = homography_dlt(src, dst)
    assert np.abs(apply_homography(H, src) - dst).max() < 1e-6


def test_many_noisy_points_least_squares():
    """잡음이 있으면 '가장 잘 맞는' H. 재투영 오차가 OpenCV(findHomography) 와 비슷해야 한다."""
    rng = np.random.default_rng(2)
    H_true = cv2.getPerspectiveTransform(_random_quad(rng), np.float32([[0, 0], [599, 0], [599, 847], [0, 847]]))
    src = rng.uniform(0, 900, (30, 2))
    dst = apply_homography(H_true, src) + rng.normal(0, 0.5, (30, 2))
    H = homography_dlt(src, dst)
    H_cv, _ = cv2.findHomography(src, dst, 0)
    err = np.linalg.norm(apply_homography(H, src) - dst, axis=1).mean()
    err_cv = np.linalg.norm(apply_homography(H_cv, src) - dst, axis=1).mean()
    assert err < err_cv * 1.2 + 0.05, f"재투영 오차 {err:.3f}px (OpenCV {err_cv:.3f}px)"
