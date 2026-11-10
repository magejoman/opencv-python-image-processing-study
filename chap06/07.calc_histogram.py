import numpy as np, cv2

def calc_histo(image, hsize, ranges=[0, 256]):  # 행렬 원소의 1차원 히스토그램 계산
    hist = np.zeros((hsize, 1), np.float32)  # 히스토그램 누적 행렬
    gap = ranges[1]/hsize  # 계급 간격

    for i in (image/gap).flat:
        hist[int(i)] += 1
    return hist

image = cv2.imread("images/pixel.jpg", cv2.IMREAD_GRAYSCALE)  # 영상 읽기
if image is None: raise Exception("영상 파일 읽기 오류 발생")

# image.flat: 배열을 1차원으로 순회하는 이터레이터(flatiter 객체) -> shape 속성이 없어 image.flat.shape는 AttributeError 발생
print(f"image.shape: {image.shape}, image.dtype: {image.dtype}")
print(f"image.flat: {image.flat}, type: {type(image.flat)}")  # <numpy.flatiter object>
print(f"image.flat[0]: {image.flat[0]}")  # 인덱싱 가능 (1차원 인덱스로 접근)
print(f"전체 원소 수: image.size = {image.size} (shape 대신 size 사용)")  # flat의 '크기'는 image.size로 확인
print(f"list(image.flat)[:8]: {list(image.flat)[:8]}")  # 이터레이터이므로 list()로 변환해 값 확인 가능
# for pixel in image.flat:  # 반복문에서 1차원 순회용으로 주로 사용
#     ...

hsize, ranges = [32], [0, 256]  # 히스토그램 간격수, 값 범위
hist = calc_histo(image, hsize[0], ranges)  # 사용자 정의 히스토그램 계산
print(f"hist.shape: {hist.shape}, hist.dtype: {hist.dtype}", hist)
print("사용자 정의 함수: \n", hist.flatten())  # 행렬을 벡터로 변환하여 출력
cv2.imshow("image", image)

cv2.waitKey(0)