# projects — 교재 복습용 바닥부터 프로젝트

교재(chap02~12)에서 함수 단위로 배운 것을 **문제 단위**로 다시 엮는 프로젝트 모음이다.
현업은 이렇게 일한다:

```
문제 정의 → 데이터 수집 → 파이프라인 → 정량 평가 → 실패 분석 → 튜닝 → (속도)
```

## 최초 1회 설정

```powershell
# 저장소 루트에서
python -m pip install -e projects --no-deps
```

`cvkit`(공용 도구)을 **현재 위치 그대로** 파이썬 환경에 등록한다. `Common` 설치와 같은 방식이다.

- `--no-deps` 는 꼭 붙인다. 이미 `opencv-contrib-python` 이 깔려 있는데 `opencv-python` 이 겹쳐 설치되면 `cv2` 가 깨진다.
- 확인: `python tools/run_tests.py` (projects 폴더에서) → 전부 PASS 면 준비 완료.

## 폴더 구조

```
projects/
├── cvkit/              ← 공용 도구 (모든 프로젝트가 import)
├── _template/          ← 새 프로젝트 뼈대 (직접 고치지 말고 new_project 로 복사)
├── tools/
│   ├── new_project.py  ← 새 프로젝트 만들기
│   └── run_tests.py    ← 테스트 실행 (pytest 없이)
├── tests/              ← cvkit 자체 테스트
├── lab_topview_moire/  ← 실험 (완성본): 어안 → 톱뷰 모아레 저감 방법 비교. P3 미리보기·기준 답안
└── p1_doc_scanner/ …   ← 프로젝트들 (new_project 로 생성)
    ├── main.py         ← 실행 진입점 (--tune, --show, --input)
    ├── config.yaml     ← 파라미터 (코드에 숫자 박지 않기)
    ├── data/raw/       ← 원본 사진 (git 에 안 올림)
    ├── data/           ← 라벨·대응점 등 직접 만든 작은 파일 (git 에 올림)
    ├── results/        ← 실행 결과 (git 에 안 올림, 언제든 다시 만들 수 있으므로)
    ├── tests/          ← 직접 구현한 함수 검증
    └── README.md       ← 목표·결과표·실패 분석 (포트폴리오)
```

## 새 프로젝트 시작

```powershell
cd projects
python tools/new_project.py p1_doc_scanner "문서 스캐너"
# data/raw/ 에 사진을 넣고
python p1_doc_scanner/main.py            # 전체 처리 → results/stages/*.jpg, results/summary.csv
python p1_doc_scanner/main.py --tune     # 트랙바로 파라미터 찾기 → config.yaml 에 옮겨 적기
python tools/run_tests.py p1_doc_scanner
```

템플릿의 `pipeline()` 은 '그레이 → 블러 → Canny' 예시다. 프로젝트에 맞게 바꿔 쓴다.
VS Code 에서는 `main.py` 를 열고 F5 로 실행해도 된다 (경로를 `__file__` 기준으로 잡으므로 실행 위치와 무관).

## cvkit 한눈에

**알고리즘은 cvkit 에 넣지 않는다.** 호모그래피·RANSAC·Hough 같은 것은 각 프로젝트에서 직접 구현하며 배울 부분이다.
cvkit 에는 매번 반복되는 잡일만 있다.

| 모듈 | 주요 기능 | 왜 필요한가 |
|---|---|---|
| `io` | `imread(path, max_side=)`, `imwrite`, `list_images` | `cv2.imread` 는 한글 경로에서 조용히 `None` 을 돌려준다. 실패하면 이유가 담긴 예외를 던진다 |
| `check` | `check_image(img, dtype=, channels=)`, `describe(img)` | uint8 overflow, 채널 착오를 함수 입구에서 잡는다. `describe` 는 shape/dtype/min/max 를 한 줄로 |
| `viz` | `Stages`, `mosaic`, `show`, `put_label`, `to_display` | 중간 결과를 한 장에 모아 "어느 단계에서 망가졌나" 를 바로 본다. bool·float·음수 배열도 알아서 보이게 바꾼다. 라벨에 한글 가능 |
| `compare` | `compare(mine, ref, tol=)`, `diff_heatmap` | 직접 구현 vs OpenCV 를 최대/평균 오차·PSNR·다른 픽셀 수로 비교, 차이가 어디 몰렸는지 색으로 |
| `timing` | `Timer`, `benchmark`, `speed_table` | 처리 시간 측정, 직접 구현이 몇 배 느린지 표로 |
| `config` | `load_config`, `save_config`, `cfg.params.k` 점 표기 | 파라미터를 YAML 로 관리 |
| `project` | `Project(__file__)` → `.config`, `.images()`, `.result_path()` | 실행 위치와 무관한 경로 |
| `report` | `Table.add(...)`, `.to_markdown()`, `.save_csv()`, `.mean()` | 이미지별 지표를 쌓아 결과표로. bool 열의 `mean` 은 성공률 |
| `tuner` | `tune(img, process, params)`, `Param.from_config` | chap04 트랙바의 실전판. 실시간으로 결과를 보며 값 찾기 |

