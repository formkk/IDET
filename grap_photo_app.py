import sys
import os
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QWidget, QMessageBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

# from MvCameraControl_class import *  # 假设这是相机 SDK 的 Python 封装
sys.path.append("./MvImport")
from MvCameraControl_class import *

class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工业相机控制程序")
        self.setGeometry(100, 100, 800, 600)

        # 初始化相机相关变量
        self.cam = None
        self.device_list = None
        self.timer = QTimer()  # 用于定时获取图像

        # 创建 UI
        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout()

        # 左侧布局（设备列表和控制按钮）
        left_layout = QVBoxLayout()

        # 设备列表
        self.device_list_widget = QListWidget()
        left_layout.addWidget(self.device_list_widget)

        # 枚举设备按钮
        self.enum_devices_btn = QPushButton("枚举设备")
        self.enum_devices_btn.clicked.connect(self.enum_devices)
        left_layout.addWidget(self.enum_devices_btn)

        # 连接设备按钮
        self.connect_btn = QPushButton("连接设备")
        self.connect_btn.clicked.connect(self.connect_camera)
        left_layout.addWidget(self.connect_btn)

        # 开始采集按钮
        self.start_btn = QPushButton("开始采集")
        self.start_btn.clicked.connect(self.start_grabbing)
        left_layout.addWidget(self.start_btn)

        # 停止采集按钮
        self.stop_btn = QPushButton("停止采集")
        self.stop_btn.clicked.connect(self.stop_grabbing)
        left_layout.addWidget(self.stop_btn)

        # 右侧布局（图像显示）
        right_layout = QVBoxLayout()
        self.image_label = QLabel("图像显示区域")
        self.image_label.setScaledContents(True)
        right_layout.addWidget(self.image_label)

        # 将左右布局添加到主布局
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        # 设置主窗口的中心部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def enum_devices(self):
        """枚举设备并显示在列表中"""
        self.device_list_widget.clear()
        self.device_list = enum_devices(device=0, device_way=False)
        if self.device_list:
            for i in range(self.device_list.nDeviceNum):
                device_info = self.device_list.pDeviceInfo[i]
                self.device_list_widget.addItem(f"设备 {i}: {device_info}")

    def connect_camera(self):
        """连接选中的设备"""
        selected_item = self.device_list_widget.currentRow()
        if selected_item >= 0:
            self.cam, _ = creat_camera(self.device_list, selected_item, log=False)
            open_device(self.cam)
            QMessageBox.information(self, "提示", "设备连接成功！")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个设备！")

    def start_grabbing(self):
        """开始采集图像"""
        if self.cam:
            start_grab_and_get_data_size(self.cam)
            self.timer.timeout.connect(self.update_image)
            self.timer.start(30)  # 每 30ms 更新一次图像
        else:
            QMessageBox.warning(self, "警告", "请先连接设备！")

    def stop_grabbing(self):
        """停止采集图像"""
        if self.cam:
            self.timer.stop()
            close_and_destroy_device(self.cam)
            self.cam = None
            QMessageBox.information(self, "提示", "设备已断开连接！")
        else:
            QMessageBox.warning(self, "警告", "设备未连接！")

    def update_image(self):
        """更新图像显示"""
        if self.cam:
            stOutFrame = MV_FRAME_OUT()
            memset(byref(stOutFrame), 0, sizeof(stOutFrame))
            ret = self.cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if ret == 0 and stOutFrame.pBufAddr:
                # 将图像数据转换为 OpenCV 格式
                if stOutFrame.stFrameInfo.enPixelType == 17301505:  # Mono8
                    image = np.frombuffer(
                        (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight).from_address(
                            stOutFrame.pBufAddr),
                        dtype=np.uint8
                    ).reshape(stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth)
                elif stOutFrame.stFrameInfo.enPixelType == 17301514:  # BayerGB8
                    image = np.frombuffer(
                        (c_ubyte * stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight).from_address(
                            stOutFrame.pBufAddr),
                        dtype=np.uint8
                    ).reshape(stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth)
                    image = cv2.cvtColor(image, cv2.COLOR_BAYER_GB2RGB)
                else:
                    return

                # 将 OpenCV 图像转换为 QImage
                height, width = image.shape[:2]
                bytes_per_line = 3 * width if len(image.shape) == 3 else width
                q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                self.image_label.setPixmap(QPixmap.fromImage(q_img))

                # 释放缓冲区
                self.cam.MV_CC_FreeImageBuffer(stOutFrame)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())