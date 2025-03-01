import cv2
image = cv2.imread("./111.bmp", 1)

#txt_img = np.zeros((height, width, channels), dtype=np.uint8)

font = cv2.FONT_HERSHEY_SIMPLEX

txt1 = f"File: 1"

cv2.putText(image, txt1, (100, 300), font, 2, (0, 200, 0), 8)
cv2.imshow("1",image)
cv2.imwrite("txt.bmp",image)
import pdb;pdb.set_trace()

