# chap07 영역 처리 (Area Processing) 학습 노트

- 세션 날짜: 2026-10-20 ~ 2026-10-28 (세션 `5a0a6846`)
- 설명 방식: Markdown(ASCII 그림, 숫자 표, 손계산) 우선. 숫자는 전부 실제로 돌려서 얻은 값 (NumPy 2.1.2, OpenCV 4.12.0)
- 배경지식: `reference/Chapter06` (관련 개념이 나올 때 📚 복습 박스로 짧게 리뷰)
- 🚗 박스: 업무(AVM 서라운드뷰, 탑뷰, 주차선)와 연결되는 부분

> `README.md`만 직접 쓴 파일이고, `00-plan.md`와 Part 1~8 파일은 세션 기록에서 `study-notes/tools/extract_session.py --concat`으로 **추출한 원문**이에요. 이 챕터는 Part 하나를 여러 답변에 나눠 설명해서, 같은 Part의 답변들을 세션 순서대로 `---`로 이어 붙였어요. 원문에서 바꾼 곳은 링크 경로뿐이고, `06-canny.md` 마지막 줄의 잘못된 파일 이름 링크(`16.morphology.py`)만 실제 파일 `16.close_open.py`로 고쳤어요.

## 핵심 한 문장

> **출력 화소 하나를 정할 때 이웃까지 본다. 가중치를 곱해 더하면 블러·샤프닝·미분(선형 필터), 정렬해서 하나를 고르면 미디언·최소·최대·모폴로지(비선형 필터).**

## 목차

| 파일 | 내용 | 다룬 코드 |
|---|---|---|
| [00-plan.md](00-plan.md) | 학습 계획 (Part 1~8) | — |
| [01-convolution-blur-sharpen.md](01-convolution-blur-sharpen.md) | 회선 손계산, 블러링 코드 해부, 샤프닝 (답변 3개) | 01, 02 |
| [02-first-derivative-edges.md](02-first-derivative-edges.md) | 에지와 차분, 그래디언트, 로버츠 → 프리윗 → 소벨 (답변 2개) | 03, 04, 05 |
| [03-laplacian.md](03-laplacian.md) | 2차 미분, 영교차, 라플라시안 마스크 유도 | 06 |
| [04-noise-filters.md](04-noise-filters.md) | 잡음 종류, 평균, 가우시안, 미디언, 최소/최대 (답변 3개) | 10, 12, 11, 09 |
| [05-log-dog.md](05-log-dog.md) | LoG, DoG, 자료형 함정 | 07 |
| [06-canny.md](06-canny.md) | 캐니 6-1 ~ 6-8: 블러, 크기·방향, NMS, 이력 임계값, `cv2.Canny` 비교, 컬러 캐니 (답변 5개) | 08, 13 |
| [07-morphology.md](07-morphology.md) | 구조 요소, 침식, 팽창, 열림, 닫힘 (답변 2개) | 14, 15, 16 |
| [08-plate-detection.md](08-plate-detection.md) | 번호판 후보 검출 + **chap07 전체 정리**(Part별 요약, 위치 인자 함정 최종표) | 17 |

복습은 `08-plate-detection.md` 끝의 "🏁 chap07 전체 정리"부터 보면 빨라요. Part 1 ~ 5는 [summary-part1-5.md](summary-part1-5.md)에 핵심만 따로 압축해 뒀어요(세션 `26174fd7`의 다시 보기 기준, 셀프 체크 포함).

## 노트에 나온 코드 함정 (저장소 파일은 수정하지 않음)

| Part | 함정 | 노트 위치 |
|---|---|---|
| 1 | 01번: "blur2" 창에 `blur1` 표시, 44·45줄 주석이 뒤바뀜 | 01 · 1-3-g |
| 1 | `convertScaleAbs`의 절댓값이 샤프닝 음수를 밝게 뒤집음 | 01 · 1-4-f |
| 2 | "수직 마스크" = x방향 미분이라는 이름 함정 / `cv2.Sobel` 위치 인자 | 02 · 2-4, 2-5-d |
| 3 | `cv2.Laplacian` 위치 인자 (Part 2와 같은 문제) | 03 · Step 3-3 |
| 4 | 10번: 창 이름과 표시 영상 불일치 / 12번: 18×6 마스크, `GaussianBlur`의 sigmaY가 dst 자리에 들어감 | 04 · 4-2, 4-3-f |
| 5 | `astype('uint8')` 순환, uint8 뺄셈 순환, `Laplacian`의 9가 dst 자리 | 05 · Step 5-3 |
| 6 | σ=0.3 블러, 방향 버림(22.5°), 엄격한 부등호 NMS, 재귀 깊이 한계, 전역 변수, `Canny`의 5가 edges 자리 | 06 · 6-3-b, 6-4-d, 6-5-e, 6-6-e, 6-6-f, 6-8-d |
| 7 | 255가 홀수라서 동작하는 `bitwise_and`, 직접 구현한 팽창의 테두리 | 07 · 7-2-d, 7-3-c |
| 8 | `Sobel`의 5가 dst 자리, `CV_8U`가 음수 기울기를 0으로 자름 | 08 · 8-4-a, 8-4-b |

## 남은 할 일

- [ ] 세션 `26174fd7`에서 Part 1 ~ Part 6 Step 6-4 다시 공부하기 (compact 때문에 앞부분을 못 읽었음)
- [ ] 각 Part 끝 확인 질문 다시 풀기 (정답은 다음 답변 앞부분)
- [ ] (선택) HTML 인터랙티브 시각화: 마스크 슬라이딩, 그래디언트 화살표, NMS, 이력 임계값 추적
