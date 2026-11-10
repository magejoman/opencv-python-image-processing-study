"""cvkit 자체 테스트.  실행: python tools/run_tests.py   (pytest 가 있으면 pytest tests 도 된다)

창을 띄우는 기능(show, tune)은 자동 테스트에서 제외하고, 계산 부분만 검사한다.
"""
import tempfile
from pathlib import Path

import cv2
import numpy as np

from cvkit import (Config, Param, Project, Stages, Table, benchmark, check_image, compare, describe,
                   diff_heatmap, imread, imwrite, list_images, load_config, mosaic, put_label,
                   save_config, speed_table, to_display)


def _raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError(f"{exc_type.__name__} 가 발생해야 합니다")


# ---------------------------------------------------------------- io
def test_imread_imwrite_korean_path():
    img = np.random.default_rng(0).integers(0, 256, (40, 60, 3), np.uint8)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "한글 폴더" / "테스트 이미지.png"
        imwrite(path, img)
        back = imread(path)
        assert np.array_equal(back, img), "PNG 는 무손실이므로 완전히 같아야 한다"
        assert list_images(path.parent) == [path]


def test_imread_errors_and_max_side():
    _raises(FileNotFoundError, imread, "없는_파일.jpg")
    img = np.zeros((300, 400, 3), np.uint8)
    with tempfile.TemporaryDirectory() as d:
        p = imwrite(Path(d) / "a.jpg", img)
        assert imread(p, max_side=100).shape == (75, 100, 3)
        assert imread(p, max_side=1000).shape == (300, 400, 3), "작은 이미지는 키우지 않는다"
        (Path(d) / "broken.jpg").write_bytes(b"not an image")
        _raises(ValueError, imread, Path(d) / "broken.jpg")


# ---------------------------------------------------------------- check
def test_check_image():
    _raises(TypeError, check_image, None)
    _raises(TypeError, check_image, np.zeros((4, 4), np.float32), dtype=np.uint8)
    _raises(ValueError, check_image, np.zeros((4, 4), np.uint8), channels=3)
    _raises(ValueError, check_image, np.zeros((0, 4), np.uint8))
    img = np.zeros((4, 5, 3), np.uint8)
    assert check_image(img, dtype=np.uint8, channels=3) is img
    assert "H=4, W=5, C=3" in describe(img, verbose=False)


# ---------------------------------------------------------------- viz
def test_to_display_conversions():
    assert to_display(np.array([[True, False]]))[0, 0].tolist() == [255, 255, 255]
    assert to_display(np.array([[0.0, 1.0]], np.float32))[0, 1, 0] == 255           # [0,1] → ×255
    assert to_display(np.array([[0.0, 200.0]], np.float32))[0, 1, 0] == 200         # [0,255] → 그대로
    sobel = to_display(np.array([[-100, 0, 100]], np.int16))                         # 음수 → min-max
    assert sobel[0, :, 0].tolist() == [0, 128, 255]
    assert to_display(np.zeros((3, 3, 4), np.uint8)).shape == (3, 3, 3)


def test_put_label_and_mosaic():
    img = np.full((100, 200, 3), 128, np.uint8)
    for text in ("edge", "엣지 결과"):
        out = put_label(img, text)
        assert out.shape == img.shape and not np.array_equal(out, img)
    assert np.all(img == 128), "원본을 건드리면 안 된다"

    st = Stages()
    gray = st.add("그레이", np.zeros((50, 80), np.uint8))
    assert gray.shape == (50, 80) and st["그레이"] is gray
    st.add("마스크", np.ones((50, 80), bool))
    st.add("작은 행렬", np.eye(4, dtype=np.float32))
    m = mosaic(st, cell_height=100)
    assert m.dtype == np.uint8 and m.shape[0] == 100 + 2 * 4, "3장 이하는 한 줄"
    assert mosaic([("a", gray)] * 4, cell_height=100).shape[0] == 2 * 100 + 3 * 4, "4장은 2×2"


# ---------------------------------------------------------------- compare
def test_compare():
    a = np.full((10, 10), 100, np.uint8)
    same = compare(a, a.copy(), verbose=False)
    assert same.ok and same.max_abs == 0 and np.isinf(same.psnr)

    b = a.copy()
    b[0, 0] = 103
    r = compare(b, a, tol=1, verbose=False)
    assert not r.ok and r.max_abs == 3 and r.n_diff == 1, "uint8 뺄셈 overflow 없이 3 이어야 한다"
    assert diff_heatmap(b, a).shape == (10, 10, 3)
    _raises(ValueError, compare, np.zeros((3, 4)), np.zeros((4, 3)), verbose=False)


# ---------------------------------------------------------------- config / project
def test_config_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        path = save_config({"params": {"canny_low": 50, "이름": "테스트"}, "tune": {"canny_low": [0, 255, 1]}},
                           Path(d) / "config.yaml")
        cfg = load_config(path)
        assert cfg.params.canny_low == 50 and cfg.params["이름"] == "테스트"
        assert isinstance(cfg, Config)
        _raises(AttributeError, lambda: cfg.없는키)

        (Path(d) / "src").mkdir()
        proj = Project(Path(d) / "src" / "tool.py")
        assert proj.root == Path(d).resolve(), "config.yaml 이 있는 상위 폴더가 루트"
        assert proj.config.params.canny_low == 50
        assert proj.result_path("sub", "x.png").parent.is_dir()


# ---------------------------------------------------------------- report / timing
def test_table():
    t = Table()
    t.add(file="a.jpg", success=True, err=1.23456)
    t.add(file="b.jpg", success=False, reason="그림자")
    md = t.to_markdown()
    assert md.splitlines()[0] == "| file | success | err | reason |"
    assert "| a.jpg | O | 1.235 |  |" in md
    assert t.mean("success") == 0.5
    with tempfile.TemporaryDirectory() as d:
        text = t.save_csv(Path(d) / "s.csv").read_text(encoding="utf-8-sig")
        assert "그림자" in text


def test_benchmark():
    r1 = benchmark(sum, range(10), repeat=3, warmup=1, name="fast", verbose=False)
    r2 = benchmark(sum, range(10000), repeat=3, warmup=1, name="slow", verbose=False)
    table = speed_table(r2, r1)
    assert table.rows[0]["name"] == "fast" and table.rows[0]["x_slower"] == 1.0


# ---------------------------------------------------------------- tuner (GUI 제외)
def test_param_mapping():
    k = Param("blur_ksize", 5, 1, 31, 2)
    assert k.count == 15 and k.to_pos(5) == 2 and k.to_value(2) == 5 and isinstance(k.to_value(2), int)
    assert all(k.to_value(p) % 2 == 1 for p in range(k.count + 1)), "lo=1, step=2 → 항상 홀수"
    s = Param("sigma", 1.5, 0.0, 5.0, 0.1)
    assert s.to_value(s.to_pos(1.5)) == 1.5 and not s.is_int
    ps = Param.from_config({"a": 3, "b": 7}, {"a": [0, 10]})
    assert [p.name for p in ps] == ["a"] and ps[0].step == 1
    _raises(KeyError, Param.from_config, {}, {"a": [0, 10]})
    _raises(ValueError, Param, "bad", 0, 10, 0)


def test_opencv_available():
    """cv2 가 정상 로드되는지 (opencv-python 과 contrib 가 겹쳐 깨진 경우 여기서 걸린다)."""
    assert cv2.GaussianBlur(np.zeros((5, 5), np.uint8), (3, 3), 0).shape == (5, 5)
