import numpy as np, cv2, time

from sympy import true

def pixel_access1(image):
    image1 = np.zeros(image.shape[:2], image.dtype)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            pixel = image[i,j]                  # 화소 접근
            image1[i, j] =  255 - pixel            # 화소 할당
    return image1

def pixel_access2(image):
    image2 = np.zeros(image.shape[:2], image.dtype)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            pixel = image.item(i, j)  # 화소 접근
            image2.itemset((i, j),  255 - pixel)  # 화소 할당
    return image2

def pixel_access3(image):
    lut = [255 - i for i in range(256)]  # 룩업테이블 생성
    lut = np.array(lut, np.uint8)
    image3 = lut[image]
    return image3

def pixel_access4(image):
    image4 = cv2.subtract(255, image)
    return image4

def pixel_access5(image):
    image5 = 255 - image
    return image5

def pixel_access6(image):
    lut = np.array([i // 2 for i in range(256)], np.uint8)
    image6 = lut[image]
    return image6

image = cv2.imread("images/bright.jpg", cv2.IMREAD_GRAYSCALE)
if image is None: raise Exception("영상 파일 읽기 오류 발생")

# 수행시간 체크
def time_check(func, msg):
    start_time = time.perf_counter()
    ret_img = func(image)
    elapsed = (time.perf_counter() - start_time) * 1000
    print(msg, "수행시간 : %.2f ms" % elapsed)
    return ret_img

image1 = time_check(pixel_access1, "[방법 1] 직접 접근 방식")
#image2 = time_check(pixel_access2, "[방법 2] item() 함수 방식")
image3 = time_check(pixel_access3, "[방법 3] 룩업 테이블 방식")
image4 = time_check(pixel_access4, "[방법 4] OpenCV 함수 방식")
image5 = time_check(pixel_access5, "[방법 5] ndarray 연산 방식")
image6 = time_check(pixel_access6, "[방법 6] 룩업 테이블 방식 (반감)") 

# 결과 영상 보기
cv2.imshow("image  - original", image)
cv2.imshow("image1 - directly access to pixel", image1)
#cv2.imshow("image2 - item()/itemset()", image2)
cv2.imshow("image3 - LUT", image3)
cv2.imshow("image4 - OpenCV", image4)
cv2.imshow("image5 - ndarray 방식", image5)
cv2.imshow("image6 - LUT 반감", image6) 


new_image = cv2.imread("images/bright.jpg", cv2.IMREAD_COLOR)
if new_image is None: raise Exception("영상 파일 읽기 오류 발생")

def convert_to_grayscale(bgr_image, flag=True):
    if flag:
        return cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    else:
        Y = 0.299 * bgr_image[:,:,2] + 0.587 * bgr_image[:,:,1] + 0.114 * bgr_image[:,:,0]
        return Y.astype(np.uint8)

custom_gray = convert_to_grayscale(new_image, False)
cv_gray = convert_to_grayscale(new_image, True)

# compare custom_gray and cv_gray
# cv way
diff_cv = cv2.absdiff(custom_gray, cv_gray)  # cv way
# np way
diff_np = np.abs(custom_gray.astype(np.int16) - cv_gray.astype(np.int16))  # np way
comparison = np.all(diff_cv == diff_np)  # 비교 결과
print("Comparison result:", comparison)

cv2.imshow("image - grayscale custom", custom_gray) 
cv2.imshow("image - grayscale OpenCV", cv_gray) 

cv2.waitKey(0)