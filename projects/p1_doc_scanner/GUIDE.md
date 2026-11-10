# P1. 문서 스캐너 — 단계별 가이드

> 비스듬히 찍은 종이 사진을 넣으면, 반듯하게 펴진 스캔본이 나오는 프로그램을 바닥부터 만든다.
> 예상 기간: 주 6~8시간 기준 1~2주

---

## 0. 시작하기 전에

### 0.1 이 프로젝트로 얻는 것

1. **파이프라인 감각** — 함수 하나가 아니라 "입력 → 여러 단계 → 출력 → 평가" 전체를 직접 엮어 본다.
2. **호모그래피를 손으로 푸는 경험** — P3 탑뷰, P4 스티칭에서 그대로 다시 쓰는 핵심 수학이다.
   "종이 평면 → 화면" 과 "지면 평면 → 탑뷰" 는 수학적으로 **완전히 같은 문제**다.
3. **숫자로 말하는 습관** — "잘 되네" 대신 "합성 20장 중 검출률 80%, 꼭짓점 평균 오차 1.2px" 처럼 말한다.

### 0.2 전체 그림

```
 사진 (4000×3000)
   │
   │  축소 (긴 변 1000px) ─────────────── 검출은 작게: 빠르고, 잔무늬 엣지가 줄어든다
   ▼
 ┌──────────────────────────────┐
 │ Step 2  종이 찾기              │  그레이 → 블러 → Canny → 닫힘 → 윤곽선 → 사각형 근사
 │ find_document_quad            │  → 네 점 (순서 뒤죽박죽)
 └──────────────────────────────┘
   ▼
 ┌──────────────────────────────┐
 │ Step 3  꼭짓점 정렬            │  [좌상, 우상, 우하, 좌하] 로 정렬 + 원본 해상도로 되돌리기 (÷ 배율)
 │ order_corners, quad_size      │  펼칠 크기 (너비, 높이) 정하기
 └──────────────────────────────┘
   ▼
 ┌──────────────────────────────┐
 │ Step 4  호모그래피             │  네 쌍의 대응점 → 3×3 행렬 H (8×8 연립방정식)
 │ homography_dlt                │
 └──────────────────────────────┘
   ▼
 ┌──────────────────────────────┐
 │ Step 5  워핑                  │  출력 픽셀마다 H⁻¹ 로 원본 위치를 찾아 양선형 보간
 │ warp_perspective              │  (원본 해상도에서 펼친다 → 글자가 선명)
 └──────────────────────────────┘
   ▼
 ┌──────────────────────────────┐
 │ Step 6  스캔 효과              │  주변 평균보다 밝으면 흰색 → 그림자가 있어도 깔끔
 │ adaptive_threshold            │
 └──────────────────────────────┘
   ▼
 스캔본 + 결과표 (검출 여부, 꼭짓점 오차 px, 처리 시간)
```

### 0.3 파일 구성

| 파일 | 내용 | 누가 |
|---|---|---|
| [scanner/detect.py](scanner/detect.py) | Step 2 `find_document_quad` | ✏️ 직접 구현 |
| [scanner/corners.py](scanner/corners.py) | Step 3 `order_corners`, `quad_size` | ✏️ 직접 구현 |
| [scanner/homography.py](scanner/homography.py) | Step 4 `homography_dlt` (`apply_homography` 는 제공) | ✏️ 직접 구현 |
| [scanner/warp.py](scanner/warp.py) | Step 5 `warp_perspective` | ✏️ 직접 구현 |
| [scanner/enhance.py](scanner/enhance.py) | Step 6 `adaptive_threshold` | ✏️ 직접 구현 |
| [scanner/ui.py](scanner/ui.py) | 마우스로 꼭짓점 찍기 | 제공 |
| [scanner/evaluate.py](scanner/evaluate.py) | 정답 파일 읽기, 꼭짓점 오차 계산 | 제공 |
| [main.py](main.py) | 전체 조립, 평가, `--tune` `--compare` `--manual` 모드 | 제공 |
| [tools/make_synthetic.py](tools/make_synthetic.py) | 정답이 있는 합성 사진 만들기 | 제공 |
| [tools/label_corners.py](tools/label_corners.py) | 직접 찍은 사진에 정답 찍기 | 제공 |
| [tests/](tests/) | **채점기** — 직접 구현한 함수를 OpenCV·정답과 비교 | 제공 |
| [config.yaml](config.yaml) | 파라미터, 직접 구현 ↔ OpenCV 전환 스위치 | 같이 고침 |
| [README.md](README.md) | 결과 보고서 | ✏️ 직접 작성 |

### 0.4 각 Step 을 진행하는 루틴

```
① 이 가이드의 해당 절을 읽는다
② scanner/ 의 빈칸 함수를 구현한다  (NotImplementedError 줄을 지우고 채우기)
③ 채점한다          cd projects
                    python tools/run_tests.py p1_doc_scanner
④ 눈으로 확인한다    python p1_doc_scanner/main.py       → results/stages/*.jpg 열어 보기
⑤ README 에 기록한다 (숫자, 실패 사례, 배운 점)
```

채점기 출력에서 `FAIL` 아래 메시지를 꼭 읽자. **무엇이 기대값이고 무엇이 나왔는지** 써 있다.
아직 구현하지 않은 Step 의 테스트는 `NotImplementedError` 로 실패하는데, 이건 정상이다.

### 0.5 정답 보기 규칙

각 Step 끝에 정답 코드가 **접혀** 있다 (`▶ 정답 보기` 를 클릭하면 펼쳐진다).

1. 먼저 30분 이상 혼자 시도한다.
2. 막히면 "힌트" 를 본다.
3. 그래도 막히면 정답을 보되, **보고 나서 창을 닫고 다시 처음부터 직접 쳐 본다.** 눈으로 읽은 코드는 내 것이 아니다.

---

## Step 1. 데이터 준비 (반나절)

### 1.1 합성 데이터 만들기

```powershell
cd projects
python p1_doc_scanner/tools/make_synthetic.py
```

`data/synthetic/` 에 사진 20장과 파일 두 개가 생긴다.

| 파일 | 내용 |
|---|---|
| `syn_000.jpg` ~ `syn_019.jpg` | 배경 위에 종이를 원근감 있게 붙인 사진 (1280×960 또는 960×1280) |
| `gt.json` | 각 사진의 **정답 꼭짓점** [좌상, 우상, 우하, 좌하] |
| `meta.json` | 각 사진의 조건 (배경 종류, 기울기, 어려움 요소) |

**왜 합성 데이터부터 하나?** 종이를 붙일 때 쓴 변환을 내가 알기 때문에 꼭짓점 정답을 **정확히** 안다.
그래서 사진을 찍기 전에도 개발을 시작할 수 있고, 처음부터 "꼭짓점 오차 몇 px" 로 정량 평가를 할 수 있다.

뒤쪽 8장(40%)은 일부러 어렵게 만들었다. 현실에서 실제로 자주 생기는 문제들이다.

| 어려움 요소 (`issues`) | 모습 | 왜 어려운가 |
|---|---|---|
| `low_contrast` | 밝은 책상 위의 흰 종이 | 경계의 밝기 차이가 작아 엣지가 약하다 |
| `shadow` | 종이를 가로지르는 그림자 | 그림자 경계도 강한 엣지가 된다 |
| `occluder` | 펜·손가락이 테두리를 가림 | 테두리가 끊기거나 사각형이 아닌 모양이 된다 |
| `clutter` | 폰·포스트잇이 종이에 맞닿음 | 두 물체의 윤곽선이 하나로 합쳐진다 |

### 1.2 첫 실행 — 실패하는 게 정상

```powershell
python p1_doc_scanner/main.py
```

```
아직 구현하지 않은 단계가 있습니다 → Step 2: find_document_quad 를 구현하세요 (GUIDE.md §2)
```

이 메시지가 나오면 환경은 준비된 것이다.

### 1.3 실제 사진 20장 찍기

폰으로 A4 종이(글자가 있는 것)를 찍어 `data/raw/` 에 넣는다. **골고루** 찍는 게 중요하다.

