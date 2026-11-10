# chap06 화소 처리 (Point Processing) 학습 노트

- 세션 날짜: 2026-10-19 ~ 2026-10-20
- 설명 방식: Markdown(ASCII 그림, 숫자 표, 손계산) 우선. 어려운 부분은 HTML 시각화로 보충 예정
- 배경지식: `reference/Chapter06` (오래전에 배워서 관련 개념이 나올 때 📚 복습 박스로 짧게 리뷰)

> `summary.md`는 직접 정리한 파일이고(추출 스크립트가 건드리지 않아요), Part 1~7 파일은 세션 기록에서 `study-notes/tools/extract_session.py`로 **추출한 원문**이에요. 각 파일 끝의 "확인 질문"은 다음 Part 앞부분에 정답이 있어요.

## 핵심 한 문장

> **모든 연산은 화소 하나의 값 `x`를 받아 새 값 `y`를 돌려주는 함수 `y = f(x)`를 어떻게 설계하느냐**

## 목차

| 파일 | 내용 | 다룬 코드 |
|---|---|---|
| [summary.md](summary.md) | **핵심 API 사용법, 공식, 함정, 함수 선택 가이드 치트시트** (복습은 여기부터) | 전체 |
| [00-plan.md](00-plan.md) | 학습 계획, 이미 아는 것 / 새로 배울 것 | — |
| [01-pixel-access-lut.md](01-pixel-access-lut.md) | 화소 접근 5가지 방법, 룩업 테이블(LUT), 속도 | 01, 02 |
| [02-pixel-value-quantization.md](02-pixel-value-quantization.md) | 화소값 = 밝기, 그라데이션, 양자화, ROI | 03 (두 개) |
| [03-arithmetic-contrast.md](03-arithmetic-contrast.md) | 포화 vs 모듈로, 영상 합성, 명암 대비 `y = a·x + b` | 04, 05, 06 |
| [04-histogram.md](04-histogram.md) | 히스토그램 계산/그리기, Hue 히스토그램 | 07, 08, 09, 10 |
| [05-stretching-equalization.md](05-stretching-equalization.md) | 히스토그램 스트레칭, 평활화(CDF) | 11, 12 |
| [06-color-spaces.md](06-color-spaces.md) | CMY(K), HSI/HSV, YCrCb, YUV, Lab | 13, 14, 15, 16 |
| [07-thresholding.md](07-thresholding.md) | threshold 5가지, 트랙바, 오츠, Hue 범위 이진화 | 17, 18 |
| [appendix-yuv422-rgba.md](appendix-yuv422-rgba.md) | **업무용 보충**: YUV422 메모리 배치(YUYV/UYVY), 스트라이드, 풀/리미티드 레인지, RGBA 알파 합성(straight vs premultiplied), 디버깅 체크리스트 | — |
| [appendix-vscode-debug.md](appendix-vscode-debug.md) | 디버거에서 "영상 파일 읽기 오류"가 날 때 | — |

## 세션에서 발견한 코드 이슈 (수정하지 않음)

| 위치 | 내용 | 설명 위치 |
|---|---|---|
| `02.image_access.py` `pixel_access2` | NumPy 2.0에서 `itemset()` 삭제 → 호출부 주석 처리됨 | Part 1 |
| `06.contrast.py` dst4 | `-avg`(= −m/2)라서 받침점이 평균이 아님. 엄밀히는 `-m` | Part 3 |
| `Common/histogram.py` `draw_histo` | `enumerate(hist)` → `int(배열)` DeprecationWarning (`.flat` 권장) | Part 4 |
| `12.histogram_equalize.py` | 리스트 컴프리헨션 결과는 바로 덮어써지는 죽은 코드 / 27줄 주석은 `표[이미지]` 순서가 반대 | Part 5 |
| `13.convert_cmy.py` | `Cyan, Magenta, Yellow = cv2.split(...)` 변수명이 뒤바뀜 (실제 순서 Y, M, C) | Part 6 |
| `15.convert_hsv.py` | 창 이름 `OpenCV_Intensity`에는 실제로 V(최댓값)가 표시됨 | Part 6 |
| `17.hue_threshold.py` | threshold 방식은 (하한, 상한], 주석의 for문은 [하한, 상한) → 경계 화소 1,020개 차이 | Part 7 |

## 남은 할 일

- [ ] Part 7 확인 질문 풀기
- [ ] Part 8: 전체 치트시트, 함수 시그니처 요약표, 자가 점검 문제
- [ ] (선택) HTML 인터랙티브 시각화: 대비 시소(Part 3), 평활화(Part 5), RGB 큐브(Part 6), 임계값 슬라이더(Part 7)
