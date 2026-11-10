# chap06 요약: 핵심 API와 핵심 개념

이 파일은 `01`~`07` 문서와 부록의 **핵심만 뽑은 치트시트**예요. 설명이 필요하면 각 절 제목의 링크로 원문을 보세요.
(원문 `01`~`07`은 세션 기록에서 추출한 것이고, 이 파일은 직접 정리한 거예요.)

## 0. 한눈에 보기

> **모든 연산은 화소 하나의 값 `x`를 새 값 `y`로 보내는 함수 `y = f(x)`를 어떻게 설계하느냐**

| 연산 | f(x)의 모양 | f를 정하는 방법 | 문서 |
|---|---|---|---|
| 영상 반전 | `255 − x` | 고정 | [01](01-pixel-access-lut.md) |
| 밝기, 대비 | `a·x + b` | 사람이 a, b 지정 | [03](03-arithmetic-contrast.md) |
| 스트레칭 | `(x − low)·255/(high − low)` | 히스토그램 양 끝으로 자동 | [05](05-stretching-equalization.md) |
| 평활화 | `cdf(x)/N × 255` | 히스토그램 전체로 자동 | [05](05-stretching-equalization.md) |
| CMY 변환 | 채널별 `255 − x` | 고정 | [06](06-color-spaces.md) |
| 이진화 | 계단 하나 | 사람(트랙바) 또는 오츠로 자동 | [07](07-thresholding.md) |

### 세 가지 불변 규칙 (이것만 알아도 대부분의 버그를 피해요)

1. **좌표 순서**: numpy 인덱싱과 `.shape`는 **(y, x) / (h, w)**, OpenCV 그리기 함수의 점은 **(x, y)**, `cv2.resize` 크기는 **(w, h)**
2. **uint8 범위**: 0~255를 넘으면 numpy는 **한 바퀴 돌고**(300 → 44), OpenCV 함수는 **끝에서 멈춰요**(포화, 300 → 255)
3. **뷰와 복사**: 슬라이싱 결과와 함수 인자는 **원본과 같은 메모리**를 공유해요. 지키려면 `.copy()`

---

## 1. [01-pixel-access-lut.md](01-pixel-access-lut.md): 화소 접근과 LUT

### 핵심 API

| API | 사용법 | 메모 |
|---|---|---|
| `ndarray.shape` / `.dtype` | `img.shape → (450, 360)`, `img.dtype → uint8` | 이미지는 보통 `(H, W)` 또는 `(H, W, 3)`의 `uint8` |
| `arr[i, j]` | `k = mat[i, j]; mat[i, j] = k * 2` | `mat[i][j]`보다 한 번에 찾아가는 `mat[i, j]`가 정석 |
| `arr.item(i, j)` | `mat.item(i, j)` → 파이썬 `int` | `mat[i, j]`는 `numpy.int64`를 돌려줘서 조금 더 느려요 |
| ~~`arr.itemset()`~~ | — | **NumPy 2.0에서 삭제됨** → `mat[i, j] = v` 사용 |
| `np.arange(10).reshape(2, 5)` | 1차원 → 2행 5열 | `reshape`은 복사하지 않고 보는 방식만 바꿈 |
| `np.zeros(shape, dtype)` | `np.zeros(img.shape[:2], img.dtype)` | 결과를 담을 빈 도화지 |
| **`lut[image]`** (팬시 인덱싱) | `lut = np.array([255 - i for i in range(256)], np.uint8); out = lut[image]` | **표[이미지]** 순서. 결과 shape는 `image`를 따라가요 |
| **`cv2.LUT(src, lut)`** | `cv2.LUT(image, lut)` | `lut`는 길이 256 `uint8`. 가장 빠름 |
| `cv2.subtract(255, img)` | 반전 | `255 - img`와 같은 결과 |
| 브로드캐스팅 | `255 - image` | 숫자 하나를 표 전체에 "그런 척" 적용 |

### 핵심 개념

- 화소값은 256가지뿐이라서 **계산을 미리 해 둔 정답표(LUT)**를 만들어 두고 찾기만 하면 f가 아무리 복잡해도 속도가 같아요. 비싼 계산은 256번만 해요.
- LUT = 변환 곡선의 숫자 버전 (`lut[x]` = x를 넣었을 때의 답)
- 반전 `255 − x`를 다섯 방법으로 구현하면 결과는 **모두 같고 속도만 달라요**.

