import numpy as np, cv2

image = cv2.imread("images/dog.jpg", cv2.IMREAD_GRAYSCALE)
if image is None: raise Exception("영상파일 읽기 오류")

gaus = cv2.GaussianBlur(image, (9,9), 0, 0)            # 가우시안 마스크 적용
dst1 = cv2.Laplacian(gaus, cv2.CV_16S, ksize=1)        # 키워드로 (3×3이면 충분)

gaus1 = cv2.GaussianBlur(image, (3, 3), 0)          # 가우사안 블러링
gaus2 = cv2.GaussianBlur(image, (9, 9), 0)
dst2 = gaus1.astype(np.int16) - gaus2.astype(np.int16)        # −87 ~ 82 그대로 보존

# 화면에 띄우는 방법 세 가지
a = cv2.convertScaleAbs(dst1)                                  # ① 절댓값: 에지 세기만 (부호 버림)
b = np.clip(dst2 * 4 + 128, 0, 255).astype(np.uint8)          # ② 128 = 0, 위아래로 부호 표시
c = cv2.normalize(dst1, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)  # ③ 최소~최대를 0~255로 늘리기

cv2.imshow("image", image)
cv2.imshow("dst1 - LoG", a)
cv2.imshow("dst2 - DoG", b)
cv2.imshow("dst1 - LoG (normalized)", c)
cv2.waitKey(0)
