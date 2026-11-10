import numpy as np, cv2
from Common.filters import filter

image = cv2.imread("images/filter_sharpen.jpg", cv2.IMREAD_GRAYSCALE) # 영상 읽기
if image is None: raise Exception("영상파일 읽기 오류")

# 샤프닝 마스크 원소 지정 
data1 = [0, -1, 0,
        -1, 5, -1,
         0, -1, 0]
data2 = [[-1, -1, -1],
         [-1, 9, -1],
         [-1, -1, -1]]
mask1 = np.array(data1, np.float32).reshape(3, 3)
mask2 = np.array(data2, np.float32)

sharpen1 = filter(image, mask1)                     # 회선 수행 – 저자 구현 함
sharpen2 = filter(image, mask2) 
"""_summary_ 
💡 그럼 convertScaleAbs는 언제 맞는 도구일까요? 부호가 의미 없을 때예요. Part 2의 에지 검출에서 "밝아지는 경계(+)든 어두워지는 경계(−)든 경계의 세기만 보고 싶다"면 절댓값이 정답이에요. Common/filters.py의 differential()이 convertScaleAbs를 쓰는 이유가 그거예요. 도구 자체는 잘못이 없고, 샤프닝에 쓴 게 잘못이에요.
"""
sharpen1 = cv2.convertScaleAbs(sharpen1)  # 오구현: 음수에 절댓값을 취해 밝은 값으로 바꿈
sharpen2 = cv2.convertScaleAbs(sharpen2)  # 샤프닝 결과의 음수는 어두운 값이므로 0으로 포화해야 함
sharpen3 = np.clip(filter(image, mask1), 0, 255).astype(np.uint8) # # 방법 ①: 직접 만든 filter를 쓰고, numpy로 0~255 자르기

sharpen4 = np.clip(filter(image, mask2), 0, 255).astype(np.uint8)
# sharpen3 = cv2.filter2D(image, -1, mask1) # # 방법 ②: OpenCV에 맡기기 (ddepth = -1 → 출력도 입력과 같은 uint8, 자동으로 0~255 포화)

# sharpen4 = cv2.filter2D(image, -1, mask2)

cv2.imshow("image", image)
cv2.imshow("sharpen1", sharpen1)
cv2.imshow("sharpen2", sharpen2)
cv2.imshow("sharpen3", sharpen3)
cv2.imshow("sharpen4", sharpen4)

# 계산값은 5×250 − 4×200 = 1250 − 800 = 450이에요. 
# filter2D(image, -1, ...)는 uint8로 내보내면서 포화시키니까 최종 값은 255예요.
data3 = [0, 200, 0,
         200, 250, 200,
         0, 200, 0]
data3_np = np.array(data3, np.uint8).reshape(3, 3)
result = cv2.filter2D(data3_np, -1, mask1)
print(result) 

cv2.waitKey(0)