| 방법 | 시간 (162,000화소) |
|---|---:|
| 이중 for문 | 22.81 ms |
| `item()` for문 | 16.12 ms |
| `lut[image]` | 0.23 ms |
| `cv2.LUT` / `cv2.subtract` / `255 - image` | **0.07 ms** (약 330배) |

- for문이 느린 이유는 반복마다 객체 포장, 타입 검사, 함수 호출 같은 잡일을 하기 때문이에요. 실전은 **벡터 연산 또는 LUT**.
- 속도는 **여러 번 재서 최솟값**을 봐야 해요 (첫 호출은 준비 작업 때문에 느려요).

---

## 2. [02-pixel-value-quantization.md](02-pixel-value-quantization.md): 화소값과 양자화

### 핵심 API

| API | 사용법 | 메모 |
|---|---|---|
| `cv2.imread(path, cv2.IMREAD_GRAYSCALE)` | `img = cv2.imread("images/pixel.jpg", cv2.IMREAD_GRAYSCALE)` | 읽기 실패하면 `None` → 반드시 검사 |
| 슬라이싱 (ROI) | `roi = image[y:y+h, x:x+w]` | `a:b`는 **b 미포함**. 결과 shape `(h, w)`. **뷰**라서 원본과 메모리 공유 |
| `//` 정수 나눗셈 | `j // 20 * 10` | 계단(양자화)을 만드는 도구 |
| `cv2.rectangle(img, (x, y, w, h), color, thickness)` | `cv2.rectangle(image, (x,y,w,h), 255, 1)` | 점은 (x, y). 흑백은 색이 숫자 하나 |
| `np.zeros((h, w), np.uint8)` | `np.zeros((50, 512), np.uint8)` | 인자 순서 (세로, 가로) |
| `.copy()` | `roi = image[...].copy()` | 원본을 지킬 때 |

### 핵심 개념

- 흑백 화소값 = 밝기 (0 검정 ~ 255 흰색). 컬러 → 흑백은 `Y = 0.299R + 0.587G + 0.114B`.
- **양자화**: `(x // 간격) × 높이`. 256단계는 매끈하고 26단계는 띠가 보여요. 이후 히스토그램의 bin(Part 4)과 이진화(Part 7, 2단계)로 이어져요.
- **경계(edge)** = 이웃 화소값이 크게 뛰는 곳.
- 식에 `i`(행)가 없으면 모든 행이 같아져서 세로 줄무늬가 돼요.
- `uint8`에 256 이상 넣기: 파이썬 `int`는 `OverflowError`, `np.int64`는 조용히 한 바퀴(300 → 44).
- ROI를 만든 뒤 원본에 그리면 ROI도 같이 바뀌어요 (뷰). 출력을 먼저 하고 그려야 해요.

---

## 3. [03-arithmetic-contrast.md](03-arithmetic-contrast.md): 산술 연산, 합성, 대비

### 핵심 API

| API | 사용법 | 메모 |
|---|---|---|
| `cv2.add(a, b)` / `cv2.subtract(a, b)` | `cv2.add(image, 200)` | **포화**(0과 255에서 멈춤) |
| `image + 100` / `image - 100` (numpy) | | **모듈로**(한 바퀴 돎): `200+100=44`, `0-100=156` |
| 안전한 numpy 덧셈 | `np.clip(img.astype(np.int16) + 100, 0, 255).astype(np.uint8)` | 큰 자료형으로 올림 → 자름 → 되돌림 |
| `cv2.addWeighted(s1, a, s2, b, gamma)` | `cv2.addWeighted(i1, 0.6, i2, 0.7, 0)` | `sat(s1·a + s2·b + gamma)`, 반올림 |
| `cv2.scaleAdd(s1, alpha, s2)` | `cv2.scaleAdd(image, 2.0, noimage)` | `s1·alpha + s2`, 반올림 |
| `cv2.mean(img)[0]` | 평균 밝기 | 항상 4칸 튜플(흑백은 첫 칸만 의미) |
| `np.clip(x, 0, 255)` | | float 결과를 자를 때 |
| `.astype("uint8")` | | 소수점 **버림** (OpenCV는 반올림) |
| `img.std()` | 표준편차 | 대비를 숫자로 나타냄 |

