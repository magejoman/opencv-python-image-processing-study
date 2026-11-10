"""리샘플링 방법과 지표 검증.  실행: python tools/run_tests.py lab_topview_moire"""
import cv2
import numpy as np

from moire import scene
from moire.camera import FisheyeCamera
from moire.lut import footprint
from moire.methods import anisotropic, pyramid_sample, remap_bilinear, supersample
from moire.metrics import align_frames, contrast_kept, flat_mask, flicker, moire_rms


def _src(h=64, w=80):
    rng = np.random.default_rng(0)
    return cv2.GaussianBlur(rng.random((h, w), dtype=np.float32), (0, 0), 1.5)


def _scaled_lut(scale, h, w):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x * scale, y * scale


def test_identity_lut_is_exact():
    src = _src()
    mx, my = _scaled_lut(1.0, *src.shape)
    assert np.array_equal(remap_bilinear(src, mx, my), src)


def test_pyramid_level_coordinates():
    """LUT 가 정확히 2배 축소이고 lod = 1 이면 결과는 pyrDown 과 같아야 한다.
    (레벨 k 에서 LUT 좌표를 2^k 로 나누는 관례가 맞는지 확인 — 0.5 화소 어긋나면 여기서 걸린다)"""
    src = _src()
    mx, my = _scaled_lut(2.0, 32, 40)
    out = pyramid_sample(src, mx, my, np.ones((32, 40), np.float32), levels=3)
    assert np.allclose(out, cv2.pyrDown(src), atol=1e-5)


def test_trilinear_at_lod0_equals_bilinear():
    src = _src()
    mx, my = _scaled_lut(0.7, 50, 60)
    out = pyramid_sample(src, mx, my, np.zeros((50, 60), np.float32), levels=3)
    assert np.allclose(out, remap_bilinear(src, mx, my), atol=1e-6)


def test_anisotropic_reduces_to_trilinear_when_isotropic():
    src = _src()
    mx, my = _scaled_lut(2.0, 32, 40)
    fp = footprint(mx, my)                                  # 원 모양 발자국 (s_max = s_min = 2) → 탭 1개
    out = anisotropic(src, mx, my, fp, levels=3, max_probes=8)
    assert np.allclose(out, cv2.pyrDown(src), atol=1e-5)


def test_supersample_output_shape():
    src = _src()
    mx, my = _scaled_lut(0.5, 40, 60)                       # 2배 해상도 LUT
    assert supersample(src, mx, my, 2).shape == (20, 30)


def test_truth_has_no_fine_pattern():
    """정답 톱뷰에서는 미세 무늬(톱뷰로 표현 불가)가 고른 회색으로 사라져야 한다."""
    X, Y = np.meshgrid(np.arange(0.6, 1.6, 0.01) + 0.005, np.arange(0.5, 1.1, 0.01) + 0.005)   # 그레이팅 영역
    full = scene.render_truth(X, Y, 0.01)
    clean = scene.render_truth(X, Y, 0.01, fine=0.0)
    assert moire_rms(full, clean, np.ones_like(full, bool)) < 0.5


def test_render_fisheye_shapes_and_range():
    cam = FisheyeCamera(64, 48, 190, 0.95, 60)
    frames = scene.render_fisheye(cam, [(0.0, 1.0), (0.01, 1.0), (0.0, 0.0)], ss=2)
    assert len(frames) == 3 and all(f.shape == (48, 64) and f.dtype == np.float32 for f in frames)
    assert all(0 <= f.min() and f.max() <= 1 for f in frames)


def test_align_frames_and_flicker():
    rng = np.random.default_rng(1)
    world = rng.random((20, 60)).astype(np.float32)
    shift, W = 2, 40
    frames = [world[:, k * shift: k * shift + W] for k in range(5)]   # 프레임 k 의 열 c = 바닥 열 c + k·shift
    aligned, cols = align_frames(frames, shift)
    assert all(np.array_equal(a, aligned[0]) for a in aligned), "움직임을 보정하면 모든 프레임이 같아야 한다"
    assert cols == slice(8, 40)
    assert flicker(frames, shift, np.ones((20, W), bool)) < 1e-3       # float32 평균의 반올림 오차만 남는다


def test_simple_metrics():
    a = _src()
    assert moire_rms(a, a, np.ones_like(a, bool)) == 0
    assert np.isclose(contrast_kept(2 * a, a, np.ones_like(a, bool)), 200)
    step = np.zeros((20, 40), np.float32)
    step[:, 20:] = 1
    m = flat_mask(step, margin_px=3)
    assert not m[:, 16:24].any() and m[:, :15].all() and m[:, 25:].all(), "경계 ±3 화소는 '평평하지 않음'"
