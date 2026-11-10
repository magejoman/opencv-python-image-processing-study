"""이 프로젝트의 테스트.  실행: python tools/run_tests.py {{NAME}}

직접 구현한 함수는 여기서 OpenCV 결과나 손으로 계산한 값과 비교해 둔다.
나중에 코드를 고쳤을 때 예전 결과가 깨지지 않았는지(회귀) 바로 알 수 있다.
"""
import numpy as np

from main import pipeline


def test_pipeline_runs_on_synthetic_image():
    img = np.zeros((120, 160, 3), np.uint8)
    img[30:90, 40:120] = 255                              # 흰 사각형 하나
    stages, metrics = pipeline(img, blur_ksize=5, canny_low=50, canny_high=150)
    assert len(stages) >= 2
    assert 0 < metrics["edge_ratio"] < 0.2, "사각형 테두리만 엣지여야 한다"
