# chap11 PaintCV와 얼굴 검출·성별 분류 학습 노트

- 세션 날짜: 2026-10-27 ~ 2026-11-05
- 설명 방식: Markdown(ASCII 그림, 숫자 표, 손계산) 우선. 숫자는 전부 실제로 돌려서 얻은 값 (Python 3.12.9, NumPy 2.1.2, OpenCV 4.12.0). GUI 동작은 `onMouse`를 직접 호출해 시뮬레이션했고, Haar cascade 내부 값은 OpenCV와 결과가 같은 것을 확인한 파이썬 평가기로 뽑았어요
- 배경지식: `reference/Chapter06` (관련 개념이 나올 때 📚 복습 박스로 짧게 리뷰)
- 🚗 박스: 업무(AVM 서라운드뷰, 탑뷰 LUT, 주차선·주차 칸)와 연결되는 부분

> `README.md`만 직접 쓴 파일이고, 나머지는 세션 기록에서 **추출한 원문**이에요. 이 세션은 제목이 `# Part N.`이 아니라 `# <이모지> Step N.` 형식이라 `study-notes/tools/extract_session.py`의 `fix_links`를 그대로 쓰고 제목 찾는 부분만 바꾼 임시 스크립트로 뽑았어요. 보관하면서 고친 곳은 `14-summary.md` 마지막 줄(보관 안내 문구 → 이 README 링크) 하나예요. 각 파일 끝의 "확인 퀴즈"는 같은 파일 안에 정답이 있어요.

## 핵심 한 문장

> **얼굴을 찾고(Haar cascade), 눈으로 기울기를 바로잡고(회전 행렬), 얼굴 크기에 비례한 영역의 색 히스토그램을 비교해서(마스크 + CORREL) 손으로 정한 기준값으로 판단한다. 각 단계는 단순하지만, `dst` 위치 인자·제자리 수정·배열 모양 해석 때문에 에러 없이 틀린 답이 나오는 곳이 여럿 있다.**

## 목차

| 파일 | 내용 | 다룬 코드 |
|---|---|---|
| [14-summary.md](14-summary.md) | **총정리**: 한 장 지도, 반복된 함정 5가지, 코드 이슈 전체 표, 숫자 치트시트, AVM 연결, 종합 퀴즈 (복습은 여기부터) | 전체 |
| [00-plan.md](00-plan.md) | 학습 계획 | — |
| **Part A. PaintCV** | | |
| [01-paintcv-icons-menu.md](01-paintcv-icons-menu.md) | 아이콘 메뉴 배치, ROI (x,y,w,h) ↔ numpy [y:y+h, x:x+w] | 01, 02 |
| [02-hue-palette.md](02-hue-palette.md) | HSV 색상 바·팔레트, OpenCV H 0~179, dtype 함정 | 03, paint_utils |
| [03-mouse-menu-click.md](03-mouse-menu-click.md) | 마우스 콜백, hit-test(반열린 구간), 클릭 픽셀 → 색, `global` | 03, 04 |
| [04-state-machine-drawing.md](04-state-machine-drawing.md) | `mouse_mode` 상태 기계, 고무줄 미리보기, 도형 수학 | 04 |
| [05-paintcv-complete.md](05-paintcv-complete.md) | 캔버스 view, 포화 연산 vs numpy 랩어라운드, 트랙바, OPEN/SAVE/CLEAR | 05 |
| [06-part-a-summary.md](06-part-a-summary.md) | Part A 정리와 버그 3개(메뉴→캔버스 그리기, 두께 0, 팔레트 252) | 01~05 |
| **Part B. 얼굴 → 성별** | | |
| [07-preprocessing-equalize.md](07-preprocessing-equalize.md) | Part B 개요, 흑백 가중치, 평활화(CDF·LUT), CLAHE, `%2d` 버그 | 06, haar_utils |
| [08a-haar-features-integral.md](08a-haar-features-integral.md) | Haar-like 특징, 적분 영상 D−B−C+A, 분산 정규화 | XML |
| [08b-adaboost-cascade.md](08b-adaboost-cascade.md) | 나무 약분류기, Gentle AdaBoost, 20단계 cascade | XML |
| [08c-pyramid-minneighbors.md](08c-pyramid-minneighbors.md) | 피라미드, 슬라이딩 윈도우, groupRectangles, minNeighbors, scaleFactor | 06 |
| [09-eye-detection-coords.md](09-eye-detection-coords.md) | 얼굴 안 눈 검출(60장 비교), 부분 좌표 + offset, `faces.any()` 함정 | 06 |
| [10-tilt-correction.md](10-tilt-correction.md) | atan2/fastAtan2, 회전 행렬 유도, 역방향 매핑·쌍선형 보간, INTER_CUBIC이 dst로 가는 버그, `cv2.transform` shape | 07, haar_utils |
| [11-hair-lip-roi.md](11-hair-lip-roi.md) | 비율 ROI 4개, `np.ravel` 트릭, 입술 0.3h 검증(Cr), 사진 밖 ROI → 유사도 1.0 | 07, haar_utils |
| [12-masks-3d-histogram.md](12-masks-3d-histogram.md) | 타원 마스크(제자리 수정에 기댐), 64³ 히스토그램, CORREL 손계산, 64채널 해석으로 N = 4,096 | 08, haar_histogram |
| [13-gender-classify.md](13-gender-classify.md) | 판단 나무, `waitKeyEx` 키 코드, 09 루프 00번 건너뜀, 60장 결과 58/60, 과대평가와 한계 | 09, haar_classify |

## 세션에서 발견한 코드 이슈 (수정하지 않음)

전체 표와 수정안은 [14-summary.md](14-summary.md)의 C-3에 있어요. 특히 조용히 틀린 답을 내는 것:

| 위치 | 내용 | 설명 위치 |
|---|---|---|
| [haar_utils.py:20](../../chap11/header/haar_utils.py#L20) | `cv2.INTER_CUBIC`이 `dst` 자리 → 실제로는 LINEAR | Step 10 |
| [haar_utils.py:28-50](../../chap11/header/haar_utils.py#L28-L50) | 박스가 사진 밖이면 빈 ROI → NaN → 유사도 1.0 | Step 11 |
| [haar_histogram.py:11-15](../../chap11/header/haar_histogram.py#L11-L15) | 마스크가 `draw_ellipse`의 제자리 수정에 기댐 | Step 12 |
| [haar_histogram.py:32-33](../../chap11/header/haar_histogram.py#L32-L33) | (64,64,64) 히스토그램 CORREL이 N = 4,096으로 계산됨 | Step 12 |
| [06~09](../../chap11/09.gender_classifier.py#L20) | `faces.any()` → 얼굴이 없으면 AttributeError | Step 9 |

## 남은 할 일

- [ ] [.vscode/launch.json](../../.vscode/launch.json) PYTHONPATH에 `chap11/header` 추가할지 결정 (지금은 chap11 파일을 F5로 실행하면 import 실패)
- [ ] Step 13 실험: 칸 수·색 공간(H-S, Cr-Cb)을 바꾸고 기준값을 다시 맞춰서 39번(그림자)이 맞는지 보기
- [ ] 60장을 기준값 정하는 용도와 채점 용도로 나눠서(중복 3쌍 제거) 실제 정확도 재기
- [ ] (선택) HTML 인터랙티브 시각화: 상태 기계 미니 그림판(4), 적분 영상 특징 드래그(8-A), 게이트 통과 애니메이션(8-B), 회전 행렬 슬라이더(10), ROI 비율 박스(11), 64³ 서랍장(12), 기준선 드래그 산점도(13)
