"""문서 스캐너 모듈.

    detect.py      Step 2  find_document_quad   종이(사각형) 찾기             ← 직접 구현
    corners.py     Step 3  order_corners        꼭짓점 순서 정렬              ← 직접 구현
                           quad_size            출력 크기 정하기              ← 직접 구현
    homography.py  Step 4  homography_dlt       호모그래피 행렬 풀기          ← 직접 구현
    warp.py        Step 5  warp_perspective     역매핑 + 양선형 보간          ← 직접 구현
    enhance.py     Step 6  adaptive_threshold   적응형 이진화                 ← 직접 구현
    ui.py                  pick_corners         마우스로 꼭짓점 찍기 (제공)
    evaluate.py            corner_error 등      정답과 비교 (제공)

구현 순서와 설명은 GUIDE.md.  채점: python tools/run_tests.py p1_doc_scanner (projects 폴더에서)
"""
