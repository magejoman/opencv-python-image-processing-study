"""cvkit — 프로젝트 공용 도구 모음.

알고리즘(호모그래피, RANSAC, Hough …)은 여기 넣지 않는다. 그건 각 프로젝트에서 직접 구현하며 배울 부분이다.
여기에는 모든 프로젝트가 반복해서 쓰는 '잡일'만 모은다.

    io       imread / imwrite (한글 경로 OK), list_images
    check    check_image (dtype·채널 검사), describe (shape/dtype/min/max 출력)
    viz      to_display, put_label, mosaic, show, Stages (중간 결과 기록)
    compare  compare (직접 구현 vs OpenCV 차이), diff_heatmap
    timing   Timer, benchmark, speed_table
    config   load_config / save_config (YAML, 점 표기 접근)
    project  Project (프로젝트 폴더 경로 + 설정)
    report   Table (결과표 → 마크다운 / CSV)
    tuner    Param, tune (트랙바로 파라미터 튜닝)
"""
from .io import imread, imwrite, list_images
from .check import check_image, describe
from .viz import to_display, put_label, mosaic, show, Stages
from .compare import compare, diff_heatmap, CompareResult
from .timing import Timer, benchmark, speed_table, BenchResult
from .config import Config, load_config, save_config
from .project import Project
from .report import Table
from .tuner import Param, tune

__all__ = [
    "imread", "imwrite", "list_images",
    "check_image", "describe",
    "to_display", "put_label", "mosaic", "show", "Stages",
    "compare", "diff_heatmap", "CompareResult",
    "Timer", "benchmark", "speed_table", "BenchResult",
    "Config", "load_config", "save_config",
    "Project",
    "Table",
    "Param", "tune",
]