| 조건 | 장수 | 예시 |
|---|---|---|
| 쉬운 사진 | 8 | 어두운 책상, 위에서 약간 비스듬히, 밝은 조명 |
| 많이 기울임 | 3 | 30° 이상 회전, 아주 비스듬한 각도 |
| 낮은 대비 | 3 | 흰 책상·밝은 바닥 위 |
| 그림자 | 3 | 폰이나 손 그림자가 종이에 걸침 |
| 잡동사니 | 3 | 펜·폰·컵이 종이 옆이나 위에 |

> 종이 네 귀퉁이가 **모두 화면 안에** 들어오게 찍는다. 귀퉁이가 잘린 사진은 이번 프로젝트 범위 밖이다.
> 폰 사진은 4000px 안팎이라 용량이 크다. `data/raw/` 는 git 에 올라가지 않게 설정돼 있다.

### 1.4 정답 라벨링

```powershell
python p1_doc_scanner/tools/label_corners.py
```

창이 뜨면 **좌상 → 우상 → 우하 → 좌하** 순서로 종이 꼭짓점을 클릭하고 Enter 를 누른다.

| 키 | 동작 |
|---|---|
| 좌클릭 | 점 찍기 |
| 우클릭 | 마지막 점 지우기 |
| Enter | 확정 (4점일 때) → 바로 `data/raw/gt.json` 에 저장 |
| s | 이 사진 건너뛰기 |
| ESC | 종료 (그때까지 찍은 것은 저장돼 있음) |

> 💡 **라벨도 오차가 있다.** 화면을 줄여서 보여주므로 한 번 클릭이 원본에서는 4px 쯤 된다.
> 시간이 되면 같은 사진을 `--redo` 로 한 번 더 찍어서 두 정답이 몇 px 다른지 재 보자.
> 그 값이 "사람 라벨의 오차" 이고, 알고리즘 오차를 이것보다 작게 만드는 건 의미가 없다.
> 현업에서도 라벨 품질 확인은 중요한 일이다.

### ✅ Step 1 체크

- [ ] `data/synthetic/` 에 20장 + `gt.json` + `meta.json`
- [ ] `data/raw/` 에 직접 찍은 사진 20장 + `gt.json`

---

## Step 2. 종이 찾기 — `find_document_quad` (1~2일)

### 2.1 목표

```
입력: 축소된 사진 (uint8, BGR)            출력: 네 점 (4, 2) float32
┌────────────────────────┐               [[312.0, 140.0],
│   ╱‾‾‾‾‾‾‾‾╲            │                [655.0, 182.0],
│  ╱  글자    ╲   책상    │       →        [601.0, 701.0],
│ ╱   글자     ╲          │                [240.0, 650.0]]
│ ‾‾‾‾‾‾‾‾‾‾‾‾‾          │               (순서는 아무래도 됨 → Step 3)
└────────────────────────┘               못 찾으면 None
```

### 2.2 큰 그림: 다섯 단계

```
그레이 ──→ 블러 ──→ Canny ──→ 닫힘(close) ──→ 윤곽선 ──→ 사각형 근사 ──→ 조건 검사
 색은      잔무늬    밝기가     끊어진        엣지 픽셀을   점 수백 개를     꼭짓점 4개?
 필요 없음  줄이기   급변하는 곳 엣지 잇기     선으로 묶기   몇 개로 단순화    볼록? 충분히 큼?
```

> 📚 **복습 — GaussianBlur** (reference 03 OpenCV기초, chap07 `12.filter_gaussian.py`)
> 주변 픽셀을 가우시안 가중치로 평균 내서 흐리게 만든다. 커널 크기는 **홀수**여야 한다.
> 여기서 쓰는 이유: 나뭇결이나 천의 잔무늬가 엣지로 잡히는 것을 줄이려고.

> 📚 **복습 — Canny** (chap07 `08.edge_canny.py`)
> 밝기 기울기가 `high` 보다 크면 "확실한 엣지", `low` 와 `high` 사이면 **확실한 엣지에 이어져 있을 때만** 엣지로 남긴다.
> 결과는 0 / 255 의 uint8, 엣지 두께는 1픽셀.

> 📚 **복습 — 닫힘(close)** (chap07 `16.close_open.py`)
> 팽창(dilate) 후 침식(erode). 가까운 흰 픽셀끼리 이어 붙여 **틈을 메운다.**
> 종이 테두리 엣지가 군데군데 끊기면 윤곽선이 닫힌 고리가 되지 않으므로 이게 중요하다.

### 2.3 새로 배우는 함수 ① `cv2.findContours` — 엣지를 "선" 으로 묶기

Canny 결과는 흰 픽셀이 흩어진 그림일 뿐이다. `findContours` 는 서로 붙어 있는 흰 픽셀 덩어리마다
**테두리를 따라가며 좌표 목록**을 만든다.

```python
contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#  contours: 윤곽선들의 리스트. 각 윤곽선은 shape (N, 1, 2) int32 — N 개의 (x, y)
```

| 인자 | 선택지 | 이번에 쓸 것과 이유 |
|---|---|---|
| 모드 | `RETR_EXTERNAL` 가장 바깥 것만 / `RETR_LIST` 전부 / `RETR_TREE` 안팎 관계까지 | **EXTERNAL** — 종이 안의 글자 윤곽선 수백 개는 필요 없다 |
| 근사 | `CHAIN_APPROX_NONE` 모든 점 / `CHAIN_APPROX_SIMPLE` 직선 구간은 양 끝만 | **SIMPLE** — 메모리 절약 |

> ⚠️ `(N, 1, 2)` 의 가운데 1 은 OpenCV 의 옛 관례다. 다룰 때는 `c.reshape(-1, 2)` 로 (N, 2) 로 펴서 쓴다.
> OpenCV 3.x 는 값을 3개 돌려줬다. 인터넷 예제에서 `_, contours, _ = ...` 를 보면 옛 버전 코드다.

### 2.4 새로 배우는 함수 ② `contourArea`, `arcLength`

```python
area = cv2.contourArea(c)            # 윤곽선이 둘러싼 넓이 (px²)
peri = cv2.arcLength(c, True)        # 둘레 길이 (px). True = 닫힌 도형
```

**함정:** 종이 테두리가 한 군데라도 끊겨 있으면, 윤곽선은 고리가 아니라 **선을 따라 갔다가 되돌아오는 모양**이 된다.
그러면 넓이가 거의 0 이 된다. "큰 사각형이 분명히 보이는데 못 찾는" 경우의 단골 원인이고, 닫힘 연산이 필요한 이유다.

```
닫힌 테두리                  끊긴 테두리
┌────────┐                  ┌────────┐
│        │  넓이 ≈ 종이       │         ← 틈
│        │                  │        │  넓이 ≈ 0 (선의 양면을 따라 왕복)
└────────┘                  └────────┘
```

### 2.5 새로 배우는 함수 ③ `cv2.approxPolyDP` — 점 수백 개를 꼭짓점 몇 개로

종이 윤곽선은 점이 수백 개다. **Douglas–Peucker 알고리즘**으로 "허용 오차 ε 안에서 가장 적은 꼭짓점" 으로 줄인다.

```
① 양 끝 A, B 를 잇는다          ② 선분에서 가장 먼 점 C 를 찾는다   ③ 거리 > ε 이면 C 를 꼭짓점으로 남기고
                                                                    AC, CB 에 대해 반복. ≤ ε 이면 직선으로 끝.
A ●~~~~~~~~~~~~~● B           A ●───────────● B                  A ●            ● B
   ~~~         ~~                 ╲    d    ╱                         ╲          ╱
      ~~~~●~~~~                     ╲  │  ╱                            ╲        ╱
          C                           ●C                                ●C ────
```

```python
approx = cv2.approxPolyDP(c, approx_eps * peri, True)    # ε 를 둘레에 비례하게
```

ε 를 고정값(예: 10px)이 아니라 **둘레의 비율**로 주는 이유: 종이가 크게 찍히든 작게 찍히든 같은 기준이 되도록.
예를 들어 1000px 이미지에서 종이 둘레가 약 2400px 이면 `0.02 × 2400 = 48px` 까지의 굴곡은 직선으로 본다.

| `approx_eps` | 효과 |
|---|---|
| 너무 작음 (0.005) | 모서리의 작은 굴곡까지 꼭짓점이 됨 → 5~8각형이 나와서 실패 |
| 적당 (0.02) | 종이 → 4각형 |
| 너무 큼 (0.1) | 무엇이든 3~4각형이 됨 → 종이가 아닌 것도 사각형으로 오인 |

