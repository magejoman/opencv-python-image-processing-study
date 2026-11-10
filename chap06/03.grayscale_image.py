import numpy as np, cv2

image1 = np.zeros((50, 512), np.uint8)         # 50 x 512 영상 생성
image2 = np.zeros((50, 512), np.uint8)

rows, cols = image1.shape[:2]

for i in range(rows):                           # 행렬 전체 조회
    for j in range(cols):
        image1[i, j]= j // 2                # 화소값 점진적 증가
        image2[i, j]= j // 20 * 10          # 계단 현상 증가

cv2.imshow("image1", image1)
cv2.imshow("image2", image2)

image3, image4 = np.zeros((50, 512), np.uint8), np.zeros((50, 512), np.uint8)
image3[:] = np.arange(512) // 2          # 길이 512 줄을 50행 전체에 브로드캐스팅
image4[:] = np.arange(512) // 20 * 10

cv2.imshow("image3", image3)
cv2.imshow("image4", image4)

cv2.waitKey(0)


a = np.zeros((1,3), np.uint8)
a[0,0] = 300            # → OverflowError: Python integer 300 out of bounds for uint8
a[0,1] = np.int64(300)  # → 에러 없이 44 가 들어감 (!!)
