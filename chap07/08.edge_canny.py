import numpy as np, cv2
from Common.utils import ck_time

# ─────────────────────────────────────────────────────────────────────
# Part 6(study-notes/chap07/06-canny.md)에서 찾은 코드 문제 수정 내역
#   [문제 1] 블러 σ = 0.3은 사실상 블러가 아님        → σ = 1.0            (6-3-b)
#   [문제 2] 방향 구간을 버림으로 계산 → 22.5° 밀림     → +π/8 후 버림(반올림) (6-4-d)
#   [문제 3] NMS 엄격 부등호 → 동점이면 둘 다 사라짐     → s > v1 and s >= v2  (6-5-e)
#   [문제 4] trace 재귀 → 긴 에지에서 RecursionError   → 명시적 스택         (6-6-e)
#   [문제 5] 전역 변수 pos_ck, canny                   → 결과를 반환하는 함수 (6-6-f)
#   [덤]    id, max가 내장 함수 이름을 가림             → idx, vmax
# 원래 코드는 [원래 코드] 주석으로 남겨 두었다.
# ─────────────────────────────────────────────────────────────────────

def nonmax_suppression(sobel, direct):
    rows, cols = sobel.shape[:2]
    dst = np.zeros((rows, cols), np.float32)
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            # 행렬 처리를 통해 이웃 화소 가져오기
            values = sobel[i-1:i+2, j-1:j+2].flatten()
            first = [3, 0, 1, 2]
            idx = first[direct[i, j]]                   # [덤] id → idx
            v1, v2 = values[idx], values[8-idx]

            ## if 문으로 이웃 화소 가져오기
            # if direct[i, j] == 0: # 기울기 방향 0도
            #     v1, v2 = sobel[i, j-1], sobel[i, j+1]
            # if direct[i, j] == 1: # 기울기 방향 45도
            #     v1, v2 = sobel[i-1, j-1], sobel[i+1, j+1]
            # if direct[i, j] == 2: # 기울기 방향 90도
            #     v1, v2 = sobel[i-1, j], sobel[i+1, j]
            # if direct[i, j] == 3: # 기울기 방향 135도
            #     v1, v2 = sobel[i+1, j-1], sobel[i-1, j+1]

            # [원래 코드] 양쪽 모두 엄격 비교 → 쌍둥이 봉우리(동점)가 둘 다 지워짐
            # dst[i, j] = sobel[i, j] if (v1 < sobel[i , j] > v2) else 0
            s = sobel[i, j]
            dst[i, j] = s if (s > v1 and s >= v2) else 0    # [문제 3] 동점이면 한쪽만 살림
    return dst

def nonmax_suppression1(sobel, direct):
    rows, cols = sobel.shape[:2]
    dst = np.zeros((rows, cols), np.float32)
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            values = sobel[i-1:i+2, j-1:j+2].flat
            vmax = np.max(values)                       # [덤] max → vmax
            dst[i, j] = sobel[i, j] if sobel[i , j] >= vmax else 0
    return dst

## [원래 코드] 재귀 버전 + 전역 변수 pos_ck, canny 사용
##   - 에지가 길게 이어지면 재귀 깊이 1000 초과로 RecursionError
##   - 두 번 호출하면 첫 호출의 방문 표시가 남아 결과가 틀림
# def trace(max_sobel, i, j, low):
#     h, w = max_sobel.shape
#     if (0 <= i < h and 0 <= j < w) == False: return  # 추적 화소 범위 확인
#     if pos_ck[i, j] == 0 and max_sobel[i, j] > low:
#         pos_ck[i, j] = 255
#         canny[i, j] = 255
#         trace(max_sobel, i - 1, j - 1, low)# 추적 함수 재귀 호출 - 8방향 추적
#         trace(max_sobel, i    , j - 1, low)
#         trace(max_sobel, i + 1, j - 1, low)
#         trace(max_sobel, i - 1, j    , low)
#         trace(max_sobel, i + 1, j    , low)
#         trace(max_sobel, i - 1, j + 1, low)
#         trace(max_sobel, i    , j + 1, low)
#         trace(max_sobel, i + 1, j + 1, low)
#
# def hysteresis_th(max_sobel, low, high):                # 이력 임계값 수행
#     rows, cols = max_sobel.shape[:2]
#     for i in range(1, rows - 1):  # 에지 영상 순회
#         for j in range(1, cols - 1):
#             if max_sobel[i, j] > high:  trace(max_sobel, i, j, low)  # 추적 시작

