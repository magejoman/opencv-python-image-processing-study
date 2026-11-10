# chap09 주파수 영역 처리 (DFT · FFT · DCT) 학습 노트

- 세션 날짜: 2026-10-20 ~ 2026-10-27
- 설명 방식: Markdown(ASCII 그림, 숫자 표, 손계산) 우선. 숫자는 전부 실제로 돌려서 얻은 값 (Python 3.12.9, NumPy 2.1.2, OpenCV 4.12.0, SciPy 1.15.3)
- 배경지식: `reference/Chapter06` (관련 개념이 나올 때 📚 복습 박스로 짧게 리뷰)
- 🚗 박스: 업무(AVM 서라운드뷰, 탑뷰, 어안, 모아레)와 연결되는 부분. [moire_sim/HANDOFF_topview_moire.md](../../moire_sim/HANDOFF_topview_moire.md)와 이어져요

> `README.md`만 직접 쓴 파일이고, `00-plan.md`와 Part 파일은 세션 기록에서 `study-notes/tools/extract_session.py`로 **추출한 원문**이에요. 보관하면서 고친 곳은 두 군데예요: `08`의 양자화 손계산 한 줄(실측값 −60.125로 정리), `09` 마지막 줄(정리 작업 안내 문구 → 목차 링크). 각 파일 끝의 "셀프 체크"는 같은 파일 안에 정답이 있어요. 총정리는 **Part 9**가 해요.

## 핵심 한 문장

> **이미지는 여러 주파수 무늬의 합이다. 그 무늬들을 재고(DFT·DCT), 고르고(마스크), 다시 합치면(역변환) 흐림, 윤곽, 모아레 제거, 압축이 전부 같은 틀에서 나온다. 단, 샘플링 때 이미 접힌 무늬는 되돌릴 수 없다.**

## 목차

| 파일 | 내용 | 다룬 코드 |
|---|---|---|
| [09-summary.md](09-summary.md) | **총정리**: 한 장 지도, 함수 치트시트, 공식 모음, 버그 목록, AVM 요약, 종합 퀴즈 (복습은 여기부터) | 전체 |
| [00-plan.md](00-plan.md) | 학습 계획 (Part 0~9) | — |
| [00-prereq-1-sine-wave.md](00-prereq-1-sine-wave.md) | 사인파 A·sin(2πft+φ), 라디안, 진폭·주파수·위상 | — |
| [00-prereq-2-sampling-aliasing.md](00-prereq-2-sampling-aliasing.md) | 샘플링, 나이퀴스트, 앨리어싱(마차 바퀴), 모아레 = 이미지 앨리어싱 | — |
| [00-prereq-3-complex-numbers.md](00-prereq-3-complex-numbers.md) | 복소수 = 2D 화살표, 곱셈 = 회전 + 확대, OpenCV 2채널 저장 | — |
| [00-prereq-4-euler.md](00-prereq-4-euler.md) | 오일러 공식, cos = 거울 봉우리 두 개, 회전자 | — |
| [00-prereq-5-inner-product.md](00-prereq-5-inner-product.md) | 내적 = 닮은 정도, 직교성, DFT = sin·cos 측정 | — |
| [01-frequency-basics.md](01-frequency-basics.md) | 사인파 그리기와 합성 | 01, 02 |
| [02-dft-1d.md](02-dft-1d.md) | 1D DFT/IDFT, DC, 진폭 2\|G\|/N, 켤레 대칭, df, 누설 | 03 |
| [03-dft-2d-spectrum.md](03-dft-2d-spectrum.md) | 2D DFT 분리, 전치 트릭, `calc_spectrum`, fftshift, 스펙트럼 읽기 | 04 |
| [04-fft.md](04-fft.md) | FFT 짝/홀 분할, 나비 연산, 비트 반전, 영삽입, np.fft vs cv2.dft | 05 |
| [05-frequency-filtering.md](05-frequency-filtering.md) | 원 마스크 LPF/HPF, 링잉(깁스), 가우시안·버터워스, 컨볼루션 정리 | 06, 07 |
| [06-moire-removal.md](06-moire-removal.md) | 모아레 = 맥놀이, threshold INV + 원 보호, 트랙바, 탑뷰에 안 되는 이유 | 08 |
| [07-dct.md](07-dct.md) | DCT = 거울 확장, 기저 행렬과 직교성, 기저 이미지 64장, 에너지 압축 | 09 |
| [08-dct-block-jpeg.md](08-dct-block-jpeg.md) | 8×8 블록 마스크 5종, DC Pass = 박스 평균, JPEG 양자화, 박스 vs 이항 | 10 |

