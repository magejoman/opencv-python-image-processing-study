"""Step 6 채점: adaptive_threshold"""
import cv2
import numpy as np

from scanner.enhance import adaptive_threshold


def _document_with_shadow(h=200, w=300, return_paper_mask=False):
    img = np.full((h, w), 220, np.uint8)
    for y in range(30, h - 20, 22):
        cv2.putText(img, "lorem ipsum dolor", (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 40, 1, cv2.LINE_AA)
    paper = cv2.erode((img == 220).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0   # 글자에서 조금 떨어진 종이
    shade = np.linspace(1.0, 0.35, w)[None, :]                     # 오른쪽으로 갈수록 어두워지는 그림자
    out = (img * shade).astype(np.uint8)
    return (out, paper) if return_paper_mask else out


def test_output_is_binary_uint8():
    out = adaptive_threshold(_document_with_shadow(), 31, 10)
    assert out.dtype == np.uint8 and out.shape == (200, 300)
    assert set(np.unique(out)) <= {0, 255}


def test_matches_opencv():
    gray = _document_with_shadow()
    for block, C in [(31, 10), (15, 5), (51, 15)]:
        mine = adaptive_threshold(gray, block, C)
        ref = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block, C)
        diff_ratio = (mine != ref).mean()
        # 평균을 정수로 반올림하느냐에 따라 경계 픽셀 몇 개가 다를 수 있다 (GUIDE.md §6.4)
        assert diff_ratio < 0.005, f"block={block}, C={C}: {diff_ratio:.2%} 픽셀이 다릅니다"


def test_beats_global_threshold_under_shadow():
    """그림자가 있어도 글자 아닌 종이 부분은 대부분 흰색이어야 한다 (전역 임계값은 실패하는 상황)."""
    gray, paper = _document_with_shadow(return_paper_mask=True)
    _, global_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    out = adaptive_threshold(gray, 31, 10)
    right = np.s_[:, 230:]                                                  # 가장 어두운 오른쪽
    assert (global_bin[right][paper[right]] == 255).mean() < 0.5, "(전제) 전역 Otsu 는 여기서 실패해야 한다"
    assert (out[right][paper[right]] == 255).mean() > 0.9, "어두운 오른쪽에서도 종이는 흰색이어야 한다"