### 2.6 새로 배우는 함수 ④ `cv2.isContourConvex` — 볼록한가

펜이 테두리를 가리면 근사 결과가 "움푹 들어간 사각형" 일 수 있다. 종이는 원근 변환을 해도 **항상 볼록**하므로 오목하면 버린다.

```
볼록 (통과)        오목 (탈락)
●──────●          ●──────●
│      │          │    ╱
│      │          │   ●     ← 안쪽으로 꺾인 꼭짓점
●──────●          ●──────●
```

### 2.7 구현 순서 (힌트)

```
1. 그레이 변환 → 블러 → Canny → 닫힘                 (각 결과를 stages 에 기록)
2. findContours(RETR_EXTERNAL)
3. 넓이 큰 순으로 정렬
4. 하나씩 보면서:
     넓이 < min_area_ratio × 이미지 넓이 → 중단 (이후는 전부 더 작으니까)
     approxPolyDP → 꼭짓점 4개이고 볼록하면 → (4, 2) float32 로 바꿔 돌려준다
5. 끝까지 못 찾으면 None
```

**디버깅 화면을 꼭 만들자.** `stages` 가 None 이 아닐 때 `stages.add("Canny", edges)` 처럼 단계마다 기록하면,
`main.py` 가 사진마다 모자이크를 `results/stages/` 에 저장해 준다. 실패 원인의 90% 는 이 그림 한 장으로 보인다.
윤곽선 전체를 얇게, 근사한 후보를 굵게 그린 이미지도 추가하면 더 좋다.

```python
def log(label, im):
    if stages is not None:
        stages.add(label, im)
```

### 2.8 확인 — 트랙바로 보기

Step 2 는 채점기 대신 **눈과 튜너**로 확인한다 (Step 3 를 마치면 정답과 비교한 숫자가 나온다).

```powershell
python p1_doc_scanner/main.py --tune
```

첫 사진에 대해 트랙바가 뜬다. 하나씩 움직이며 관찰하자.

| 트랙바 | 올리면 | 내리면 |
|---|---|---|
| `blur_ksize` | 잔무늬 엣지 감소, 하지만 약한 종이 경계도 사라짐 | 배경 질감이 엣지로 잔뜩 |
| `canny_low` / `canny_high` | 엣지가 줄어 깔끔하지만 경계가 끊김 | 엣지가 많아져 배경과 합쳐짐 |
| `morph_ksize` | 틈이 잘 메워지지만 옆 물체와 붙어 버림 | 틈이 안 메워짐 |
| `approx_eps` | (§2.5 표 참고) | |

`s` 로 저장하면 `results/tuned_params.yaml` 에 값이 남는다. 마음에 들면 `config.yaml` 의 `detect` 에 옮겨 적는다.
**한 장에만 맞추지 말 것.** `--input` 으로 다른 사진을 열어 같은 값이 통하는지 확인하자.

<details>
<summary>▶ 정답 보기 — find_document_quad</summary>

```python
def find_document_quad(img, *, blur_ksize=5, canny_low=50, canny_high=150,
                       morph_ksize=5, approx_eps=0.02, min_area_ratio=0.1, stages=None):
    def log(label, im):
        if stages is not None:
            stages.add(label, im)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    log(f"블러 k={blur_ksize}", blur)
    edges = cv2.Canny(blur, canny_low, canny_high)
    log(f"Canny {canny_low}/{canny_high}", edges)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_ksize, morph_ksize))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    log(f"닫힘 k={morph_ksize}", closed)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = min_area_ratio * img.shape[0] * img.shape[1]
    debug = None
    if stages is not None:
        debug = img.copy()
        cv2.drawContours(debug, contours, -1, (255, 0, 0), 1)       # 모든 윤곽선 (파랑, 얇게)
    found = None
    for c in sorted(contours, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(c) < min_area:
            break                                                   # 넓이순이므로 이후는 전부 더 작다
        approx = cv2.approxPolyDP(c, approx_eps * cv2.arcLength(c, True), True)
        if debug is not None:
            cv2.drawContours(debug, [approx], -1, (0, 165, 255), 2)  # 후보 (주황, 굵게)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            found = approx.reshape(4, 2).astype(np.float32)
            break
    if debug is not None:
        log("윤곽선 (파랑) / 후보 (주황)", debug)
    return found
```

</details>

---

## Step 3. 꼭짓점 정렬 — `order_corners`, `quad_size` (반나절)

### 3.1 왜 순서가 중요한가

`approxPolyDP` 가 돌려주는 네 점의 순서는 **윤곽선을 따라간 순서**일 뿐, 어느 게 좌상인지 모른다.
호모그래피는 "src 의 i 번째 점 → dst 의 i 번째 점" 으로 대응시키므로, 순서가 어긋나면 결과가 **뒤집히거나 꼬인다.**

```
올바른 대응                     한 칸 밀린 대응 (90° 회전)         두 점이 바뀐 대응 (꼬임)
src TL→dst TL ...              src TR→dst TL ...                  나비넥타이 모양 ⋈
┌──────┐                       ┌──────┐                           ╲    ╱
│ ABC  │                       │ ⋖    │                            ╲  ╱
│      │                       │ ⋖    │                            ╱  ╲
└──────┘                       └──────┘                           ╱    ╲
```

> 📚 **복습 — 이미지 좌표계** (reference 01·03)
> 점은 `(x, y)` = (가로, 세로), 배열 접근은 `img[y, x]` = `img[행, 열]`. **y 는 아래로 증가**한다.
> 그래서 "위쪽" 은 y 가 **작은** 쪽이다. 수학 시간의 좌표계와 반대라 헷갈리기 쉽다.

### 3.2 방법 1 — x+y, y−x 트릭 (인터넷에 가장 흔한 방법)

| 꼭짓점 | 특징 | 고르는 법 |
|---|---|---|
| 좌상 | x 도 작고 y 도 작다 | **x+y 최소** |
| 우하 | x 도 크고 y 도 크다 | **x+y 최대** |
| 우상 | x 는 크고 y 는 작다 | **y−x 최소** |
| 좌하 | x 는 작고 y 는 크다 | **y−x 최대** |

짧고 직관적이다. 직사각형이 ±45° 안에서 회전한 경우는 전부 맞는다. 그런데…

### 3.3 방법 1 이 깨지는 경우

원근이 심하게 찍힌 이 사각형을 보자 (채점기 `test_strong_perspective_breaks_sum_diff_trick`).

```
          ● TR (200, 90)
 TL ●
 (100,100)
                       ● BR (210, 200)
  ● BL (20, 160)
```

| 점 | (x, y) | x+y | y−x |
|---|---|---|---|
| TL | (100, 100) | 200 | 0 |
| TR | (200, 90) | 290 | **−110** ← 최소 |
| BR | (210, 200) | **410** ← 최대 | −10 |
| BL | (20, 160) | **180** ← 최소 | **140** ← 최대 |

x+y 최소가 TL 이 아니라 **BL** 이다. 결과는 `[BL, TR, BR, BL]` 로, **BL 이 두 번** 나오고 TL 은 사라진다.
각 꼭짓점을 따로따로 골라서 생기는 문제다. 네 점을 **함께** 보는 방법이 필요하다.

### 3.4 방법 2 — 중심 기준 각도로 정렬

```
           -90°
            │
  -135° ●   │   ● -45°        중심에서 각 점을 바라보는 각도 = arctan2(dy, dx)
         ╲  │  ╱              (y 가 아래로 증가하므로 위쪽이 음수 각도)
  180° ────중심──── 0°
         ╱  │  ╲              각도 오름차순 = 화면에서 시계 방향 = TL → TR → BR → BL
   135° ●   │   ● 45°
            │
           90°
```

1. 네 점의 평균 = 중심
2. 각 점의 각도 `np.arctan2(y − cy, x − cx)` 를 구해 **오름차순 정렬** → 시계 방향 순서가 된다
3. 이제 "어디서 시작할지" 만 정하면 된다. 좌상은 중심에서 **−135° (왼쪽 위 대각선) 방향에 가장 가까운** 점이다

