import cv2
import numpy as np

image = cv2.imread("images/pixel.jpg", cv2.IMREAD_GRAYSCALE) # 영상 읽기
if image is None: raise Exception("영상 파일 읽기 오류")

(x,y),(w,h) = (180, 37), (15, 10)                   # 좌표는 x, y
roi_img = image[y:y+h, x:x+w]                   # 행렬 접근은 y, x

#print(“[roi_img] =\n”, roi_img) # 행렬 원소 바로 출력 가능
print(f"[ROI] shares_memory: {np.shares_memory(image, roi_img)}") # True, roi_img는 image와 메모리를 공유함

(x1, y1), (w1, h1) = (10, 20), (30, 5)
roi_img2 = image[y1:y1+h1, x1:x1+w1]
print(f"[shape] roi_img2: {roi_img2.shape}")

print("[roi_img] =")
for row in roi_img:
    for p in row:
        print("%4d" % p, end="")       # 행렬 원 하나 출력
    print()

cv2.rectangle(image, (x,y, w,h), 255, 1)
cv2.imshow("image", image)

original_width, original_height = image.shape[1], image.shape[0]
scale_x, scale_y = 2.0, 2.0
scaled_width, scaled_height = int(original_width * scale_x), int(original_height * scale_y)
scaled_image = cv2.resize(image, (scaled_width, scaled_height))

print(f"[Scaled] shares_memory: {np.shares_memory(image, scaled_image)}") # False, scaled_image는 image와 메모리를 공유하지 않음

(x2,y2), (w2,h2) = (180, 37), (100,100)
cv2.rectangle(scaled_image, (x2, y2, w2, h2), 125, 2)
cv2.imshow("scaled_image", scaled_image)

cv2.waitKey(0)