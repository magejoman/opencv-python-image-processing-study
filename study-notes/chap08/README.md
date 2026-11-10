# chap08 기하학적 처리 (Geometric Transform) 학습 노트

- 세션 날짜: 2026-10-20 ~ 2026-10-27
- 설명 방식: Markdown(ASCII 그림, 숫자 표, 손계산) 우선. 숫자는 전부 실제로 돌려서 얻은 값 (NumPy 2.1.2, OpenCV 4.12.0)
- 배경지식: `reference/Chapter06` (관련 개념이 나올 때 📚 복습 박스로 짧게 리뷰)
- 🚗 박스: 업무(AVM 서라운드뷰, 탑뷰, 어안, 모아레)와 연결되는 부분

> `README.md`만 직접 쓴 파일이고, `00-plan.md`와 Part 0~11 파일은 세션 기록에서 `study-notes/tools/extract_session.py`로 **추출한 원문**이에요. 각 파일 끝의 "확인 질문"은 다음 Part 앞부분에 정답이 있어요. chap06의 `summary.md` 역할은 **Part 11**이 해요.

## 핵심 한 문장

> **목적 영상의 화소마다 역행렬로 원본 위치를 찾고(원근이면 w로 나누고), 그 소수 좌표의 값을 보간해서 가져온다.**

## 목차

| 파일 | 내용 | 다룬 코드 |
|---|---|---|
| [11-summary.md](11-summary.md) | **총정리**: 변환 계층도, 함수 대응표, 보간법 비교(모아레), 버그 목록, 연습문제, AVM 로드맵, 치트시트 (복습은 여기부터) | 전체 |
| [00-plan.md](00-plan.md) | 학습 계획 (Part 0~11) | — |
| [00-setup-coordinates.md](00-setup-coordinates.md) | 좌표계 `(x, y)` ↔ `img[y, x]`, `shape` vs `size`, 큰 그림 | — |
| [01-forward-mapping-scaling.md](01-forward-mapping-scaling.md) | 순방향 사상, 구멍과 겹침 | 01 |
| [02-backward-mapping-nearest.md](02-backward-mapping-nearest.md) | 역방향 사상, 최근접 이웃 보간 | 02 |
| [03-bilinear-interpolation.md](03-bilinear-interpolation.md) | 양선형 보간, 반화소 정렬, 보간 모드 | 03 |
| [04-translation.md](04-translation.md) | 평행 이동, 범위 검사, 음수 인덱스 함정 | 04 |
| [05-rotation.md](05-rotation.md) | 회전 공식 유도, 중심 회전, 회전 방향, `fastAtan2` | 05, 06 |
| [06-homogeneous-affine.md](06-homogeneous-affine.md) | 동차 좌표, 어파인 `[A\|t]`, `getAffineTransform`, 역행렬 | 07 |
| [07-transform-composition.md](07-transform-composition.md) | 변환 합성 `C·B·A`, 순서, 보간 한 번의 장점 | 08 |
| [08-affine-mouse-event.md](08-affine-mouse-event.md) | 마우스 드래그 상태 기계, 3점 어파인 | 09 |
| [09-perspective-transform.md](09-perspective-transform.md) | 원근 변환, w로 나누기, 8×8 연립방정식, 호모그래피 | 10 |
| [10-doc-scanner-event.md](10-doc-scanner-event.md) | 4점 드래그 문서 스캐너, 점 순서 함정, 출력 크기, LUT | 11 |

## 세션에서 발견한 코드 이슈 (수정하지 않음)

| 위치 | 내용 | 설명 위치 |
|---|---|---|
| [01.scaling.py:39](../../chap08/01.scaling.py#L39) | 창 제목 `dst3- zoom out`인데 실제로는 확대 (구멍 45,000개) | Part 1 |
| [03.scaling_bilinear.py:36](../../chap08/03.scaling_bilinear.py#L36) | `INTER_NEAREST`가 5번째 위치(`fy`)에 들어가서 실제로는 LINEAR | Part 3 |
| [03.scaling_bilinear.py:35](../../chap08/03.scaling_bilinear.py#L35) | 같은 위치 인자 실수. 기본값이 LINEAR라 우연히 맞음 | Part 3 |
| [07.affine_transform.py:37-38](../../chap08/07.affine_transform.py#L37-L38) | `warpAffine` 4번째 위치는 `dst`. 기본값이라 우연히 맞음 | Part 6 |
| [08.affine_combination.py:16](../../chap08/08.affine_combination.py#L16) | `np.multiply(center[0], -1)` → 회전 중심이 15.0화소 밀림. `center`로 고쳐야 함 | Part 7, 11 |
| [09.affine_event.py:14](../../chap08/09.affine_event.py#L14) | `warpAffine` 위치 인자. 우연히 맞음 | Part 8 |
| [10.perspective_transform.py:10](../../chap08/10.perspective_transform.py#L10) | `INTER_CUBIC` 위치 인자 → 실제로는 LINEAR | Part 9 |
| [11.perspective_event.py:16](../../chap08/11.perspective_event.py#L16) | 같음 → 실제로는 LINEAR | Part 10 |
| [11.perspective_event.py:7](../../chap08/11.perspective_event.py#L7) | 핸들이 가장자리 밖이면 음수 슬라이싱 → 빈 ROI 또는 반대편에 그려짐 | Part 10 |

이 외에 버그는 아니지만 헷갈리는 점: `05`(역방향 사용)는 양수 각도가 **시계**, `08`과 `getRotationMatrix2D`(순방향)는 **반시계** (Part 5, 11-3-b).
`warpAffine`, `warpPerspective`에서는 `INTER_AREA`가 조용히 LINEAR로 바뀌어요 (Part 11-2-d).

## 남은 할 일

- [ ] Part 11 연습 1(회전 방향 맞추기), 연습 2(`08` 버그 고치기) 직접 실행
- [ ] `projects/p1_doc_scanner` Step 3~5: `order_corners`, `quad_size`, `homography_dlt`, `warp_perspective`
- [ ] chap09 (DFT/FFT, `08.remove_moire.py`)로 모아레를 주파수 관점에서 다시 보기
- [ ] (선택) HTML 인터랙티브 시각화: 양선형 4화소(Part 3), 회전 슬라이더(Part 5), 어파인 6개 숫자(Part 6), 변환 순서 카드(Part 7), g·h 슬라이더와 w(Part 9), 4점 드래그와 det·w(Part 10), 변환 계층과 존 플레이트(Part 11)
