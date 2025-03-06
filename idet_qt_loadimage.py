import sys
import json
import random
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QScrollArea
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


# 定义数字与中文说明的映射字典
LABEL_DICT = {
    "1": "色差",
    "2": "套印不准",
    "3": "字体残缺",
    "4": "点缺陷",
    "5": "擦花",
    "6": "亮印",
    "7": "墨杠",
    "8": "水杠",
    "9": "深度划痕",
    "10": "轻微划痕",
    "11": "爆刀爆线",
    "12": "爆色/脱漆",
    "13": "锯齿",
    "14": "易脆",
    "15": "超线/离线",
    "16": "除泡不实/气泡",
    "17": "凹凸点或凹凸包",
    "18": "折皱",
    "19": "PP边线泛白",
    "20": "分层 PP分层/纸张分层",
    "21": "PP膜破损、覆膜不全",
    "22": "折痕/压痕",
    "23": "脏污",
    "24": "粘贴开胶",
    "25": "面纸脱胶",
    "26": "溢胶",
    "27": "残胶/胶水痕",
    "28": "烫印掉粉",
    "29": "偏位",
    "30": "皱角/爆角",
    "31": "刀位同坑纸",
    "32": "成品掉粉",
    "33": "毛丝",
    "34": "除废不良",
    "35": "破损",
    "36": "V槽破损",
    "37": "灰板漏灰",
}