위 예시로 계산하면 (중심 = (132.5, 137.5)):

| 점 | 각도 | −135° 와의 차이 |
|---|---|---|
| TL (100, 100) | −130.9° | **4.1°** ← 가장 가까움 → 시작점 |
| TR (200, 90) | −35.1° | 99.9° |
| BR (210, 200) | 38.9° | 173.9° |
| BL (20, 160) | 168.7° | 56.3° (−191.3° 로 보면 56.3° 차이) |

> 💡 **각도 차이 계산의 함정:** 168.7° 와 −135° 의 차이는 303.7° 가 아니라 56.3° 다 (원을 한 바퀴 도니까).
> `((a − b + 180) % 360) − 180` 으로 −180 ~ 180 범위로 접은 뒤 절댓값을 쓰면 된다 (라디안이면 180 → π).
> 정렬된 배열을 시작점부터 다시 늘어놓을 때는 `np.roll(pts, -start, axis=0)` 이 편하다.

### 3.5 `quad_size` — 펼칠 크기

```
TL ●────── 위 80 ──────● TR
   ╱                    ╲          너비 = max(위, 아래) = 120
  ╱                      ╲         높이 = max(왼쪽, 오른쪽) ≈ 63.2 → 63
BL ●──────── 아래 120 ──────● BR
```

원근 때문에 가까운 변은 길게, 먼 변은 짧게 찍힌다. **긴 쪽**을 고르면 해상도를 잃지 않는다.
길이는 `np.linalg.norm(tr - tl)`, 반환은 반올림한 정수 `(width, height)` 로.

### 3.6 채점 + 첫 전체 실행 🎉

```powershell
python tools/run_tests.py p1_doc_scanner        # test_corners.py 가 전부 PASS 여야 한다
python p1_doc_scanner/main.py
```

`config.yaml` 의 `impl` 이 전부 `opencv` 이므로, Step 4~6 은 아직 OpenCV 함수가 대신 해 준다.
**처음으로 파이프라인 전체가 돈다.**

```
  syn_000.jpg: 성공 (평균 오차 0.7px)
  ...
  syn_017.jpg: 검출 실패
== 요약: 20장, 검출률 80%, 성공률 100% (평균 오차 10px 이하)
```

- `results/stages/` — 사진마다 중간 결과 모자이크. 검출 결과(초록)와 정답(빨강)이 겹쳐 그려진다
- `results/scans/` — 스캔본
- `results/summary.csv` — 사진별 숫자 (엑셀로 열어도 한글이 안 깨진다)

**이 숫자를 README 에 "기준선(baseline)" 으로 적어 두자.** 이후 무엇을 바꾸든 이 숫자와 비교한다.

<details>
<summary>▶ 정답 보기 — order_corners, quad_size</summary>

```python
def order_corners(pts):
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])     # -π ~ π, 이미지 좌표계
    pts = pts[np.argsort(angles)]                                         # 화면에서 시계 방향 순서
    gap = np.abs((np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0]) + 3 * np.pi / 4 + np.pi)
                 % (2 * np.pi) - np.pi)                                   # -135°(왼쪽 위 방향)와의 각도 차
    return np.roll(pts, -int(np.argmin(gap)), axis=0)


def quad_size(quad):
    tl, tr, br, bl = np.asarray(quad, dtype=np.float64)
    width = max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))
    height = max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))
    return int(round(width)), int(round(height))
```

`gap` 줄 풀이: 각도 a 와 −135°(= −3π/4) 의 차이는 `a − (−3π/4) = a + 3π/4`.
여기에 π 를 더하고 2π 로 나눈 나머지에서 π 를 빼면 −π ~ π 로 접힌다. 그 절댓값이 원 위의 최단 각도 차이다.

</details>

---

## Step 4. 호모그래피 — `homography_dlt` (1~2일)

> 📚 **복습 — 가상광고판** (reference 04)
> 광고판 네 꼭짓점을 클릭하고 `cv2.findHomography` → `cv2.warpPerspective` 로 다른 그림을 붙였다.
> 그때 블랙박스로 썼던 `findHomography` 의 **안을 연다.**

### 4.1 동차 좌표 — 왜 2D 변환에 3×3 행렬을 쓰나

2D 점 `(x, y)` 에 1 을 붙여 `(x, y, 1)` 로 쓰는 것을 **동차 좌표(homogeneous coordinates)** 라고 한다.
규칙은 하나다: **`(X, Y, W)` 는 `(X/W, Y/W)` 를 뜻한다.** 그래서 `(2, 4, 2)` 와 `(1, 2, 1)` 은 같은 점이다.

```
[X]   [h11 h12 h13] [x]
[Y] = [h21 h22 h23] [y]        →   u = X / W,   v = Y / W
[W]   [h31 h32 h33] [1]
```

- 아래 줄이 `[0 0 1]` 이면 W = 1 → 그냥 어파인 변환 (chap08 의 이동·회전·크기·기울임)
- 아래 줄에 값이 있으면 **점마다 W 가 달라진다** → 멀리 있는 쪽은 작게, 가까운 쪽은 크게 = **원근**

> 🎥 **비유:** 벽에 비친 슬라이드 영사기 화면을 떠올려 보자. 영사기를 비스듬히 두면 네모난 슬라이드가 사다리꼴로 비친다.
> 슬라이드 평면 → 벽 평면, 이렇게 **평면에서 평면으로** 빛을 통해 옮기는 변환이 호모그래피다.
> 종이 평면 → 카메라 화면도, 지면 → AVM 탑뷰도 같은 변환이다.

### 4.2 식 전개 — 미지수 8개

h33 = 1 로 고정한다. H 전체에 아무 숫자를 곱해도 X/W, Y/W 는 그대로라서 **실제 자유도는 9가 아니라 8**이기 때문이다.

```
u = (h11·x + h12·y + h13) / (h31·x + h32·y + 1)
```

양변에 분모를 곱하고 정리하면 **미지수에 대해 1차식**이 된다.

```
u·(h31·x + h32·y + 1) = h11·x + h12·y + h13
→  h11·x + h12·y + h13                         − u·x·h31 − u·y·h32 = u
                          h21·x + h22·y + h23  − v·x·h31 − v·y·h32 = v      (v 도 같은 방법)
```

**점 한 쌍 → 식 두 개.** 미지수가 8개이므로 **네 쌍이면 8×8 연립방정식**이 된다.

```
 미지수 순서: h = [h11, h12, h13, h21, h22, h23, h31, h32]

      x   y   1   0   0   0   −u·x   −u·y          u
    [ 0   0   0   x   y   1   −v·x   −v·y ]  h  =  [ v ]
      ... 점마다 두 줄씩, 네 점이면 8줄 ...
            A (8×8)                     (8,)       b (8,)
```

### 4.3 손으로 따라가 보기

사진 속 종이 `src` 를 300×400 직사각형 `dst` 로 펼친다고 하자.

| | TL | TR | BR | BL |
|---|---|---|---|---|
| src (x, y) | (120, 80) | (400, 110) | (430, 500) | (90, 470) |
| dst (u, v) | (0, 0) | (299, 0) | (299, 399) | (0, 399) |

TR 쌍 (x, y) = (400, 110) → (u, v) = (299, 0) 이 만드는 두 줄:

```
[400  110  1    0    0  0   −119600   −32890]  h = 299        ← −u·x = −299·400, −u·y = −299·110
[  0    0  0  400  110  1        −0       −0]  h = 0          ← v = 0 이라 뒤 두 칸이 0
```

여덟 줄을 다 채워 풀면:

```
H = [[ 1.078128     0.082933   −136.0101 ]
     [−0.136421     1.273264    −85.49058]
     [−0.00011003   0.00056320    1.0    ]]
```

검산: BR (430, 500) 에서 `W = −0.00011003·430 + 0.0005632·500 + 1 = 1.2343`.
W 가 1 이 아니다. 이게 원근 효과다. `u = X / W = 299.0` ✓

### 4.4 원근의 비선형성 직접 확인하기

위 사진에서 종이 네 꼭짓점의 **평균** (260, 290) 을 H 로 보내 보자.

```
네 꼭짓점 평균  (260.00, 290.00) → (148.37, 218.81)    ✗ 펼친 종이의 중심 (149.5, 199.5) 이 아니다!
대각선의 교점   (261.15, 271.24) → (149.50, 199.50)    ✓ 정확히 중심
```

