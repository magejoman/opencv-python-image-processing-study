# P1. 문서 스캐너

> 프로젝트를 진행하면서 채워 나가는 결과 보고서. 끝났을 때 이 문서만 읽어도 무엇을 왜 했고 결과가 어땠는지 알 수 있어야 한다.
> 진행 방법은 [GUIDE.md](GUIDE.md).

## 1. 목표

- 무엇을 만드는가: 비스듬히 찍은 종이 사진을 반듯하게 펴진 스캔본으로 바꾸는 프로그램
- 완료 기준:
  - 호모그래피·워핑·적응형 이진화를 직접 구현하고 OpenCV 와 차이를 설명할 수 있다
  - 합성 데이터 검출률 ___% → ___% (개선 전 → 후), 꼭짓점 평균 오차 ___px 이하
  - 실사 20장 검출률 ___%, 실패 원인을 유형별로 분류

## 2. 데이터

| 항목 | 내용 |
|---|---|
| 합성 | `tools/make_synthetic.py` (seed 0) 20장, 정답 자동 생성. 뒤 8장은 어려움 (`meta.json` 의 issues) |
| 실사 — 촬영 방법 | |
| 실사 — 장수 | |
| 실사 — 일부러 넣은 어려운 경우 | |
| 실사 — 정답 | `tools/label_corners.py` 로 직접 클릭 (`data/raw/gt.json`) |

실사 사진은 `data/raw/` (git 에 올리지 않음, `gt.json` 만 커밋). 합성 데이터는 언제든 다시 만들 수 있어서 커밋하지 않는다.

## 3. 파이프라인

```
사진 → 축소 → 종이 찾기 → 꼭짓점 정렬 → 호모그래피 → 원본 해상도에서 워핑 → 적응형 이진화 → 스캔본
```

| 단계 | 방법 | 직접 구현? | 복습 챕터 |
|---|---|---|---|
| 종이 찾기 | 블러 → Canny → 닫힘 → 윤곽선 → approxPolyDP | OpenCV 조합 | 07 |
| 꼭짓점 정렬 | 중심 기준 각도 정렬 | ✏️ | — |
| 호모그래피 | DLT 8×8 연립방정식 / 최소제곱 | ✏️ | 05, 08 |
| 워핑 | 역매핑 + 양선형 보간 (벡터화) | ✏️ | 08 |
| 스캔 효과 | 적응형 이진화 (적분 영상) | ✏️ | 06 |
| 수동 보정 | 마우스로 네 점 | 제공 | 04, 08 |

## 4. 실행

```powershell
python p1_doc_scanner/tools/make_synthetic.py   # 합성 데이터 생성
python p1_doc_scanner/main.py                    # 전체 처리 → p1_doc_scanner/results/
python p1_doc_scanner/main.py --tune             # 검출 파라미터 튜닝
python p1_doc_scanner/main.py --compare          # 직접 구현 vs OpenCV
python p1_doc_scanner/main.py --manual           # 실패 시 수동 보정
python tools/run_tests.py p1_doc_scanner         # 채점
```

## 5. 결과

| 버전 | 합성 검출률 | 합성 평균 오차 | 실사 검출률 | 실사 평균 오차 |
|---|---|---|---|---|
| 기준선 (impl 전부 opencv) | | | | |
| impl 전부 mine | | | | |
| 개선 1: | | | | |
| 개선 2: | | | | |

## 6. 실패 분석

| 실패 유형 | 장수 | 망가진 단계 | 원인 | 대책 |
|---|---|---|---|---|
| | | | | |

## 7. 직접 구현 vs OpenCV

| 함수 | 최대 차이 | 평균 차이 | 속도 (직접 / OpenCV) | 차이가 나는 이유 |
|---|---|---|---|---|
| homography_dlt | | | | |
| warp_perspective | | | | |
| adaptive_threshold | | | | |

## 8. 배운 것 / 다음에 해볼 것

-
