import numpy as np, cv2
from  Common.filters import differential

image = cv2.imread("images/edge.jpg", cv2.IMREAD_GRAYSCALE)
if image is None: raise Exception("영상파일 읽기 오류")
    
data1 = [-1, 0, 1,                  # 수직 마스크
         -2, 0, 2,
         -1, 0, 1]
data2 = [-1,-2,-1,                 # 수평 마스크
          0, 0, 0,
          1, 2, 1]
dst, dst1, dst2 = differential(image, data1, data2)     # 두 방향 회선 및 크기(에지 강도) 계산
# OpenCV 제공 소벨 에지 계산
# np.float32(image)는 필요 없어요. uint8 영상을 그대로 넣고 ddepth=cv2.CV_32F만 주면 결과가 완전히 같았어요. OpenCV가 내부에서 알아서 바꿔요.
# dst3 = cv2.Sobel(np.float32(image), cv2.CV_32F, 1, 0, ksize=3)  # x방향 미분 - 수직 마스크
dst3 = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)  # x방향 미분 - 수직 마스크
dst4 = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)  # y방향 미분 - 수평 마스크
# 시그니처의 dst=None은 결과를 저장할 출력 배열을 생략할 수 있다는 뜻이다.
# 생략하면 새 배열을 반환하고, 지정하면 그 배열에 결과를 기록한다.
# MatLike는 OpenCV 행렬을 나타내는 타입 표기로, Python에서는 보통 NumPy 배열(np.ndarray)을 전달한다.
# 예: output = np.empty_like(image, dtype=np.float32)
#     cv2.Sobel(np.float32(image), cv2.CV_32F, 1, 0, dst=output, ksize=3)
# 위 호출은 output에 결과를 기록하고, 반환값도 output이다.



dst3 = cv2.convertScaleAbs(dst3)                          # 절댓값 및 uint8 형변환
dst4 = cv2.convertScaleAbs(dst4)

cv2.imshow("dst- sobel edge", dst)
cv2.imshow("dst1- vertical_mask", dst1)
cv2.imshow("dst2- horizontal_mask", dst2)
cv2.imshow("dst3- vertical_OpenCV", dst3)
cv2.imshow("dst4- horizontal_OpenCV", dst4)
cv2.waitKey(0)


gray = cv2.imread("images/edge.jpg", cv2.IMREAD_GRAYSCALE)
if gray is None: raise Exception("영상파일 읽기 오류")

# Sobel은 x와 y 방향의 밝기 변화율(기울기)을 각각 계산합니다.
# CV_32F를 사용해 음수 기울기와 소수점 값을 보존합니다.
# Gx: 좌우(x) 방향의 밝기 변화 -> 주로 수직 경계에 반응
# Gy: 상하(y) 방향의 밝기 변화 -> 주로 수평 경계에 반응
grad_x = cv2.Sobel(gray, cv2.CV_32F, dx=1, dy=0, ksize=3)
grad_y = cv2.Sobel(gray, cv2.CV_32F, dx=0, dy=1, ksize=3)

# 두 방향의 기울기를 결합해 각 픽셀의 전체 엣지 강도를 계산합니다.
# magnitude = sqrt(Gx^2 + Gy^2)
# 따라서 수평·수직뿐 아니라 대각선 방향의 엣지도 함께 나타납니다.
magnitude = cv2.magnitude(grad_x, grad_y)

# 화면에 표시하기 위한 8비트 영상으로 변환합니다.
# 정규화는 시각화용이므로, 실제 강도 임계값 처리에는 magnitude를 사용하세요.
magnitude_display = cv2.normalize(
    magnitude, None, 0, 255, cv2.NORM_MINMAX
).astype(np.uint8)

# 필요하면 기울기 방향도 계산할 수 있습니다.
# 이 값은 밝기가 가장 빠르게 증가하는 방향이며,
# 엣지 선의 방향과는 수직입니다.
gradient_direction = cv2.phase(grad_x, grad_y, angleInDegrees=True)

cv2.imshow("Sobel magnitude", magnitude_display)
cv2.imshow("Sobel gradient direction", gradient_direction)
cv2.waitKey(0)
cv2.destroyAllWindows()

# cv2.phase의 각도 범위는 0~360도입니다.
# OpenCV의 8비트 HSV에서 H(색상) 범위는 0~179이므로 각도를 2로 나눕니다.
# 색상: 그래디언트 방향, 밝기(V): 엣지 강도, 채도(S): 방향을 표시할 최소 강도
hsv = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)
hsv[..., 0] = (gradient_direction / 2).astype(np.uint8)

# 약한 기울기는 방향이 불안정하므로 채도를 낮춰 회색으로 표시합니다.
# 30은 예시 임계값이며, 영상의 밝기와 Sobel 결과에 따라 조정하세요.
hsv[..., 1] = np.where(magnitude > 30, 255, 0).astype(np.uint8)

# 전체 강도를 화면에 맞게 정규화해 밝기로 표시합니다.
hsv[..., 2] = cv2.normalize(
    magnitude, None, 0, 255, cv2.NORM_MINMAX
).astype(np.uint8)

direction_color = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
cv2.imshow("Sobel gradient direction (color)", direction_color)
cv2.waitKey(0)
cv2.destroyAllWindows()