### 핵심 공식

$$y = a\,x + b \qquad (a = \text{대비},\ b = \text{밝기})$$

$$y = m + a\,(x - m) = a\,x + (1 - a)\,m \qquad (m = \text{평균, 평균 기준 대비})$$

- 평균 기준 대비는 `addWeighted(image, a, noimage, 0, (1 - a) * m)`. 평균 화소는 어떤 a를 써도 그대로예요.
- `noimage`(전부 0인 이미지)는 두 장을 받는 함수에 한 장만 쓰려고 넣는 더미예요.

### 핵심 개념과 함정

- `uint8 × 소수` → **float64로 자동 승격**돼서 포화가 일어나지 않아요 → 직접 `np.clip(...).astype("uint8")` 필요
- `addWeighted`와 직접 구현이 1씩 다른 이유 = **반올림 vs 버림** (45% 화소)
- `((img1 + img2) / 2)`는 `img1 + img2`가 uint8로 먼저 돌아서 틀려요. `addWeighted(img1, 0.5, img2, 0.5, 0)`를 쓰세요.
- `α + β = 1`이면 순수 블렌딩, `> 1`이면 밝아지고, `< 1`이면 어두워져요.
- ⚠️ `06.contrast.py`의 dst4(`-avg`)는 받침점이 평균의 절반이라 엄밀히는 `-m`이어야 해요.
- `06`이 저장한 `dst.jpg`(JPEG라 14~76)가 Part 5 스트레칭의 입력이에요. 값을 보존하려면 `.png`.

---

## 4. [04-histogram.md](04-histogram.md): 히스토그램

### 핵심 API

| API | 사용법 | 메모 |
|---|---|---|
| **`cv2.calcHist(images, channels, mask, histSize, ranges)`** | `cv2.calcHist([img], [0], None, [32], [0, 256])` | 전부 **리스트**로 감쌈. 결과 `(N, 1) float32`. mask가 0이 아닌 화소만 셈 |
| `np.histogram(img, bins)` | `np.histogram(img, np.arange(0, 257, 8.0))` | bin **경계값 N+1개**를 받음. 결과 `(N,) int64` |
| `cv2.normalize(src, dst, 0, h, cv2.NORM_MINMAX)` | `cv2.normalize(hist, hist, 0, 200, cv2.NORM_MINMAX)` | `(v−min)/(max−min)·h`. `dst`에 `src`를 넣으면 **원본을 덮어씀** |
| `cv2.rectangle(img, (x, 0, w, h), 0, cv2.FILLED)` | 막대 그리기 | 높이 0이면 아무것도 안 그려짐 |
| `cv2.flip(img, 0)` | 상하 반전 | `0` 상하, `1` 좌우, `-1` 둘 다 |
| `arr.flat` | `for h in hist.flat:` | 2차원을 한 줄로 펼쳐 순회 |
| `cv2.cvtColor(img, cv2.COLOR_BGR2HSV)` | Hue 채널은 `[:, :, 0]` | H는 0~179 |
| `cv2.inRange(hsv, lo, hi)` | `cv2.inRange(hsv, (0, 60, 30), (180, 255, 255))` | 마스크를 만들어 `calcHist`의 mask로 |

### 핵심 공식

$$\text{bin} = \left\lfloor \frac{x}{\text{gap}} \right\rfloor,\qquad \text{gap} = \frac{256}{\text{bin 개수}}$$

- 범위는 `[0, 256]`처럼 **끝 미포함**이에요 (`[0, 255]`로 쓰면 255가 빠져요).
- 직접 구현, `cv2.calcHist`, `np.histogram`의 결과는 **완전히 같고**, 합계 = 화소 수예요.

### 핵심 개념과 함정

