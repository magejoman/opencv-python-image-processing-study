import numpy as np
import cv2

image = cv2.imread("images/bright.jpg", cv2.IMREAD_GRAYSCALE)    # 영상 읽기
if image is None: raise Exception("영상 파일 읽기 오류")

# OpenCV 함수 이용
dst1 = cv2.add(image, 200)                  # 영상 밝게 saturation 방식
dst2 = cv2.subtract(image, 200)             # 영상 어둡게
# safe = np.clip(image.astype(np.int16) + 100, 0, 255).astype(np.uint8)
dst5 = np.clip(image.astype(np.int16) + 100, 0, 255).astype(np.uint8)  # 안전하게 밝게
dst6 = np.clip(image.astype(np.int16) - 100, 0, 255).astype(np.uint8)  # 안전하게 어둡게

# numpy array 이용
dst3 = image + 100                          # 영상 밝게 modulo 방식
dst4 = image - 100                          # 영상 어둡게

cv2.imshow("original image", image)
cv2.imshow("dst1- bright: OpenCV", dst1)
cv2.imshow("dst2- dark: OpenCV", dst2)
cv2.imshow("dst3- bright: numpy", dst3)
cv2.imshow("dst4- dark: numpy", dst4);
cv2.imshow("dst5- bright: safe", dst5)
cv2.imshow("dst6- dark: safe", dst6)
cv2.waitKey(0)

