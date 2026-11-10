"""카메라 모델과 LUT·발자국 검증.  실행: python tools/run_tests.py lab_topview_moire"""
import numpy as np

from moire.camera import FisheyeCamera
from moire.lut import footprint, make_topview

CAM = FisheyeCamera(1280, 960, 190, 0.95, 60)


def test_ground_image_round_trip():
    X, Y = np.meshgrid(np.linspace(-3, 3, 13), np.linspace(0.2, 6, 13))
    u, v, ok = CAM.ground_to_image(X, Y)
    assert ok.all(), "기본 톱뷰 범위는 전부 시야 안이어야 한다"
    X2, Y2, ok2 = CAM.image_to_ground(u, v)
    assert ok2.all()
    assert np.abs(X2 - X).max() < 1e-6 and np.abs(Y2 - Y).max() < 1e-6, "지면 → 영상 → 지면 은 제자리로 돌아와야 한다"


def test_optical_axis_hits_image_center():
    y_axis = CAM.height_m / np.tan(np.deg2rad(CAM.pitch_deg))      # 광축이 지면에 닿는 곳
    u, v, _ = CAM.ground_to_image(np.array(0.0), np.array(y_axis))
    assert np.allclose([u, v], CAM.center, atol=1e-6)


def test_near_ground_is_lower_in_image():
    _, v_near, _ = CAM.ground_to_image(np.array(0.0), np.array(0.5))
    _, v_far, _ = CAM.ground_to_image(np.array(0.0), np.array(5.0))
    assert v_near > v_far, "가까운 바닥은 영상 아래쪽(v 가 큼), 먼 바닥은 위쪽에 맺혀야 한다"


def _grid_lut(J, h=40, w=50):
    """출력 (x, y) → 원본 J @ (x, y) 인 아핀 LUT."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return (J[0, 0] * x + J[0, 1] * y).astype(np.float32), (J[1, 0] * x + J[1, 1] * y).astype(np.float32)


def test_footprint_uniform_scale():
    fp = footprint(*_grid_lut(np.array([[4.0, 0], [0, 4.0]])))
    for name in ("rho", "s_max", "s_min"):
        assert np.allclose(getattr(fp, name), 4), f"4배 균일 축소면 {name} = 4"


def test_footprint_rotated_anisotropic():
    t = np.deg2rad(30)
    R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    J = R @ np.diag([3.0, 1.0])
    fp = footprint(*_grid_lut(J))
    assert np.allclose(fp.s_max, 3) and np.allclose(fp.s_min, 1), "특이값은 회전과 무관하다"
    assert np.allclose(np.linalg.norm(fp.major, axis=-1), 3), "긴 축 벡터의 길이 = s_max"
    assert np.allclose(np.abs(fp.major[0, 0] / 3), np.abs(R[:, 0])), "긴 축 방향 = J 가 가장 늘리는 방향"
    assert np.allclose(fp.rho, 3), "ρ = J 의 열 길이 중 큰 값 (여기선 1열 = 3)"


def test_topview_grid_and_crop():
    tv = make_topview(CAM, 0.01, (-3.0, 3.0), (0.2, 6.2))
    assert tv.shape == (600, 600)
    assert np.isclose(tv.Y[0, 0], 6.195) and np.isclose(tv.Y[-1, 0], 0.205), "위 행 = 먼 곳, 화소 중심 좌표"
    rows, cols = tv.rows_cols((-1.0, 2.0, 0.2, 1.4))
    assert (rows.stop - rows.start, cols.stop - cols.start) == (120, 300)
    assert np.isclose(tv.X[rows, cols].min(), -0.995) and np.isclose(tv.Y[rows, cols].min(), 0.205)