자주 쓰는 패턴:

```python
from cvkit import Stages, compare, diff_heatmap, benchmark, speed_table, describe

st = Stages()
gray = st.add("그레이", cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))   # 기록하고 그대로 돌려줌
edge = st.add("엣지", cv2.Canny(gray, 50, 150))
st.describe()                                                    # 단계별 shape/dtype/값 범위
st.show()                                                        # 창으로 (제목은 영문)

r = compare(my_warp(img, H), cv2.warpPerspective(img, H, (w, h)), tol=1)   # 직접 구현 검증
st.add("차이", r.heatmap())

print(speed_table(benchmark(my_warp, img, H, name="직접"),
                  benchmark(cv2.warpPerspective, img, H, (w, h), name="OpenCV")))
```

## 모든 프로젝트 공통 습관

| 습관 | cvkit 도구 | 이유 |
|---|---|---|
| 중간 결과를 한 장에 모아 저장 | `Stages` | 디버깅의 대부분은 "어느 단계에서 망가졌나" 찾기 |
| 트랙바로 찾고 config 로 고정 | `tune`, `config.yaml` | 코드에 박힌 숫자는 다른 데이터에서 깨진다 |
| 직접 구현은 OpenCV 와 숫자로 비교 | `compare`, `benchmark` | 원리 이해 + 라이브러리를 쓰는 이유 체감 |
| 함수 입구에서 dtype·채널 검사 | `check_image` | 현업 CV 버그 1~3위 (overflow, BGR, (x,y)↔(row,col)) |
| 실패 사례를 일부러 수집 | `Table`, 템플릿 README §6 | 성공 사진만 보면 실력이 안 는다 |
| README 에 결과표와 한계 | `Table.to_markdown` | 그대로 포트폴리오·보고 연습 |

## 로드맵

P1~P4 를 순서대로 하면 **미니 AVM 파이프라인**(호모그래피 → 렌즈 모델 → 탑뷰 LUT → 다중 카메라 합성)이 완성된다.

| | 프로젝트 | 핵심 (직접 구현) | 기간 |
|---|---|---|---|
| [ ] | P1 문서 스캐너 — [가이드](p1_doc_scanner/GUIDE.md) | 호모그래피 DLT, 역매핑 bilinear | 1주 |
| [ ] | P2 카메라 캘리브레이션·왜곡 보정 | 왜곡 모델 → remap LUT, 재투영 오차 | 2주 |
| [ ] | P3 바닥 탑뷰 + 모아레 실험 — [미리보기 실험](lab_topview_moire/README.md) | 탑뷰 LUT 합성, 축소율 맵, 피라미드 프리필터 | 2주 |
| [ ] | P4 스티칭 (파노라마 → 미니 서라운드뷰) | RANSAC, 멀티밴드 블렌딩, 노출 보정 | 2~3주 |
| [ ] | P5 주차선/주차칸 검출 + 평가 | 라벨링 툴, Hough, P/R/F1 평가기 | 2~3주 |
| [ ] | P6 (선택) 화질 측정 툴 | 슬랜티드 엣지 MTF | 1~2주 |
| [ ] | P7 (선택) 고전 CV vs 딥러닝 | 작은 CNN | 2주 |

## 챕터 커버리지 — 모든 챕터를 최소 한 번씩

본 과제만으로는 빠지는 내용이 있어서, 각 프로젝트에 자연스럽게 붙는 **복습 보너스(★)** 로 빈칸을 채운다.
★ 없는 항목은 본 과제에서 이미 쓰는 것.