def simdefect_json(output_path="box.json"):
    # 生成有效边界框坐标‌:ml-citation{ref="1,2" data="citationList"}
    x1 = round(random.uniform(0, 1279), 2)
    y1 = round(random.uniform(0, 959), 2)
    x2 = round(random.uniform(x1, 1280), 2)  # 确保x2≥x1‌:ml-citation{ref="2,3" data="citationList"}
    y2 = round(random.uniform(y1, 960), 2)  # 确保y2≥y1‌:ml-citation{ref="2,3" data="citationList"}

    data = {
        "label": str(random.randint(1, 37)),  # 标签字符串化‌:ml-citation{ref="1,5" data="citationList"}
        "points": [
            [x1, y1],  # 左上角坐标
            [x2, y2]  # 右下角坐标
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)

    return data

def draw_annotations(image, shapes):
    """
    将标注绘制到图像上
    :param image: 输入的图像
    :param shapes: JSON文件中的shapes字段
    :return: 绘制后的图像
    """
    for shape in shapes:
        label = shape.get("label", "")
        points = shape.get("points", [])
        shape_type = shape.get("shape_type", "")
        import pdb; pdb.set_trace()

        if shape_type == "rectangle" and len(points) == 2:
            # 将点转换为整数类型
            pt1 = tuple(map(int, points[0]))
            pt2 = tuple(map(int, points[1]))
            # 绘制矩形
            cv2.rectangle(image, pt1, pt2, color=(0, 255, 0), thickness=2)
            # 在矩形上方绘制标签
            cv2.putText(image, label, (pt1[0], pt1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        else:
            print(f"Unsupported shape type: {shape_type} or invalid points: {points}")

    return image


def resize_image(image, width, height):
    """
    调整图像大小
    :param image: 输入的图像
    :param width: 目标宽度
    :param height: 目标高度
    :return: 调整大小后的图像
    """
    return cv2.resize(image, (width, height))


class ImageViewer(QWidget):
    """
    PyQt5 图像查看器
    """

    def __init__(self):
        super().__init__()
        self.image_path = None
        self.json_path = None
        self.init_ui()

    def init_ui(self):
        """
        初始化界面
        """
        self.setWindowTitle("MQ缺陷检测")
        self.setGeometry(100, 100, 1200, 600)  # 调整窗口大小
        self.setMinimumSize(1000, 500)  # 设置窗口最小大小

        # 设置背景颜色为深灰色
        self.setStyleSheet("background-color: #2E2E2E; color: white;")

        # 主布局：左右两栏
        main_layout = QHBoxLayout()

        # 左栏布局
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)  # 减少左栏的边距
        left_layout.setSpacing(10)  # 减少组件之间的间距

        # 载入文件按钮和关闭按钮
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("开始检测")
        self.load_button.setStyleSheet("background-color: #4A4A4A; color: white; padding: 10px; font-size: 16px;")
        self.load_button.clicked.connect(self.load_bmp)
        self.close_button = QPushButton("停止")
        self.close_button.setStyleSheet("background-color: #4A4A4A; color: white; padding: 10px; font-size: 16px;")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.close_button)
        left_layout.addLayout(button_layout)

        # 在标注区域上方增加说明“缺陷：”
        defect_label = QLabel("缺陷：")
        defect_label.setStyleSheet("font-size: 18px; font-weight: bold; color: orange;")
        left_layout.addWidget(defect_label)

        # 中部：显示所有 label 的值
        self.label_scroll_area = QScrollArea()
        self.label_scroll_area.setWidgetResizable(True)
        self.label_scroll_area.setStyleSheet("background-color: #2E2E2E; color: white;")
        self.label_container = QWidget()
        self.label_container.setStyleSheet("background-color: #2E2E2E; color: white;")
        self.label_layout = QVBoxLayout(self.label_container)
        self.label_scroll_area.setWidget(self.label_container)
        left_layout.addWidget(self.label_scroll_area)

        # 下方：显示“检测结果：”
        result_label = QLabel("检测结果：")
        result_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        left_layout.addWidget(result_label)

        # 显示“良品”或“NG”
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 36px; font-weight: bold;")
        left_layout.addWidget(self.status_label)

        # 设置左栏宽度
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setFixedWidth(300)  # 减少左栏宽度

        # 右栏布局：显示图像
        right_layout = QHBoxLayout()
        self.image_original_label = QLabel()
        self.image_original_label.setAlignment(Qt.AlignCenter)
        self.image_original_label.setStyleSheet("border: 2px solid #4A4A4A;")
        self.image_annotated_label = QLabel()
        self.image_annotated_label.setAlignment(Qt.AlignCenter)
        self.image_annotated_label.setStyleSheet("border: 2px solid #4A4A4A;")
        right_layout.addWidget(self.image_original_label)
        right_layout.addWidget(self.image_annotated_label)

        # 将左右栏添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addLayout(right_layout)

        # 设置主布局
        self.setLayout(main_layout)

    def load_bmp(self):
        """
        载入 BMP 文件并处理
        """
        # 打开文件对话框选择 BMP 文件
        self.image_path, _ = QFileDialog.getOpenFileName(self, "载入 BMP 文件", "", "BMP 文件 (*.bmp)")
        if not self.image_path:
            return

        # 清空之前的 label 和状态
        for i in reversed(range(self.label_layout.count())):
            self.label_layout.itemAt(i).widget().setParent(None)
        self.status_label.clear()

        # 查找同名的 JSON 文件
        json_path = os.path.splitext(self.image_path)[0] + ".json"
        if not os.path.exists(json_path):
            print(f"JSON 文件未找到: {json_path}")
            return

        # 读取 JSON 文件
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 显示所有 label 的值
        shapes = data.get("shapes", [])
        for shape in shapes:
            label = shape.get("label", "")
            if label:
                # 获取中文说明
                chinese_desc = LABEL_DICT.get(label, "未知")
                label_widget = QLabel(f" {label}: {chinese_desc}")
                label_widget.setStyleSheet("color: white; font-size: 14px;")  # 设置文字颜色和大小
                self.label_layout.addWidget(label_widget)

        # 读取图像
        image = cv2.imread(self.image_path)
        if image is None:
            print(f"Failed to load image: {self.image_path}")
            return

        # 绘制标注
        annotated_image = draw_annotations(image.copy(), shapes)

        # 调整图像大小
        resized_image = resize_image(image, 640, 480)
        resized_annotated_image = resize_image(annotated_image, 640, 480)

        # 将 OpenCV 图像转换为 QImage
        qimage_original = QImage(resized_image.data, resized_image.shape[1], resized_image.shape[0],
                                 QImage.Format_BGR888)
        qimage_annotated = QImage(resized_annotated_image.data, resized_annotated_image.shape[1],
                                  resized_annotated_image.shape[0], QImage.Format_BGR888)

        # 显示图像
        self.image_original_label.setPixmap(QPixmap.fromImage(qimage_original))
        self.image_annotated_label.setPixmap(QPixmap.fromImage(qimage_annotated))

        # 判断“良品”或“NG”
        if not shapes:  # 如果 shapes 列表为空
            self.status_label.setText("良品")
            self.status_label.setStyleSheet("font-size: 36px; font-weight: bold; color: green;")
        else:  # 如果 shapes 列表不为空
            self.status_label.setText("NG")
            self.status_label.setStyleSheet("font-size: 36px; font-weight: bold; color: red;")


if __name__ == "__main__":
    # 启动 PyQt5 应用
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())