## 세션에서 발견한 코드 이슈 (수정하지 않음)

| 위치 | 내용 | 설명 위치 |
|---|---|---|
| [03.1d_dft.py:15](../../chap09/03.1d_dft.py#L15) | `idft(G)`가 인자 대신 전역 `g` 사용 → 역변환이 1e−12 잡음 | Part 2 |
| [03.1d_dft.py:29](../../chap09/03.1d_dft.py#L29) | `np.arange(0, N, df)`는 N = fs일 때만 맞음 | Part 2 |
| [04.2d_dft.py:26](../../chap09/04.2d_dft.py#L26) | `dft = dft2(image)` 변수가 함수 이름을 가림 | Part 3 |
| [Common/dft2d.py:24-32](../../Common/dft2d.py#L24-L32), [Common/fft2d.py:54-62](../../Common/fft2d.py#L54-L62) | 수업용 `fftshift`가 홀수 크기에서 가운데 행·열을 버림 | Part 3 |
| [Common/fft2d.py](../../Common/fft2d.py) `fft()` | 2ⁿ이 아닌 길이(예: 6)면 IndexError (`fft2`는 영삽입으로 피함) | Part 4 |
| [06.FFT_filtering1.py:22](../../chap09/06.FFT_filtering1.py#L22) | mode 1(256 패딩)에서 원 중심이 DC와 8칸 어긋남 → 허수부 48, 결과 최대 43 차이 | Part 5 |
| [07.FFT_filtering2.py:8-9](../../chap09/07.FFT_filtering2.py#L8-L9) | `arange(−u, u)`는 짝수 크기만 됨 | Part 5 |
| [08.remove_moire.py:33-34](../../chap09/08.remove_moire.py#L33-L34) | `createTrackbar`가 즉시 콜백 호출 → 시작 시 Traceback, 기본 threshold 120은 98% 삭제 | Part 6 |
| [09.dct.py:42](../../chap09/09.dct.py#L42), [:47](../../chap09/09.dct.py#L47) | `dct2`, `idct2` 변수가 함수 이름을 가림 | Part 7 |
| [10.dct_filtering.py:20](../../chap09/10.dct_filtering.py#L20) | 8의 배수가 아닌 크기면 ValueError | Part 8 |
| [10.dct_filtering.py:16-21](../../chap09/10.dct_filtering.py#L16-L21) | 주석이 `??`로 깨짐 (원문 복구 불가, 글자 수로 후보 추정), 전역 `mode`, `'Horizental'` 오타 | Part 8 |

## 남은 할 일

- [ ] Part 9-8의 직접 해 볼 것 (03 idft 고치기, 06 mode 1 중심, 07 R = 42 비교, 08 `ready` 플래그 + 부드러운 마스크, 10 REFLECT 패딩)
- [ ] [moire_sim/](../../moire_sim/)에서 2×2 박스 vs [1,3,3,1] 이항 프리필터를 스펙트럼 지표(중심 밖 에너지)로 비교
- [ ] (선택) 10번 깨진 주석을 Part 8-8-5 후보로 복원
- [ ] (선택) HTML 인터랙티브 시각화: 관람차 사인파(0-1), fs·f 슬라이더 앨리어싱(0-2), 회전자(2), 스펙트럼 그리기(3), 나비 연산(4), 필터 단면·링잉(5), threshold·radius 모아레 제거(6), DCT 기저 타일 조립(7), JPEG 품질 슬라이더(8)