| 챕터 | 내용 | 어디서 쓰나 |
|---|---|---|
| chap02~03 | 파이썬 기초, NumPy | 전 프로젝트 — 직접 구현은 NumPy 벡터화로 (for 문 버전과 `benchmark` 비교) |
| chap04 | 창·키·마우스·트랙바 이벤트 | P1 꼭짓점 수동 지정, P5 라벨링 툴, 모든 프로젝트 `--tune` |
| chap04 | 그리기, 이미지 입출력, 카메라·동영상, matplotlib | P2 웹캠 실시간 캡처, P3 동영상 입력, P2 RMS 그래프·P6 MTF 곡선 (matplotlib) |
| chap05 | 채널, 산술·비트 연산, 행렬 곱, 연립방정식 | P1 `cv2.solve` 로 호모그래피, P2 투영 `K[R\|t]` 행렬 곱, P4 블렌딩(산술)·마스크(비트 연산) |
| chap05 | 최소·최대, 정렬(sortIdx), reduce | ★ P5 `cv2.reduce` 로 행/열 투영 프로파일 → 주차선 위치 후보, Hough 선을 득표순 정렬 |
| chap06 | 화소 접근, 밝기·대비, 히스토그램, 평활화 | P4 겹침 영역 히스토그램 매칭, P5 CLAHE |
| chap06 | 컬러 공간 (HSV, CMY/CMYK 등), 이진화 | P1 적응형 이진화, P5 HSV 흰 선 추출, ★ P5 노란 선은 HSV vs CMY 의 Y 채널 vs Lab 비교 |
| chap07 | 블러, Canny, 모폴로지 | P1, P5 |
| chap07 | Roberts·Prewitt·Sobel·Laplacian·DoG | ★ P1 종이 경계 검출을 연산자별로 바꿔 성공률 비교 (P3 축소율 맵의 미분에도 Sobel) |
| chap07 | 샤프닝, min/max·median 필터 | P6 과샤프닝 오버슈트 측정, ★ P5 노면 잡티 제거에 median vs min/max 비교 |
| chap08 | 크기 변환(최근접·양선형), 이동·회전, 어파인, 원근 | P1·P3 핵심, ★ P4 어파인으로 충분한 경우 vs 호모그래피가 필요한 경우 비교 |
| chap09 | DFT·FFT, 주파수 필터링, 모아레 제거 | P3 모아레 스펙트럼·노치 필터, P6 MTF |
| chap09 | DCT | ★ P3 JPEG(8×8 DCT 양자화) 품질별로 탑뷰 디테일·모아레가 어떻게 변하는지 |
| chap10 | 허프 변환, 기울기 보정, 해리스 코너 | P5 Hough, P4 Harris, ★ P1 스캔 결과의 글자 기울기 보정 (`02.correct_object.py` 방식) |
| chap10 | 워핑(모핑), 카메라 캘리브레이션 | P2 캘리브레이션, ★ P3 메시 탑뷰: 격자 꼭짓점만 정확히 계산하고 내부는 보간 (실제 AVM 메시 방식) |
| chap10 | kNN, MNIST | P7 kNN vs CNN |
| chap11 | GUI 그림판 | P5 라벨링 툴 뼈대로 재활용 (`05.PaintCV.py`) |
| chap11 | Haar 얼굴 검출, 히스토그램 비교 | ★ P4 노출 보정 전후 겹침 영역을 `compareHist` 로 수치화, ★ P7 Haar 검출기 vs 딥러닝 검출기 |
| chap12 | 동전 (Otsu, 윤곽선, 외접원, 색상 히스토그램) | P1 윤곽선 검출, ★ P7 동전 분류: 색상 히스토그램 규칙 vs CNN |
| chap12 | 번호판 (후보 검출, SVM) | P1 윤곽선 + 가로세로비 필터 (번호판 후보 검출 방식), P7 SVM vs CNN |

## 참고

- OpenCV 창 제목·트랙바 이름은 **영문**으로 쓴다 (Windows 에서 한글이 깨진다). 이미지 안 라벨(`put_label`, `Stages`)은 한글 가능.
- 확인된 환경: Python 3.12 · NumPy 2.1 · OpenCV(contrib) 4.12 · PyYAML 6.0 · Pillow 11 · PyTorch 2.6 (P7 용)
