import numpy as np, cv2

def draw_histo(hist, shape=(200, 256)):
    hist_img = np.full( shape, 255, np.uint8)
    cv2.normalize(hist, hist, 0, shape[0], cv2.NORM_MINMAX)
    gap = hist_img.shape[1]/hist.shape[0]             # 한 계급 너비

    for i, h in enumerate(hist.flat):
        x = int(round(i * gap))                         # 막대 사각형 시작 x 좌표
        w = int(round(gap))
        cv2.rectangle(hist_img, (x, 0, w, int(h)), 0, cv2.FILLED)
    return   cv2.flip(hist_img, 0)                        # 영상 상하 뒤집기 후 반환

def draw_hist_np(hist, shape=(200, 256)):
    hist_img = np.full(shape, 255, np.uint8)
    # not use cv2.normalize, but scale manually
    hist_max, hist_min = hist.max(), hist.min()
    gap = hist_img.shape[1]/hist.shape[0]
    min_val, max_val = 0, shape[0]

    for i, h in enumerate(hist.flat):
        x = int(round(i * gap))
        w = int(round(gap))
        # scale formula = (h - hist_min) * (max - min) / (hist_max - hist_min) + min
        h_scaled = int((h - hist_min) * (max_val - min_val) / (hist_max - hist_min) + min_val) if hist_max != hist_min else 0
        cv2.rectangle(hist_img, (x, 0, w, h_scaled), 0, cv2.FILLED)
    return cv2.flip(hist_img, 0)

image = cv2.imread("images/draw_hist.jpg", cv2.IMREAD_GRAYSCALE)  # 영상 읽기
if image is None: raise Exception("영상 파일 읽기 오류")
    
hist = cv2.calcHist([image], [0], None, [32], [0, 256])
hist_img = draw_histo(hist)

hist_np = cv2.calcHist([image], [0], None, [32], [0, 256])
hist_img_np = draw_hist_np(hist_np)

cv2.imshow("image", image)
cv2.imshow("hist_img", hist_img)
cv2.imshow("hist_img_np", hist_img_np)
cv2.waitKey(0)