- 히스토그램은 **위치 정보를 버리고 분포만** 남겨요.
- 모양으로 진단: 왼쪽에 몰림 = 어두움, 오른쪽 = 밝음, 좁게 몰림 = 저대비, 양 끝 = 고대비·포화, **쌍봉 = 물체/배경 분리 가능**.
- 그리기 순서: 흰 도화지 → `normalize` → 막대 → `flip`. 이미지 y축은 아래로 증가해서 flip이 필요해요.
- `NORM_MINMAX`는 **최솟값 bin을 0으로** 만들어서 막대가 안 보여요.
- ⚠️ `Common/histogram.py`의 `enumerate(hist)` → `int(배열)`은 DeprecationWarning (미래 에러). `.flat` 사용.
- **Hue 함정**: OpenCV H = 각도/2 (0~179). **회색·흰색은 H = 0(빨강)**으로 나와서 채도 낮은 화소는 mask로 빼야 해요.

---

## 5. [05-stretching-equalization.md](05-stretching-equalization.md): 스트레칭과 평활화

### 핵심 API

| API | 사용법 | 메모 |
|---|---|---|
| **`cv2.LUT(image, lut)`** | `cv2.LUT(image, idx.astype('uint8'))` | 두 방법 모두 최종 적용 단계 |
| `cv2.equalizeHist(gray)` | `dst = cv2.equalizeHist(image)` | **흑백(1채널) 전용** |
| `np.cumsum(hist)` | 누적합 | for문 누적을 한 줄로 |
| `np.abs(bias - i)` | `search_value_idx`의 양방향 탐색 트릭 | bias 0 = 앞에서, bias 63 = 뒤에서 |
| `arr[a:b] = v` | `idx[0:int(low)] = 0; idx[int(high+1):] = 255` | LUT 양 끝 자르기 |

### 핵심 공식

$$\text{스트레칭: } y = \frac{(x - \text{low})\times 255}{\text{high} - \text{low}}$$

$$\text{평활화: } y = \frac{\text{cdf}(x)}{N}\times 255 \quad (\text{OpenCV는 } \tfrac{\text{cdf}(x)-\text{cdf}_{\min}}{N-\text{cdf}_{\min}} \text{ 를 반올림})$$

### 핵심 개념과 함정

- 두 방법 모두 **히스토그램 → 256칸 LUT 자동 생성 → `cv2.LUT`** 구조예요.
- 스트레칭 = (low, 0)과 (high, 255)를 지나는 직선. 기울기 `a`와 절편 `b`를 **자동**으로 정한 `y = a·x + b`.
- 스트레칭 약점: **극단값 화소 1~2개**가 low/high를 결정해서 무력화돼요. 이미 0~255를 쓰면 효과 없음.
- 평활화 = "나보다 어둡거나 같은 화소의 비율을 밝기로". **곡선의 기울기 ∝ 히스토그램 높이** → 빽빽한 구간은 대비↑, 빈 구간은 대비↓ (재분배).
- 둘 다 **새 정보를 만들지 못해요** (빗살 모양 히스토그램, 같은 값은 쪼갤 수 없음).
- `bin 번호 × bin 폭`은 구간의 **시작값**이라 low가 실제 최솟값보다 작게 나와요 (12 vs 14).
- 직접 구현은 **버림**, OpenCV는 **반올림**이라 46% 화소가 1 차이.
- ⚠️ `12.histogram_equalize.py`: 리스트 컴프리헨션은 바로 덮어써지는 죽은 코드, 27줄 주석은 `표[이미지]` 순서가 반대. `sum(hist)`는 파이썬 내장이라 shape `(1,)` 배열이 나와요 (`hist.sum()` 권장).
- 평활화는 스캔한 문서처럼 **한 값에 화소가 몰린 이미지**에서 노이즈를 증폭해요. 컬러에는 B, G, R 각각이 아니라 **Y(YCrCb)나 L(Lab) 채널에만** 적용.

---

## 6. [06-color-spaces.md](06-color-spaces.md): 컬러 공간

### 핵심 API