**"사진 속 종이의 가운데는 꼭짓점 평균이 아니다."** 원근에서는 먼 쪽이 압축되므로 평균이 가까운 쪽으로 쏠린다.
반면 직선은 직선으로 보내므로(호모그래피의 성질), 대각선의 교점은 정확히 중심으로 간다.
P3 에서 탑뷰를 만들 때 이 감각이 다시 필요하다. `apply_homography(H, pts)` 로 직접 실험해 보자.

### 4.5 점이 4개보다 많으면 — 최소제곱

현실에서는 대응점이 수십 개이고 **잡음**이 있다 (P2 체커보드, P4 특징점).
그러면 식이 미지수보다 많아서(2N > 8) 모든 식을 정확히 만족하는 해가 없다.
그때는 **오차 제곱합이 가장 작은 해** `min ‖A·h − b‖²` 를 찾는다.

```python
h = np.linalg.solve(A, b)                     # N == 4: 정확히 풀기
h = np.linalg.lstsq(A, b, rcond=None)[0]      # N > 4: 최소제곱 (N == 4 에서도 같은 답)
```

> 📚 **복습 — 연립방정식** (chap05 `19.equation.py`)
> `cv2.solve(A, b, flags=cv2.DECOMP_LU)` 로 풀었던 그것이다. numpy 의 `np.linalg.solve` 도 같은 일을 한다.

### 4.6 구현 힌트

```
1. src, dst 를 float64 (N, 2) 로 정리 (np.asarray(...).reshape(-1, 2))
2. A = zeros(2N, 8), b = zeros(2N)
3. for i, ((x, y), (u, v)) in enumerate(zip(src, dst)):
       A[2i]   = [x, y, 1, 0, 0, 0, -u*x, -u*y];  b[2i]   = u
       A[2i+1] = [0, 0, 0, x, y, 1, -v*x, -v*y];  b[2i+1] = v
4. h 를 풀고, 끝에 1 을 붙여 3×3 으로 reshape
```

### 4.7 채점과 비교

```powershell
python tools/run_tests.py p1_doc_scanner          # test_homography.py 3개 PASS
```

통과하면 `config.yaml` 에서 `impl.homography: mine` 으로 바꾸고 전체를 다시 돌린다. 결과가 그대로여야 한다.

```powershell
python p1_doc_scanner/main.py --compare
```

```
[호모그래피] 최대 원소 차이 1.819e-06
| name   | median_ms | x_slower |
| opencv | 0.003     | 1.000    |
| mine   | 0.016     | 4.836    |       ← 이 PC 기준. 행렬 하나 푸는 데 0.02ms 면 충분히 빠르다
```

### 4.8 ★ 더 해보기 — 정규화 (Hartley normalization)

A 행렬에는 1 같은 작은 값과 `u·x ≈ 120,000` 같은 큰 값이 섞여 있다. 이런 행렬은 수치적으로 불안정하다(조건수가 크다).
그래서 OpenCV 는 풀기 전에 점들을 "중심 0, 평균 거리 √2" 로 옮겨 정규화하고, 푼 다음 되돌린다.
`np.linalg.cond(A)` 를 정규화 전후로 찍어 보고, 잡음이 있는 점 30개에서 재투영 오차가 어떻게 달라지는지 재 보자.
P4 RANSAC 에서 이 함수를 수천 번 부를 때 차이가 드러난다.

<details>
<summary>▶ 정답 보기 — homography_dlt</summary>

```python
def homography_dlt(src, dst):
    src = np.asarray(src, dtype=np.float64).reshape(-1, 2)
    dst = np.asarray(dst, dtype=np.float64).reshape(-1, 2)
    n = len(src)
    if n < 4 or len(dst) != n:
        raise ValueError(f"대응점이 4쌍 이상, 같은 개수여야 합니다: src {len(src)}, dst {len(dst)}")
    A = np.zeros((2 * n, 8))
    b = np.zeros(2 * n)
    for i, ((x, y), (u, v)) in enumerate(zip(src, dst)):
        A[2 * i] = [x, y, 1, 0, 0, 0, -u * x, -u * y]
        A[2 * i + 1] = [0, 0, 0, x, y, 1, -v * x, -v * y]
        b[2 * i], b[2 * i + 1] = u, v
    h = np.linalg.solve(A, b) if n == 4 else np.linalg.lstsq(A, b, rcond=None)[0]
    return np.append(h, 1.0).reshape(3, 3)
```

</details>

---

## Step 5. 워핑 — `warp_perspective` (2일)

### 5.1 순방향 매핑은 왜 안 되나

가장 먼저 떠오르는 방법은 "원본 픽셀마다 H 로 보내서 출력에 찍기" (순방향, forward) 다. 그런데 **구멍이 난다.**

```
원본 (촘촘)          순방향으로 2배 확대한 출력
■ ■ ■ ■             ■ · ■ · ■ · ■ ·
■ ■ ■ ■      →      · · · · · · · ·     ← 아무도 안 찍은 픽셀 (구멍)
■ ■ ■ ■             ■ · ■ · ■ · ■ ·
                    · · · · · · · ·
```

100×100 을 순방향으로 2배 확대하면 200×200 출력 중 **25% 만** 채워진다 (직접 계산해 봤다).
반대로 축소하는 곳에서는 여러 원본 픽셀이 한 출력 픽셀에 겹쳐 찍힌다.

### 5.2 역방향 매핑 (inverse mapping)

순서를 뒤집는다. **출력의 모든 픽셀**에서 출발해 "너는 원본의 어디서 왔니?" 를 묻는다.

```
출력 (u, v) ──H⁻¹──→ 원본 (x, y) = (37.3, 112.6)   ← 보통 정수가 아니다
                                    │
                         주변 네 픽셀로 보간해서 값을 가져온다
```

출력의 모든 픽셀이 반드시 한 번씩 계산되므로 구멍이 없다. OpenCV 의 `warpPerspective`, `remap`, 그리고 AVM 탑뷰 렌더링이 전부 이 방식이다.

> 📚 **복습 — 양선형 보간** (chap08 `03.scaling_bilinear.py`)
> 크기 변환에서 이미 구현했다. 이번에는 좌표가 H⁻¹ 로 계산된다는 점만 다르다.

### 5.3 양선형 보간 — 숫자로 한 번

원본 좌표가 `(x, y) = (0.3, 0.6)` 이고, 주변 네 픽셀 값이 다음과 같다고 하자.

```
        x=0      x=1
y=0     10 ────── 20          fx = x − ⌊x⌋ = 0.3   (오른쪽으로 30% 지점)
         │    ●    │          fy = y − ⌊y⌋ = 0.6   (아래로 60% 지점)
y=1     30 ────── 40

① 위 줄 가로 보간:   10 × (1 − 0.3) + 20 × 0.3 = 7 + 6   = 13
② 아래 줄 가로 보간: 30 × (1 − 0.3) + 40 × 0.3 = 21 + 12 = 33
③ 세로 보간:         13 × (1 − 0.6) + 33 × 0.6 = 5.2 + 19.8 = 25
```

### 5.4 경계 처리 — 원본 밖은 0

```
 x 가 −0.4 인 경우:  왼쪽 이웃(x=−1)은 원본 밖 → 0 으로 보고, 오른쪽 이웃(x=0)과 섞는다
                     → 경계가 부드럽게 검은색으로 이어진다 (OpenCV BORDER_CONSTANT 와 같다)
 x 가 −1 보다 작으면: 네 이웃이 모두 밖 → 0
```

if 문 없이 처리하는 요령: 원본 둘레에 **0 으로 된 테두리를 1픽셀** 붙인(padding) 배열을 만들고 거기서 읽는다.
좌표는 +1 만큼 밀어서 읽으면 된다.

### 5.5 먼저 for 문으로, 그다음 벡터화

**1단계 — for 문 버전** (이해용, 채점은 안 함). 한 픽셀에서 일어나는 일이 그대로 보인다.

