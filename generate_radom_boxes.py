import random
import cv2
# from typing import List, Dict


def generate_cv_boxes(cv_image):
    # 获取图像尺寸 (OpenCV的height在前)
    height, width = cv_image.shape[:2]
    num_boxes = 3
    boxes = []
    for _ in range(num_boxes):
        # 生成随机坐标（保持浮点精度）
        x1 = round(random.uniform(0, width - 1), 5)  # 防止溢出右边界
        y1 = round(random.uniform(0, height - 1), 5)  # 防止溢出下边界
        x2 = round(random.uniform(x1, width), 5)
        y2 = round(random.uniform(y1, height), 5)

        boxes.append({
            "label": str(random.randint(1, 37)),
            "points": [[x1, y1], [x2, y2]]
        })

    return boxes


# 使用示例
if __name__ == "__main__":


    # 读取图像
    img = cv2.imread("example.bmp")
    if img is None:
        raise FileNotFoundError("测试图片加载失败")

    # 生成并打印结果
    result = generate_cv_boxes(img)
    import pdb; pdb.set_trace()
    print("Generated boxes:")
    for i, box in enumerate(result, 1):
        print(f"Box {i}: {box}")