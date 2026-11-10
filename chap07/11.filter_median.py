import numpy as np, cv2

def median_filter(image, ksize):
    rows, cols = image.shape[:2]
    dst = np.zeros((rows, cols), np.uint8)
    center = ksize // 2                                 # 마스크 절반 크기

    for i in range(center, rows - center):              # 입력 영상 순회
        for j in range(center, cols - center):
            y1, y2 = i - center, i + center + 1             # 마스크 높이 범위
            x1, x2 = j - center, j + center + 1             # 마스크 너비 범위
            mask = image[y1:y2, x1:x2].flatten()            # 마스크 영역
            # sort_mask = cv2.sort(mask, cv2.SORT_EVERY_COLUMN).flat   # 정렬 수행 #1
            # sort_mask = np.sort(mask)                               # 정렬 수행 #2
            # dst[i, j] = sort_mask[mask.size//2]                  # 출력화소로 지정
            dst[i, j] = np.median(mask)                           # 중앙값으로 출력화소 지정
    return dst

def salt_pepper_noise(img, n):
    h, w = img.shape[:2]
    x, y = np.random.randint(0, w, n), np.random.randint(0, h, n)
    noise = img.copy()
    for (x,y) in zip(x,y):
        noise[y, x] = 0 if np.random.rand() < 0.5 else 255
    return noise

image = cv2.imread("images/median2.jpg", cv2.IMREAD_GRAYSCALE)
if image is None: raise Exception("영상파일 읽기 오류")
    
noise = salt_pepper_noise(image, 500)
med_img1 = median_filter(noise, 3)                            # 사용자 정의 함수
med_img2 = cv2.medianBlur(noise, 3)                          # OpenCV 제공 함수

cv2.imshow("image", image),
cv2.imshow("noise", noise),
cv2.imshow("median - User", med_img1)
cv2.imshow("median - OpenCV", med_img2)
cv2.waitKey(0)


# # flatten 동작 확인
# mask = np.array([[9, 5, 3],
#                  [4, 8, 1],
#                  [7, 2, 6]])
# print(f"mask:\n{mask}")
# print(f"mask.flatten():\n{mask.flatten()}")
# print(f"mask.size: {mask.size}")
# print(f"mask.flatten().size: {mask.flatten().size}")
# # reshaped = mask.reshape((mask.size, -1)) # wrong
# reshaped = mask.reshape(-1)
# print(f"reshaped:\n{reshaped} | reshaped.shape: {reshaped.shape}")