```python
for v in range(h):
    for u in range(w):
        x, y, s = Hinv @ [u, v, 1]
        x, y = x / s, y / s
        x0, y0 = int(np.floor(x)), int(np.floor(y))
        fx, fy = x - x0, y - y0
        top    = pixel(x0, y0)     * (1 - fx) + pixel(x0 + 1, y0)     * fx
        bottom = pixel(x0, y0 + 1) * (1 - fx) + pixel(x0 + 1, y0 + 1) * fx
        out[v, u] = top * (1 - fy) + bottom * fy
```

200×150 출력에 **약 290ms**. 3000×2000 이면 1분이 넘는다.

**2단계 — 벡터화.** "픽셀 하나" 대신 "모든 픽셀을 한꺼번에" 계산한다. shape 을 따라가는 게 핵심이다.

| 변수 | 만드는 법 | shape (출력 h×w, 채널 c) |
|---|---|---|
| `u, v` | `np.meshgrid(np.arange(w), np.arange(h))` | 각각 (h, w) |
| `uv1` | `np.stack([u.ravel(), v.ravel(), ones])` | (3, h·w) |
| `xyw` | `np.linalg.inv(H) @ uv1` | (3, h·w) |
| `x, y` | `xyw[0] / xyw[2]`, `xyw[1] / xyw[2]` | 각각 (h·w,) |
| `x0, fx` | `np.floor(x)`, `x − x0` | (h·w,) |
| `fx[:, None]` | 채널 방향으로 브로드캐스팅하려고 축 추가 | (h·w, 1) |
| `padded[yi, xi]` | **팬시 인덱싱** — 정수 배열 두 개로 한 번에 h·w 개 픽셀 읽기 | (h·w, c) |
| 결과 | 보간 → `reshape(h, w, c)` | (h, w, c) |

그레이 입력 (h, w) 도 받아야 하므로, 처음에 `img.reshape(H, W, -1)` 로 (h, w, 1) 로 통일하고 마지막에 되돌리면 편하다.

### 5.6 왜 OpenCV 와 최대 4 만큼 다를까 — 실험

채점기는 OpenCV 결과와 **완전히 같기를 요구하지 않는다** (최대 6, 평균 0.2 이하). 이유를 직접 확인해 보자.

OpenCV 는 속도를 위해 원본 좌표를 **1/32 픽셀 단위로 반올림**해서 정수 연산으로 보간한다 (`INTER_BITS = 5`).
좌표 오차는 최대 1/64 픽셀이다. 그런데 글자 테두리처럼 한 픽셀 사이에 밝기가 255 차이 나는 곳에서는
`255 × 1/64 ≈ 4` 만큼 값이 달라질 수 있다.

검증 실험: 내 좌표를 직접 1/32 단위로 반올림한 뒤 `cv2.remap` 에 넣으면 OpenCV 결과와 **차이가 0** 이 된다.

```python
xq = np.round(x * 32) / 32          # 1/32 픽셀 단위로 반올림
yq = np.round(y * 32) / 32
same = cv2.remap(img, xq.reshape(h, w).astype(np.float32), yq.reshape(h, w).astype(np.float32),
                 cv2.INTER_LINEAR)
# → cv2.warpPerspective 결과와 max diff 0
```

이런 걸 **"차이를 설명할 수 있다"** 고 한다. 현업에서 "직접 구현이 라이브러리와 미세하게 다르다" 는 보고를 할 때 꼭 필요한 능력이다.

### 5.7 채점과 비교

```powershell
python tools/run_tests.py p1_doc_scanner          # test_warp.py 4개 PASS
python p1_doc_scanner/main.py --compare
```

```
[비교] 워핑 mine vs opencv  shape=(520, 381, 3)  → 다름 (허용 오차 1)
       최대 차이 2, 평균 차이 0.08781, PSNR 58.59 dB
       허용 오차를 넘는 원소 663 / 594,360 (0.112%)
| opencv | 0.648  | 1.000  |
| mine   | 37.268 | 57.538 |        ← 벡터화해도 약 60배 느리다
```

`results/compare/warp_diff.png` 를 열어 보자. 차이가 **글자 테두리에만** 몰려 있으면 §5.6 의 반올림 때문이다.
면 전체에 퍼져 있으면 보간식이나 좌표 순서가 틀린 것이다.

OpenCV 가 60배 빠른 이유: 정수 고정소수점 연산, SIMD(한 명령으로 픽셀 여러 개 처리), 멀티스레드,
그리고 (h·w)짜리 거대한 임시 배열을 만들지 않고 한 줄씩 처리하기 때문이다. **원리는 같다.**

통과하면 `impl.warp: mine` 으로 바꾸고 전체를 다시 돌려 결과가 그대로인지 확인한다.

<details>
<summary>▶ 정답 보기 — warp_perspective (벡터화)</summary>

```python
def warp_perspective(img, H, size):
    w, h = size
    src = img.reshape(img.shape[0], img.shape[1], -1).astype(np.float32)     # 그레이도 (h, w, 1) 로 통일
    sh, sw, ch = src.shape
    padded = np.zeros((sh + 2, sw + 2, ch), np.float32)                     # 테두리 1픽셀 = 원본 바깥 = 0
    padded[1:-1, 1:-1] = src

    u, v = np.meshgrid(np.arange(w), np.arange(h))                          # 출력 격자, 각각 (h, w)
    uv1 = np.stack([u.ravel(), v.ravel(), np.ones(u.size)])                 # (3, h*w)
    xyw = np.linalg.inv(H) @ uv1                                            # 출력 → 원본 (역매핑)
    x, y = xyw[0] / xyw[2], xyw[1] / xyw[2]

    valid = (x >= -1) & (x < sw) & (y >= -1) & (y < sh)                     # 네 이웃 중 하나라도 원본 안
    x, y = np.where(valid, x, -1), np.where(valid, y, -1)                   # 바깥은 패딩(0)만 보게
    x0, y0 = np.floor(x), np.floor(y)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    xi, yi = x0.astype(np.int64) + 1, y0.astype(np.int64) + 1               # 패딩 좌표로 +1

    top = padded[yi, xi] * (1 - fx) + padded[yi, xi + 1] * fx
    bottom = padded[yi + 1, xi] * (1 - fx) + padded[yi + 1, xi + 1] * fx
    out = top * (1 - fy) + bottom * fy
    out[~valid] = 0
    out = np.clip(np.round(out), 0, 255).astype(img.dtype).reshape(h, w, ch)
    return out[..., 0] if img.ndim == 2 else out
```

</details>

<details>
<summary>▶ 참고 — for 문 버전 전체 (이해용)</summary>

```python
def warp_perspective_loop(img, H, size):
    w, h = size
    src = img.reshape(img.shape[0], img.shape[1], -1).astype(np.float32)
    sh, sw, ch = src.shape
    out = np.zeros((h, w, ch), np.float32)
    Hinv = np.linalg.inv(H)

    def pixel(xx, yy):                       # 원본 바깥이면 0
        if 0 <= xx < sw and 0 <= yy < sh:
            return src[yy, xx]
        return np.zeros(ch, np.float32)

    for v in range(h):
        for u in range(w):
            x, y, s = Hinv @ [u, v, 1]       # 출력 (u, v) → 원본 (x, y)
            x, y = x / s, y / s
            x0, y0 = int(np.floor(x)), int(np.floor(y))
            fx, fy = x - x0, y - y0
            top = pixel(x0, y0) * (1 - fx) + pixel(x0 + 1, y0) * fx
            bottom = pixel(x0, y0 + 1) * (1 - fx) + pixel(x0 + 1, y0 + 1) * fx
            out[v, u] = top * (1 - fy) + bottom * fy
    out = np.clip(np.round(out), 0, 255).astype(img.dtype)
    return out[..., 0] if img.ndim == 2 else out
```

벡터화 버전과 결과가 완전히 같다 (max diff 0). `benchmark` 로 두 버전의 속도를 직접 재서 README 에 적어 보자.

</details>

---

## Step 6. 스캔 효과 — `adaptive_threshold` (반나절~1일)

### 6.1 전역 임계값은 그림자에 진다

> 📚 **복습 — 이진화** (chap06 `18.thresholding.py`)
> `cv2.threshold(gray, T, 255, THRESH_BINARY)`: 모든 픽셀에 **같은 기준 T**. Otsu 는 T 를 히스토그램으로 자동으로 정한다.

