# chap12 응용 사례: 동전 세기 & 자동차 번호판 읽기 학습 노트

- 세션 날짜: 2026-10-20 ~ 2026-10-27
- 설명 방식: Markdown(ASCII 그림, 숫자 표, 손계산) 우선. 숫자는 전부 실제로 돌려서 얻은 값 (NumPy 2.1.2, OpenCV 4.12.0)
- 배경지식: `reference/Chapter06` (관련 개념이 나올 때 📚 복습 박스로 짧게 리뷰)
- 🚗 박스: 업무(AVM 서라운드뷰, 탑뷰, 어안)와 연결되는 부분

> `README.md`만 직접 쓴 파일이고, `00-plan.md`와 L0~L11 파일은 세션 기록에서 `study-notes/tools/extract_session.py`로 **추출한 원문**이에요. L0~L3은 제목이 `# 📘 LN.`, L4부터는 `# Part N.` 형식이에요. 각 파일 끝의 "확인 문제"는 다음 레슨 앞부분에 정답이 있어요. 총정리 치트시트 역할은 **L11**이 해요.

## 핵심 한 문장

> **규칙(이진화, 윤곽선, 모폴로지)으로 후보를 좁히고, 특징(색 히스토그램, 픽셀)으로 판정한다. 그리고 모든 중간값을 숫자로 찍어 보면 버그가 보인다.**

## 목차

| 파일 | 내용 | 다룬 코드 |
|---|---|---|
| [11-wrap-up-limits-deep-learning.md](11-wrap-up-limits-deep-learning.md) | **총정리**: 두 프로젝트 지도, 수정별 성적표, 한계(확률 곱), 딥러닝 비교, 실험 목록, AVM 교훈 (복습은 여기부터) | 전체 |
| [00-plan.md](00-plan.md) | 학습 계획 (L0~L11) | — |
| [00-tour-orientation.md](00-tour-orientation.md) | 전체 지도, 실행 결과, import 구조 | 01~08 |
| [01-coin-preprocess-otsu-morphology.md](01-coin-preprocess-otsu-morphology.md) | 블러, Otsu(130은 무시, 실제 105), 열림 연산 | 01, `coin_preprocess` |
| [02-coin-contours-circle-mask.md](02-coin-contours-circle-mask.md) | `findContours`, 최소 외접원, `getRectSubPix`, 원형 마스크 | 01, 02 |
| [03-hue-histogram-grouping.md](03-hue-histogram-grouping.md) | HSV 색상 히스토그램 32칸, 가중치 점수로 그룹 나누기 | 02, `coin_utils` |
| [04-coin-classify-total.md](04-coin-classify-total.md) | 2×70 표로 동전 종류 결정, 금액 계산 (프로젝트 A 완성) | 03 |
| [05-plate-candidates-sobel-close.md](05-plate-candidates-sobel-close.md) | Sobel, 닫힘 5×13 ×3, `minAreaRect`, 넓이·종횡비 검사 | 05, `plate_preprocess` |
| [06-floodfill-rotate-flip-bug.md](06-floodfill-rotate-flip-bug.md) | `floodFill` 플래그, 회전 행렬, **180° 뒤집힘 버그** 증명과 수정 | 06, `plate_candidate` |
| [07-ml-basics-svm.md](07-ml-basics-svm.md) | 머신러닝 기초, SVM 원리(여백, C, 커널), `SVMtrain.xml` 열어보기 | — |
| [08-svm-train-classify-retrain.md](08-svm-train-classify-retrain.md) | SVM 학습·판별 코드, 데이터 증강 재학습, 차 하나씩 빼고 평가 | 04, 07 |
| [09-knn-character-training-data.md](09-knn-character-training-data.md) | k-NN 원리, 글자표 → (200, 1600) 학습 데이터, 투영, `place_middle` | `plate_classify`, `Common/knn` |
| [10-plate-segment-recognize.md](10-plate-segment-recognize.md) | 글자 7개 분리, `np.sort`로 한글 조각 합치기, `argsort`, 오답 해부 | 08, `plate_classify` |

## 성적표 (번호판 15대 × seed 5 = 75번, L11 1-3)

| 버전 | 정답 / 75 |
|---|---|
| 원본 | 21 |
| + 회전 버그 수정 (L6) | 44 |
| + 한글 K = 1 (L10) | 51 |
| + 쪼개진 글자 합치기 `merge_x` (L10) | 52 |

⚠️ K = 1과 `merge_x`는 같은 15대를 보고 골랐기 때문에 낙관적인 숫자예요(데이터 누수).

## 세션에서 발견한 코드 이슈 (수정하지 않음)