# [문제 4] 스택 버전 - 재귀 대신 방문할 화소 목록을 직접 관리
# [문제 5] 결과 배열 edge를 인자로 받아 방문 표시로도 사용 (pos_ck와 canny는 항상 같았음)
def trace(max_sobel, edge, i, j, low):
    h, w = max_sobel.shape
    stack = [(i, j)]                                    # 방문할 화소 목록
    while stack:
        i, j = stack.pop()                              # 하나 꺼내서
        if (0 <= i < h and 0 <= j < w) == False: continue   # 추적 화소 범위 확인
        if edge[i, j] == 0 and max_sobel[i, j] > low:
            edge[i, j] = 255
            for di in (-1, 0, 1):                       # 8방향 이웃을 목록에 추가
                for dj in (-1, 0, 1):
                    if di != 0 or dj != 0:
                        stack.append((i + di, j + dj))

def hysteresis_th(max_sobel, low, high):                # 이력 임계값 수행
    rows, cols = max_sobel.shape[:2]
    edge = np.zeros((rows, cols), np.uint8)             # [문제 5] 호출할 때마다 새로 만듦
    for i in range(1, rows - 1):  # 에지 영상 순회
        for j in range(1, cols - 1):
            if max_sobel[i, j] > high:  trace(max_sobel, edge, i, j, low)  # 추적 시작
    return edge                                         # [문제 5] 결과를 반환

image = cv2.imread("images/canny.jpg", cv2.IMREAD_GRAYSCALE)
if image is None: raise Exception("영상 파일 읽기 오류")
# [원래 코드] 전역 변수 → [문제 5]로 hysteresis_th 안으로 옮김
# pos_ck = np.zeros(image.shape[:2], np.uint8)
# canny = np.zeros(image.shape[:2], np.uint8)

# 사용자 정의 캐니 에지
# gaus_img = cv2.GaussianBlur(image, (5, 5), 0.3)       # [원래 코드] σ = 0.3: 화소 1%만 바뀜
gaus_img = cv2.GaussianBlur(image, (5, 5), 1.0)         # [문제 1] 캐니 원래 의도에 맞는 블러
Gx = cv2.Sobel(np.float32(gaus_img), cv2.CV_32F, dx=1, dy=0, ksize=3)  # x방향 마스크
Gy = cv2.Sobel(np.float32(gaus_img), cv2.CV_32F, dx=0, dy=1, ksize=3)  # y방향 마스크
#sobel = cv2.magnitude(Gx, Gy)                            # 두 행렬 벡터 크기
sobel = np.fabs(Gx) + np.fabs(Gy)                       # 두 행렬 절댓값 덧셈 (cv2.Canny 기본값 L1과 같은 자)
# directs = cv2.phase(Gx, Gy) / (np.pi / 4)             # [원래 코드] 버림 → 구간이 22.5° 밀림
directs = (cv2.phase(Gx, Gy) + np.pi / 8) / (np.pi / 4) # [문제 2] +22.5° 후 버림 = 반올림
directs = directs.astype(int) % 4
max_sobel = nonmax_suppression(sobel, directs)          # 비최대치 억제
canny = hysteresis_th(max_sobel, 100, 150)              # 이력 임계값 (결과를 받음)
# canny2 = cv2.Canny(image, 100, 150)                   # [원래 코드] 블러 안 한 원본을 넣음
canny2 = cv2.Canny(gaus_img, 100, 150)                  # cv2.Canny에는 블러가 없으니 같은 블러 영상을 넣어야 공정한 비교

cv2.imshow("image", image)
cv2.imshow("canny", canny)                 # 사용자 정의 캐니
cv2.imshow("OpenCV_Canny", canny2)           # OpenCV 캐니 에지
cv2.waitKey(0)