| API | 사용법 | 메모 |
|---|---|---|
| `cv2.split(img)` | `b, g, r = cv2.split(img)` | `(H, W)` 채널 3장의 **튜플** |
| `cv2.merge([a, b, c])` | | `(H, W, 3)`으로 합침 |
| `cv2.cvtColor(img, code)` | 아래 표 | 3채널 결과를 `imshow`하면 BGR로 **오해해서** 보여줌 → split해서 흑백으로 |
| `cv2.min(a, b)` | `cv2.min(CMY[0], cv2.min(CMY[1], CMY[2]))` | 원소별 최솟값 (`np.minimum`과 같음) |
| `white - BGR_img` | `np.array([255,255,255], np.uint8) - img` | `(3,)`과 `(H,W,3)` 브로드캐스팅 |
| `float(bgr[0])` | 계산 전에 float 변환 | **uint8끼리 빼면 모듈로** |
| `math.acos`, `math.sqrt` | HSI 색상 계산 | |

| 변환 코드 | 결과 채널 순서 |
|---|---|
| `COLOR_BGR2GRAY` | 1채널. **YCrCb의 Y와 동일** |
| `COLOR_BGR2HSV` | H(0~179), S(0~255), V(0~255) |
| `COLOR_BGR2YCrCb` | **Y, Cr, Cb** (순서 주의) |
| `COLOR_BGR2YUV` | Y, U, V |
| `COLOR_BGR2LAB` | L, a, b (모두 +128 오프셋 포함, L은 0~255로 스케일) |

### 핵심 공식

| 공간 | 공식 |
|---|---|
| CMY | `C = 255−R, M = 255−G, Y = 255−B` → BGR 이미지에서는 채널 순서가 **(Y, M, C)** |
| CMYK | `K = min(C, M, Y)`, 각 채널에서 K를 뺌 (가장 작은 채널은 항상 0, 무채색은 K만 남음) |
| HSI | `I = (R+G+B)/3`, `S = 1 − min/I`, `H = arccos(tmp1/tmp2)` (`B > G`이면 `360 − θ`) |
| HSV (OpenCV) | `V = max`, `S = (max−min)/max`. H는 HSI와 거의 같음 |
| YCrCb | `Y = 0.299R + 0.587G + 0.114B`, `Cr = (R−Y)·0.713 + 128`, `Cb = (B−Y)·0.564 + 128` |
| 저장 | H는 `÷2`(0~180), S는 `×255` |

### 핵심 개념과 함정

- 컬러 공간 = **같은 색을 목적에 맞게 다시 적은 좌표계**. RGB(하드웨어), CMY(K)(프린터), HSV(사람의 직관, 색으로 찾기), YCrCb/YUV(압축), Lab(색 차이 측정).
- 가산혼합(빛, RGB)과 감산혼합(잉크, CMY). 검정 잉크 K를 따로 쓰는 이유: 비용, 번짐, 건조, 위치 어긋남.
- HSI의 H 공식은 "회색축에서 내려다봤을 때 **빨강과의 각도**". arccos는 0~180°만 줘서 `B > G`로 방향을 가려요.
- 순수 원색의 **V = 255**, **I = 85 또는 170**. HSV가 빠르고 단순해서 OpenCV 표준이 됐어요 (직접 구현 102 ms vs `cvtColor` 0.17 ms).
- 색차 채널은 **128 = 색 없음**. 정보 대부분은 밝기(Y)에 있어서 JPEG은 Cr, Cb를 절반 해상도로 줄여요.
- Lab은 숫자 거리 ≈ 사람이 느끼는 색 차이 (밝기를 비선형으로 반영).
- ⚠️ `13.convert_cmy.py`: `Cyan, Magenta, Yellow = cv2.split(...)`는 실제 채널이 (Y, M, C)라서 **이름이 뒤바뀜**. `14`는 올바름.
- ⚠️ `15.convert_hsv.py`: 창 이름 `OpenCV_Intensity`에는 실제로 V가 나와요.
- 튜플 − 배열(`CMY - black`)은 numpy가 튜플을 `(3, H, W)` 배열로 바꿔서 계산하고, 언패킹으로 3장으로 나눠요.
- ⚠️ `BGR2YUV`는 **풀 레인지**, `YUV2BGR_YUY2`는 **리미티드 레인지(BT.601)**라서 짝이 안 맞아요. YUV422/RGBA를 실무에서 다룰 때는 [appendix-yuv422-rgba.md](appendix-yuv422-rgba.md)를 보세요.

---

## 7. [07-thresholding.md](07-thresholding.md): 이진화