펼친 종이에 그림자가 지면, 그늘진 쪽 **종이** 가 밝은 쪽 **글자** 보다 어두울 수 있다. 그러면 어떤 T 로도 둘을 나눌 수 없다.

```
밝기
250 ┤■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■━━━━━━━━━━━━━━━━━━━━━━━━━━━━  종이
    │                                             ━━━━━━━━━━━━━━━━━━━━━━━  (그늘: 점점 어두워짐)
120 ┤─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  전역 T
    │                                                         ━━━━━━━━━━━  그늘진 종이 < T → 검게 칠해짐 ✗
 40 ┤ ▼글자  ▼글자  ▼글자                          ▼글자           ▼글자
    └───────────────────────────────────────────────────────────────────→ 가로 위치
```

**적응형 이진화**는 픽셀마다 **자기 주변의 평균**을 기준으로 삼는다. 그늘진 곳은 기준도 같이 내려간다.

```
규칙:  픽셀 > (주변 block_size × block_size 평균 − C)  이면 255 (흰색), 아니면 0
```

| 파라미터 | 의미 | 정하는 요령 |
|---|---|---|
| `block_size` | 주변 범위 (홀수) | **글자보다 충분히 커야** 한다. 글자 크기 정도면 글자 속이 비어 버린다 |
| `C` | 평균에서 얼마나 빼나 | 클수록 흰색이 늘어 깔끔하지만 흐린 글자가 사라진다 |

### 6.2 주변 평균을 빠르게 — 두 가지 방법

**방법 A (먼저):** `cv2.blur(gray, (k, k), borderType=cv2.BORDER_REPLICATE)` 가 바로 k×k 평균이다. 이걸로 먼저 규칙을 완성하자.

**방법 B (직접 구현):** **적분 영상(integral image, summed-area table)**.
`ii[y, x]` = 왼쪽 위 (0,0) 부터 (y−1, x−1) 까지의 **누적 합**. `np.cumsum` 을 세로·가로로 두 번 하면 된다.

```
원본 m                   적분 영상 ii (맨 위 한 줄, 맨 왼쪽 한 줄은 0)
 1  2  3  4               0   0   0   0   0
 5  6  7  8               0   1   3   6  10
 9 10 11 12               0   6  14  24  36
13 14 15 16               0  15  33 [54] 78
                          0  28  60  96 136

가운데 2×2 (6, 7, 10, 11) 의 합 = 34
  = ii[3,3] − ii[1,3] − ii[3,1] + ii[1,1]
  =   54    −   6     −   15    +   1      = 34 ✓
```

```
    ┌──────┬──────┐
    │  D   │  B   │      구하려는 칸 = 전체(ii[3,3]) − 위쪽 띠(ii[1,3]) − 왼쪽 띠(ii[3,1])
    ├──────┼──────┤                    + 두 번 빠진 모퉁이(ii[1,1])
    │  C   │ 구하려 │
    │      │ 는 칸  │
    └──────┴──────┘
```

블록이 3×3 이든 101×101 이든 **덧셈·뺄셈 4번**이면 합이 나온다. 블록 크기와 상관없이 픽셀당 계산량이 같다.
가장자리는 `np.pad(gray, r, mode="edge")` 로 가장자리 픽셀을 복제해서 붙인 뒤 계산하면 된다 (= BORDER_REPLICATE).

### 6.3 OpenCV 와 픽셀 1개가 다를 수 있다 — 왜?

적분 영상으로 구한 평균은 36.6 같은 실수인데, OpenCV 는 평균을 **정수로 반올림**(37)한 뒤 비교한다.

| | 기준 (평균 − C) | `gray = 27` 판정 |
|---|---|---|
| 내 구현 | 36.6 − 10 = **26.6** | 27 > 26.6 → **흰색** |
| OpenCV | 37 − 10 = **27** | 27 > 27 → **검정** |

이렇게 픽셀이 기준선에 아슬아슬하게 걸린 경우에만 판정이 갈린다. 실제 스캔본에서 재 보니 200,000 픽셀 중 **1개** 가 달랐고,
`mean = np.round(mean)` 한 줄을 넣으면 **0개** 가 됐다. 채점기는 0.5% 미만이면 통과다.

### 6.4 채점과 비교

```powershell
python tools/run_tests.py p1_doc_scanner          # test_enhance.py 3개 PASS
python p1_doc_scanner/main.py --compare
```

`test_beats_global_threshold_under_shadow` 는 "전역 Otsu 는 그늘에서 실패하지만 내 구현은 성공한다" 를 확인한다.
통과하면 `impl.threshold: mine`. **이제 `impl` 이 전부 `mine` 이다 — OpenCV 는 검출(Step 2)에만 쓰인다.**

<details>
<summary>▶ 정답 보기 — adaptive_threshold (적분 영상)</summary>

```python
def adaptive_threshold(gray, block_size=31, C=10):
    k, r = block_size, block_size // 2
    padded = np.pad(gray.astype(np.float64), r, mode="edge")                # BORDER_REPLICATE
    ii = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1))               # 적분 영상 (맨 위·왼쪽 0 한 줄)
    ii[1:, 1:] = padded.cumsum(axis=0).cumsum(axis=1)
    box_sum = ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k]          # 각 픽셀 중심 k×k 합
    mean = box_sum / (k * k)
    return np.where(gray > mean - C, 255, 0).astype(np.uint8)
```

`ii[k:, k:]` 같은 슬라이싱 한 줄이 "모든 픽셀에 대해 §6.2 의 공식" 을 한꺼번에 계산한다.
패딩 후 크기가 (H+2r, W+2r) 이므로 ii 는 (H+2r+1, W+2r+1), `ii[k:, k:]` 는 정확히 (H, W) 가 된다 (k = 2r+1).

</details>

---

## Step 7. 수동 보정과 실패 분석 (1일)

### 7.1 자동이 실패하면 사람이 — `--manual`

```powershell
python p1_doc_scanner/main.py --manual
```

검출에 실패한 사진에서 창이 뜨고, 마우스로 네 점을 찍으면 그 점으로 펼친다. 결과표의 `how` 열이 `manual` 이 된다.
실제 스캐너 앱도 "자동 → 실패하면 사람이 조정" 구조다. **자동화는 100% 가 아니라는 전제로 설계한다.**

> 📚 **복습 — 마우스 이벤트** (reference 03, 04 가상광고판 / chap04 `04.event_mouse.py`, chap08 `11.perspective_event.py`)
> `cv2.setMouseCallback(창, 함수)` 로 클릭 좌표를 받는다. [scanner/ui.py](scanner/ui.py) 를 열어서 읽어 보자.
> 화면에 맞게 줄여 보여주고 원본 좌표로 되돌리는 부분(÷ scale)이 이번 프로젝트의 축소 → 검출 → 복원 흐름과 같다.

### 7.2 실패 분석 — 결과표와 모자이크로

`results/summary.csv` 를 엑셀로 열고 `issues` 열로 정렬해 보자. 합성 데이터 기본 설정에서는 대략 이런 결과가 나온다.

| 파일 | found | issues |
|---|---|---|
| syn_012 | X | clutter |
| syn_013 | X | clutter+low_contrast |
| syn_014 | X | low_contrast+occluder |
| syn_017 | X | clutter |
| syn_016 | O | shadow |

**예시 분석 — syn_017 (포스트잇).** `results/stages/syn_017.jpg` 를 열면:

1. 원본: 노란 포스트잇이 종이 왼쪽 위 모서리에 맞닿아 있다
2. 블러(그레이): **노랑과 흰색이 거의 같은 밝기의 회색**이 됐다
3. Canny: 포스트잇과 맞닿은 부분의 종이 테두리 엣지가 **끊겼다**
4. 윤곽선: 테두리가 닫히지 않아 넓이가 큰 윤곽선이 없다 → 후보가 하나도 없음 → 실패

원인: **그레이 변환에서 색 정보가 사라졌다.** 노랑(B 채널이 낮음)과 흰색(B 채널이 높음)은 B 채널에서는 차이가 크다.

이런 식으로 실패한 사진마다 **어느 단계에서, 왜** 망가졌는지 README 의 실패 분석 표에 적는다.

