import numpy as np, cv2

def minmax_filter(image, ksize, mode):
    rows, cols = image.shape[:2]
    dst = np.zeros((rows, cols), np.uint8)
    center = ksize // 2                                 # 마스크 절반 크기

    for i in range(center, rows - center):             # 입력 영상 순회
        for j in range(center, cols - center):
            # 마스크 영역 행렬 처리 방식
            y1, y2 = i - center, i + center + 1          # 마스크 높이 범위
            x1, x2 = j - center, j + center + 1          # 마스크 너비 범위
            mask = image[y1:y2, x1:x2]                   # 마스크 영역
            dst[i, j] = cv2.minMaxLoc(mask)[mode]
    return dst

image = cv2.imread("images/min_max.jpg", cv2.IMREAD_GRAYSCALE)
if image is None: raise Exception("영상파일 읽기 오류")
    
minfilter_img = minmax_filter(image, 3, 0) # 3x3 마스크 최솟값 필터링(mode 0)
maxfilter_img = minmax_filter(image, 3, 1) # 3x3 마스크 최댓값 필터링(mode 1)

cv2.imshow("image", image)
cv2.imshow("minfilter_img", minfilter_img)
cv2.imshow("maxfilter_img", maxfilter_img)
cv2.waitKey(0)


"""
w = [[ 10, 12, 11],
     [255, 13, 12],
     [  0, 10, 14]]
cv2.minMaxLoc(w)  →  (0.0,  255.0,  (0, 2),  (0, 1))
                      [0]    [1]     [2]      [3]
                      최솟값  최댓값  최솟값 위치  최댓값 위치
                                     x=0, y=2   x=0, y=1     위치는 (x, y) 순서예요. numpy 인덱스 [y, x]와 반대라서, 위치로 배열에 접근할 때 뒤집어야 해요. 
"""