### 핵심 API

| API | 사용법 | 메모 |
|---|---|---|
| **`cv2.threshold(src, thresh, maxval, type)`** | `ret, dst = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)` | 반환이 **튜플**. 조건은 `x > thresh` (**초과**) |
| `cv2.THRESH_BINARY` | 넘으면 maxval, 아니면 0 | |
| `cv2.THRESH_BINARY_INV` | 결과를 뒤집음 | |
| `cv2.THRESH_TRUNC` | 넘는 부분을 thresh로 잘라 천장 만듦 | |
| `cv2.THRESH_TOZERO` | thresh 이하 → 0, 나머지는 원래 값 | |
| `cv2.THRESH_TOZERO_INV` | thresh 초과 → 0, 나머지는 원래 값 | |
| `cv2.THRESH_BINARY + cv2.THRESH_OTSU` | `ret, dst = cv2.threshold(img, 0, 255, ...)` | 임계값을 **자동 선택**해서 `ret`에 담음 |
| `cv2.namedWindow(name)` | 트랙바보다 **먼저** | |
| `cv2.createTrackbar(tb, win, init, max, cb)` | `cv2.createTrackbar("threshold", "result", 128, 255, onThreshold)` | 만들 때는 콜백이 호출되지 않음 → 첫 화면은 직접 호출 |
| `cv2.getTrackbarPos(tb, win)` | 콜백 하나에 트랙바 여러 개일 때 모두 다시 읽기 | |
| `np.copy(arr)` | `hue = np.copy(hsv[:, :, 0])` | 채널 뷰는 메모리가 듬성듬성해서 출력 배열로 못 씀 |
| `np.logical_and(a, b)` | `.astype('uint8') * 255` | 범위 마스크 |
| `cv2.inRange(src, lo, hi)` | `cv2.inRange(hsv, (95, 50, 0), (115, 255, 255))` | `lo ≤ x ≤ hi`, 3채널을 한 번에 |

### 범위 이진화: 경계가 방법마다 달라요

| 구현 | 범위 |
|---|---|
| for문 `th[0] <= h < th[1]`, `np.logical_and(h < th[1], h >= th[0])` | `[하한, 상한)` |
| `threshold(TOZERO_INV, 상한)` → `threshold(BINARY, 하한)` (17번 실제 코드) | `(하한, 상한]` |
| `cv2.inRange` | `[하한, 상한]` |

### 핵심 개념과 함정

- 이진화 = 계단 하나짜리 변환 곡선 → 0/255 **마스크**.
- 오츠는 **쌍봉 히스토그램의 골짜기**를 자동으로 찾아요 (`draw_hist.jpg` → 119).
- 범위 트릭: `TOZERO_INV`로 상한 위를 0으로 지우고 → `BINARY`로 하한 위만 255.
- Hue는 조명에 강해요 (햇빛/그늘에서 H, S 그대로 V만 변함). **그래도 채도 낮은 화소의 H는 무의미**해서 실전에서는 **H 범위 + S 하한(+ V 하한)**을 같이 걸어요.
- 빨강은 색상환의 양 끝(0 근처와 179 근처)에 걸쳐 있어서 `inRange` 두 번을 합쳐야 해요.
- ⚠️ 17번의 주석 for문과 실제 코드는 경계 화소 1,020개가 달라요.

---

## 8. [appendix-vscode-debug.md](appendix-vscode-debug.md): 디버거에서 이미지를 못 읽을 때

| 항목 | 내용 |
|---|---|
| 증상 | `Exception("영상 파일 읽기 오류 발생")` (`imread`가 `None`) |
| 원인 | `imread("images/...")`는 **실행 시 cwd** 기준. 디버거 cwd가 저장소 루트면 못 찾음 |
| 해결 | 디버그 드롭다운에서 **`Python: 현재 챕터 파일`** 선택 후 F5 |
| 함정 | `settings.json`의 `python.terminal.executeInFileDir`는 **터미널에만** 적용. 디버거는 `launch.json`의 `"cwd": "${fileDirname}"` |
| 확인 | 디버그 콘솔에서 `import os; os.getcwd()` |

---

## 9. 함수 선택 가이드