| 실패 유형 | 장수 | 망가진 단계 | 원인 | 대책 후보 |
|---|---|---|---|---|
| 포스트잇 | 2 | Canny | 그레이에서 노랑≈흰색 | 컬러 엣지 |
| … | | | | |

### 7.3 개선하기 — 최소 두 가지를 시도하고 숫자로 비교

| 아이디어 | 복습 챕터 | 기대 효과 | 부작용 |
|---|---|---|---|
| **컬러 Canny** — B, G, R 각각 Canny 후 OR | chap07 `13.edge_color_canny.py` | 색은 다르고 밝기는 비슷한 경계 검출 | 색 잡음 엣지 증가 |
| 닫힘 커널 키우기 | chap07 `16` | 끊긴 테두리 연결 | 옆 물체와 합쳐짐 |
| 엣지 대신 **영역**으로 — 채도(S)가 낮고 밝은 영역 = 종이 | chap06 `15.convert_hsv.py`, `17.hue_threshold.py` | 질감 배경에 강함 | 흰 책상에서 실패 |
| 근사 전에 `cv2.convexHull` | (새 함수) | 펜에 가려 오목해진 윤곽선 복구 | 볼록 껍질이 종이보다 커질 수 있음 |
| 4각형이 안 나오면 `cv2.minAreaRect` 로 대체 | (새 함수) | 항상 사각형이 나옴 | 원근을 무시한 직사각형 → 오차 큼 |
| 여러 파라미터 세트를 차례로 시도 | — | 한 세트 실패 시 다른 세트 | 느려짐, 엉뚱한 사각형 위험 |

**규칙: 개선은 반드시 "전후 숫자" 로 말한다.** 그리고 **보통 난이도 사진이 나빠지지 않았는지**(회귀) 꼭 확인한다.
어려운 사진 2장을 살리고 쉬운 사진 3장을 망가뜨리는 경우가 흔하다.

```
| 버전              | 합성 검출률 | 합성 평균 오차 | 실사 검출률 | 실사 평균 오차 |
| 기준선            | 80%        | 1.1px         |            |               |
| + 컬러 Canny      |            |               |            |               |
| + convexHull      |            |               |            |               |
```

---

## Step 8. 마무리 — 평가와 보고서 (반나절)

### 8.1 최종 실행

```powershell
python p1_doc_scanner/main.py --input p1_doc_scanner/data/synthetic
python p1_doc_scanner/main.py --input p1_doc_scanner/data/raw
```

### 8.2 숫자 읽는 법

| 지표 | 뜻 | 주의 |
|---|---|---|
| 검출률 (`found`) | 사각형을 찾았나 | 엉뚱한 사각형을 찾아도 O 다 → 그래서 오차가 필요 |
| 평균 오차 (`err_mean_px`) | 네 꼭짓점이 정답에서 평균 몇 px 떨어졌나 (원본 해상도) | 4000px 사진의 10px 와 1000px 사진의 10px 는 무게가 다르다 |
| 최대 오차 (`err_max_px`) | 가장 많이 틀린 꼭짓점 | 평균은 괜찮은데 한 점만 크게 틀리면 결과가 찌그러진다 |
| 성공 (`success`) | 평균 오차 ≤ `eval.success_px` (기본 10px) | 기준은 내가 정한 것이다. 왜 10px 인지 README 에 근거를 적자 |
| 시간 (`ms`) | 사진 한 장 처리 시간 | `impl: mine` 이면 워핑 때문에 느려진다 |

### 8.3 README 작성

[README.md](README.md) 의 빈칸을 채운다. 특히 다음 세 가지:

1. **결과표** — 합성/실사 각각 검출률, 평균 오차. 기준선과 개선 후 비교
2. **실패 분석** — 유형별 장수와 원인. 대표 실패 모자이크 1~2장
3. **직접 구현 vs OpenCV** — `--compare` 결과 (차이, 속도)와 **차이가 나는 이유** (§5.6, §6.3)

### ✅ P1 완료 체크리스트

- [ ] 채점기 전부 PASS (`python tools/run_tests.py p1_doc_scanner`)
- [ ] `impl` 이 전부 `mine` 인 상태로 전체 실행 성공
- [ ] 합성 + 실사 결과표 (기준선 → 개선 후)
- [ ] 실패 유형 분석표
- [ ] 개선 아이디어 2개 이상 시도, 전후 숫자 비교
- [ ] `--compare` 결과와 차이의 원인 설명
- [ ] README 의 "배운 것" 세 줄 이상

---

## Step 9. ★ 복습 보너스

### 9.1 엣지 연산자 비교 (chap07 `03`~`07`)

`find_document_quad` 에 `edge` 파라미터를 추가해서 Canny 대신 다른 연산자를 쓸 수 있게 만든다.

| `edge` | 방법 | 이진화 |
|---|---|---|
| `canny` | 지금 그대로 | (Canny 내부) |
| `sobel` | `cv2.Sobel` x, y → `cv2.magnitude` | 크기 > 임계값 |
| `prewitt` | 커널 `[[-1,0,1]]×3` 을 `cv2.filter2D` 로 | 크기 > 임계값 |
| `roberts` | 2×2 대각선 커널 | 크기 > 임계값 |
| `laplacian` | `cv2.Laplacian` | 절댓값 > 임계값 |
| `dog` | 가우시안 두 개의 차 (σ1 < σ2) | 절댓값 > 임계값 |

`config.yaml` 의 `detect.edge` 만 바꿔 가며 돌리고, **연산자별 검출률·평균 오차** 표를 만든다.
"교과서에서 Canny 가 좋다고 했다" 가 아니라 **내 데이터에서 숫자로** 확인하는 게 목적이다.

### 9.2 글자 기울기 보정 (chap10 `02.correct_object.py`)

수동으로 찍은 꼭짓점이 조금 틀리면 스캔본이 1~2° 기울어진다. 스캔본에서 Hough 직선(글자 줄)의
평균 각도를 구해 그만큼 회전시키는 후처리를 붙여 보자. 정답 꼭짓점에 일부러 ±5px 잡음을 섞어 기울어진 스캔본을 만든 뒤,
보정 전후의 기울기를 비교한다.

### 9.3 검출 해상도 실험

`input.max_side` 를 500 / 1000 / 2000 으로 바꿔 가며 검출률·오차·시간을 비교한다.
"작게 줄이면 빠르고 잔무늬가 줄지만, 꼭짓점 정밀도는 떨어진다" 는 트레이드오프를 숫자로 보자.
`cv2.cornerSubPix` 로 원본 해상도에서 꼭짓점을 다듬는 방법도 있다 (P2 에서 본격적으로 쓴다).

---

## 부록. 자주 만나는 에러

| 증상 / 에러 메시지 | 원인 | 해결 |
|---|---|---|
| `(-215:Assertion failed) src.checkVector(2, CV_32F) == 4` | `getPerspectiveTransform` 에 float64 나 int 배열을 넣음 | `.astype(np.float32)` |
| `(-215:Assertion failed) ksize.width > 0 && ksize.width % 2 == 1` | GaussianBlur 커널이 짝수 | 홀수로. 튜너 범위를 `[1, 31, 2]` 로 |
| 결과가 90° 돌아가 있거나 거울상 | 꼭짓점 순서 오류 | Step 3 채점기 확인, `results/stages` 의 TL/TR 라벨 확인 |
| 결과가 나비넥타이처럼 꼬임 | 두 꼭짓점이 바뀜 | 위와 같음 |
| `IndexError` 가 워핑에서 | 원본 밖 좌표를 그대로 인덱스로 씀 | §5.4 패딩 + valid 처리 |
| 출력 shape 이 (w, h) 로 뒤집힘 | `size=(w, h)` 와 `shape=(h, w)` 혼동 | OpenCV 함수 인자는 (가로, 세로), numpy shape 은 (세로, 가로) |
| 밝은 부분이 검게 변함 | uint8 끼리 더하다가 overflow (250 + 10 = 4) | float32 로 계산 후 마지막에 clip + astype |
| 큰 사각형이 보이는데 못 찾음 | 테두리 엣지가 끊겨 윤곽선 넓이 ≈ 0 | §2.4, 닫힘 커널, 블러 조정 |
| `ValueError: too many values to unpack` (findContours) | OpenCV 3.x 예제 코드 | 4.x 는 `contours, hierarchy = ...` |