| 위치 | 내용 | 설명 위치 |
|---|---|---|
| [coin_preprocess.py:11](../../chap12/header/coin_preprocess.py#L11) | Otsu가 켜져 있어서 기준값 130은 무시됨 (실제 105) | L1 |
| [coin_preprocess.py:31](../../chap12/header/coin_preprocess.py#L31) | `int()` 버림으로 반지름이 작아짐 | L2 |
| [coin_utils.py:22](../../chap12/header/coin_utils.py#L22) | 마스크 없이 히스토그램 → 원 밖 검정 픽셀(약 65%)이 칸 0에 투표 | L3 |
| [coin_utils.py:44-49](../../chap12/header/coin_utils.py#L44-L49) | 표에 없는 반지름 → −1 → `ncoins[-1]`로 500원에 셈 / 반지름 ≥ 70이면 IndexError | L4 |
| [03.calc_coins.py:19](../../chap12/03.calc_coins.py#L19), [26](../../chap12/03.calc_coins.py#L26) | `str`이 내장 함수를 덮어씀 / 원 색이 동전 종류가 아니라 그룹 기준 | L4 |
| [plate_preprocess.py:10](../../chap12/header/plate_preprocess.py#L10) | `Sobel(..., 3)`의 3은 ksize가 아니라 dst 자리 / `CV_8U`라 음수 기울기가 버려짐 | L5 |
| [05.find_plates.py:5](../../chap12/05.find_plates.py#L5) | `raise` 없이 `Exception(...)`만 만들어서 에러가 안 남 | L5 |
| [plate_candidate.py:24](../../chap12/header/plate_candidate.py#L24) | ★ `angle += 90` → OpenCV 4.5+에서 번호판이 180° 뒤집힘 (`-= 90`이 맞음) | L6 |
| [plate_candidate.py:28](../../chap12/header/plate_candidate.py#L28) | `warpAffine`의 위치 인자 `INTER_CUBIC`은 dst 자리 → 실제로는 선형 보간 | L6 |
| [04.train_plate_data.py:3-10](../../chap12/04.train_plate_data.py#L3-L10), [32](../../chap12/04.train_plate_data.py#L32) | 인자 이름 `type`이 내장 함수를 덮어씀 / 선형 커널에 `setGamma`는 효과 없음 / `MAX_ITER`만 켜서 epsilon 무시 | L8 |
| [07.classify_plates.py:13](../../chap12/07.classify_plates.py#L13), [23](../../chap12/07.classify_plates.py#L23) | 저장 이름(`SVMtrain.xml`)과 대소문자 다름 / `resizeWindow` 효과 없음 / 후보 0개면 reshape 에러 | L8 |
| [08.classify_number.py:19](../../chap12/08.classify_number.py#L19) | SVM이 번호판이라 한 후보 중 `result[0]`만 사용 | L8 |
| [Common/knn.py:8](../../Common/knn.py#L8), [28](../../Common/knn.py#L28) | 변수 이름 `len`이 내장 함수를 덮어씀 / `part[y0:y1, x0:x1]`이라 끝 한 줄씩 잘림 | L9 |
| [plate_classify.py:11](../../chap12/header/plate_classify.py#L11) | 여백 자르기의 `-1`은 나머지가 홀수일 때만 맞는 땜질 | L9 |
| [plate_classify.py:61-62](../../chap12/header/plate_classify.py#L61-L62) | '바'가 두 번 (글자표 그림의 33행과 36행도 완전히 같음) → 표가 갈라짐 | L9 |
| [plate_classify.py:42](../../chap12/header/plate_classify.py#L42), [47](../../chap12/header/plate_classify.py#L47), [69](../../chap12/header/plate_classify.py#L69) | 한글 구역 `45 < x < 80`과 "한글은 3번째" 가정 / 주석 "y 방향 정렬"은 실제로 열마다 정렬 | L10 |
| [08.classify_number.py:21](../../chap12/08.classify_number.py#L21) | K = 10(짝수) + OpenCV는 동점이면 번호가 작은 라벨을 고름 (거리 무시) | L10 |

## 남은 할 일

- [ ] L11 졸업 문제 3개 풀어 보기 (정답은 L11 맨 아래)
- [ ] (제안, 미적용) [.vscode/launch.json](../../.vscode/launch.json) PYTHONPATH의 `chap06/header`를 `chap11/header`로 되돌리기 (스테이징된 변경)
- [ ] (제안, 미적용) [plate_candidate.py:24](../../chap12/header/plate_candidate.py#L24) `-= 90`, [28](../../chap12/header/plate_candidate.py#L28) `flags=cv2.INTER_CUBIC` 반영
- [ ] (제안, 미적용) 재학습한 SVM을 `SVMtrain_retrained.xml`로 저장
- [ ] L11 PART 4의 측정 안 한 실험: `find_number` +1 수정, 동전 히스토그램 마스크, −1 동전 처리, 3자리 번호판 대응
- [ ] (선택) 어려웠던 레슨을 HTML 시각화로 다시 보기 ("LN 더 쉽게")

실측에 쓴 탐색 스크립트는 세션 임시 폴더에만 있었고 저장소에는 남기지 않았어요.