| 하고 싶은 일 | 쓸 것 | 피할 것 |
|---|---|---|
| 모든 화소에 같은 f(x) 적용 | `cv2.LUT` / `lut[image]` | 이중 for문 |
| 밝기 더하기 | `cv2.add`, 또는 `int16` 변환 + `clip` | uint8끼리 `+` (모듈로) |
| 두 이미지 섞기 | `cv2.addWeighted` | `(a + b) / 2` (uint8 덧셈이 먼저 돌아감) |
| 대비 조절 | `addWeighted(img, a, zeros, 0, (1−a)·mean)` | 받침점이 0인 `scaleAdd` (밝기까지 같이 변함) |
| 분포 보기 | `cv2.calcHist` + `normalize` + `flip` | 최솟값이 0이 아닐 때 `MINMAX`의 안 보이는 막대 |
| 좁은 분포 늘리기 | 스트레칭 (또는 `cv2.normalize`) | 극단값이 있을 때 |
| 쏠린 분포 펴기 | `cv2.equalizeHist` (흑백) | 컬러 3채널에 각각 |
| 색으로 물체 찾기 | `HSV` + `cv2.inRange` (H, **S 하한**) | RGB 한 채널, H만 단독 |
| 밝기로 영역 나누기 | `cv2.threshold` (+ `THRESH_OTSU`) | 고정값을 모든 사진에 |
| 범위 마스크 | `cv2.inRange` | `threshold` 두 번 (경계 헷갈림) |

---

## 10. 한 번에 보는 함정 목록

| # | 함정 | 문서 |
|---|---|---|
| 1 | `img[y, x]`와 `(x, y)` 순서 혼동 | 02 |
| 2 | 슬라이싱은 **뷰** → 원본이 같이 바뀜 (`.copy()`) | 01, 02 |
| 3 | uint8 모듈로 vs OpenCV 포화 | 03 |
| 4 | `uint8 × 소수`는 float64 → `clip` 필요 | 03 |
| 5 | `astype`는 버림, OpenCV는 반올림 | 03, 05 |
| 6 | `cv2.normalize(hist, hist)`는 원본 덮어씀 | 04 |
| 7 | 회색·흰색은 H = 0 | 04, 06, 07 |
| 8 | 3채널 비-BGR 이미지를 `imshow`하면 색이 이상함 | 06 |
| 9 | `cv2.equalizeHist`는 1채널 전용 | 05 |
| 10 | `threshold`는 `>`(초과), `inRange`는 `≤`(이하) | 07 |
| 11 | 출력용 배열은 연속 메모리여야 함 (`np.copy`) | 07 |
| 12 | NumPy 2.0: `itemset` 삭제 | 01 |
| 13 | 디버거 cwd ≠ 터미널 cwd | 부록 |

## 11. 자가 점검 (답은 원문 각 Part 끝의 질문과 다음 Part 맨 앞)

1. `lut[image]`와 `image[lut]`는 무엇이 다를까요?
2. `cv2.add(np.array([[200]], np.uint8), 100)`과 `np.uint8(200) + np.uint8(100)`은 각각 얼마일까요? (답: 255와 44. 참고로 `cv2.add(200, 100)`처럼 **숫자 둘**을 넘기면 포화가 아니라 `[[300.], [300.], [300.], [300.]]` 같은 엉뚱한 배열이 나와요. 스칼라 둘은 4채널 값으로 해석되기 때문이에요. 한쪽은 꼭 배열이어야 해요.)
3. 평균 100인 이미지의 대비를 1.5배로 높이면서 평균을 유지하려면 `gamma`는?
4. `cv2.calcHist([img], [0], None, [16], [0, 256])`에서 화소값 130은 몇 번째 bin일까요?
5. 평활화 곡선의 기울기가 가파른 구간은 히스토그램의 어떤 구간일까요?
6. BGR (0, 0, 255)의 HSV는? 흰색 (255, 255, 255)의 H는 왜 0일까요?
7. `cv2.threshold(x, 100, 255, cv2.THRESH_BINARY)`에서 `x = 100`은 어떤 값이 될까요?
8. 빨간 공을 찾을 때 `inRange`를 한 번만 쓰면 왜 위험할까요?
