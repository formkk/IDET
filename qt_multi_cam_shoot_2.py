# -*- coding: utf-8 -*-
import sys
import os
import cv2
import numpy as np
import datetime
from ctypes import *
from threading import Lock
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, QObject, pyqtSignal

sys.path.append("./MvImport")
from MvImport.MvCameraControl_class import *

SAVE_PATH = "./multi_cam_photos/"
TRIGGER_SOURCE = 0x0001
os.makedirs(SAVE_PATH, exist_ok=True)
FrameInfoCallBack = CFUNCTYPE(None, POINTER(c_ubyte), POINTER(MV_FRAME_OUT_INFO_EX), c_void_p)


class CameraSignals(QObject):
    update_image = pyqtSignal(int, int, np.ndarray)  # cam_idx, pos_idx, image
    update_filename = pyqtSignal(str)
    update_trigger_no = pyqtSignal(int)  # 新增信号
    update_system_info = pyqtSignal(str)  # 新增信号用于更新系统信息


class CameraController(QObject):
    def __init__(self, cam_idx, dev_info):
        super().__init__()
        self.cam_idx = cam_idx
        self.dev_info = dev_info
        self.cam = MvCamera()
        self.frame_counter = 1
        self.lock = Lock()
        self.is_grabbing = False
        self.signals = CameraSignals()
        self.recent_images = [None] * 4  # 固定4个位置存储图像
        self.current_pos = 0  # 当前写入位置

        # 初始化相机
        if self.cam.MV_CC_CreateHandle(dev_info) != 0:
            raise RuntimeError(f"Camera {cam_idx} 创建句柄失败")
        if self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0) != 0:
            raise RuntimeError(f"Camera {cam_idx} 连接失败")

        # 配置相机参数
        self._setup_camera_params()
        self._setup_hardware_trigger()
        self._setup_camera_params_int()
        self._setup_camera_params_bool()

        # 注册回调
        self.callback = FrameInfoCallBack(self.image_callback)
        if self.cam.MV_CC_RegisterImageCallBackEx(self.callback, None) != 0:
            raise RuntimeError(f"Camera {cam_idx} 注册回调失败")

    def _setup_camera_params(self):
        """配置曝光和增益"""
        params = [
            ("ExposureTime", 20000),
            ("Gain", 5),
            ("AcquisitionFrameRate", 5)
            # ("AcquisitionLineRateEnable", True)
        ]
        for param, value in params:
            if self.cam.MV_CC_SetFloatValue(param, value) != 0:
                raise RuntimeError(f"Camera {self.cam_idx} 设置{param}失败")

    def _setup_camera_params_int(self):
        params = [
            ("AcquisitionBurstFrameCount", 4)
        ]
        for param, value in params:
            if self.cam.MV_CC_SetIntValue(param, value) != 0:
                raise RuntimeError(f"Camera {self.cam_idx} 设置{param}失败")

    def _setup_camera_params_bool(self):
        params = [
            ("AcquisitionFrameRateEnable", True)
        ]
        for param, value in params:
            if self.cam.MV_CC_SetBoolValue(param, value) != 0:
                raise RuntimeError(f"Camera {self.cam_idx} 设置{param}失败")

    def _setup_hardware_trigger(self):
        """硬件触发配置"""
        params = [
            ("TriggerMode", MV_TRIGGER_MODE_ON),
            ("TriggerSource", 0),
            ("TriggerActivation", 0),
            ("AcquisitionMode", 2)  # 0: SingleFrame 1: MultiFrame 2: Continuous
        ]
        for param, value in params:
            if self.cam.MV_CC_SetEnumValue(param, value) != 0:
                raise RuntimeError(f"Camera {self.cam_idx} 设置{param}失败")

    def image_callback(self, pData, pFrameInfo, pUser):
        """图像回调函数（线程安全）"""
        frame_info = pFrameInfo.contents
        data_ptr = cast(pData, POINTER(c_ubyte * frame_info.nFrameLen))
        image_data = np.frombuffer(data_ptr.contents, dtype=np.uint8)

        # 图像格式转换
        if frame_info.enPixelType == 34603039:  # YUV422
            img = image_data.reshape((frame_info.nHeight, frame_info.nWidth, -1))
            img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_Y422)
        elif frame_info.enPixelType == 35127316:  # Mono8
            img = image_data.reshape((frame_info.nHeight, frame_info.nWidth))
            img = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB)
        else:
            print(f"不支持的像素格式: 0x{frame_info.enPixelType:x}")
            return

        # 存储到固定位置并更新UI
        with self.lock:
            pos = self.current_pos
            self.recent_images[pos] = img.copy()
            self.current_pos = (pos + 1) % 4

            # 发射信号更新UI（主线程安全）
            self.signals.update_image.emit(self.cam_idx, pos, img.copy())

        # 保存文件
        now = datetime.datetime.now()
        timestamp = now.strftime("%m%d_%H%M%S_") + f"{now.microsecond:06d}"[:4]
        trigger_no = (self.frame_counter - 1) // 4
        frame_no = (self.frame_counter + 1) % 4 + 1
        # filename = os.path.join(SAVE_PATH, f"cam{self.cam_idx}_trig_{timestamp}_cnt{self.frame_counter}.bmp")
        filename = os.path.join(SAVE_PATH, f"cam{self.cam_idx}_trig_{timestamp}_fn{frame_no}_tn{trigger_no}.bmp")
        cv2.imwrite(filename, img)
        self.frame_counter += 1
        self.signals.update_filename.emit(os.path.basename(filename))
        self.signals.update_trigger_no.emit(trigger_no)  # 发射更新trigger_no的信号

    def start_grabbing(self):
        if self.cam.MV_CC_StartGrabbing() == 0:
            self.is_grabbing = True
            info = f"Camera {self.cam_idx} 开始采集"
            print(info)
            self.signals.update_system_info.emit(info)  # 发射更新系统信息的信号
        else:
            error_info = f"Camera {self.cam_idx} 启动采集失败"
            print(error_info)
            self.signals.update_system_info.emit(error_info)  # 发射更新系统信息的信号

    def stop_grabbing(self):
        self.cam.MV_CC_StopGrabbing()
        self.is_grabbing = False
        info = f"Camera {self.cam_idx} 停止采集"
        print(info)
        self.signals.update_system_info.emit(info)  # 发射更新系统信息的信号

    def release(self):
        if self.is_grabbing:
            self.stop_grabbing()
        self.cam.MV_CC_CloseDevice()
        self.cam.MV_CC_DestroyHandle()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initCameras()

    def initUI(self):
        self.setWindowTitle('多相机触发显示')
        self.setGeometry(50, 50, 1800, 900)
        main_layout = QVBoxLayout()  # 修改为主垂直布局

        # 图像显示区域：每个相机4个位置
        left_layout = QVBoxLayout()
        self.image_grid = []  # [[cam0_label1, cam0_label2...], [cam1_label1...]]
        for cam_idx in range(2):  # 假设最多2个相机
            row = QHBoxLayout()
            labels = []
            for pos in range(4):
                label = QLabel()
                label.setFixedSize(360, 240)
                label.setAlignment(Qt.AlignCenter)
                row.addWidget(label)
                labels.append(label)
            self.image_grid.append(labels)
            left_layout.addLayout(row)

        # 右侧信息面板
        right_layout = QVBoxLayout()
        self.camera_info = QTextEdit()
        self.filenames = QTextEdit()
        self.trigger_no_label = QLabel()  # 新增用于显示trigger_no的标签
        font = QFont()
        font.setPointSize(24)
        self.trigger_no_label.setFont(font)
        self.trigger_no_label.setStyleSheet("color: red;")
        self.start_btn = QPushButton('开始采集')
        self.stop_btn = QPushButton('停止采集')

        # 系统信息显示区域
        self.system_info = QTextEdit()
        self.system_info.setReadOnly(True)

        # 设置 camera_info 高度为 8 行
        font_metrics_camera_info = self.camera_info.fontMetrics()
        line_height_camera_info = font_metrics_camera_info.lineSpacing()
        self.camera_info.setFixedHeight(line_height_camera_info * 8)

        # 设置 system_info 高度为 8 行
        font_metrics_system_info = self.system_info.fontMetrics()
        line_height_system_info = font_metrics_system_info.lineSpacing()
        self.system_info.setFixedHeight(line_height_system_info * 8)

        # 将系统信息显示区域添加到右侧布局的第2个位置
        right_layout.addWidget(self.camera_info)
        right_layout.addWidget(self.system_info)
        right_layout.addWidget(self.filenames)
        right_layout.addWidget(self.trigger_no_label)  # 添加到布局中
        right_layout.addWidget(self.start_btn)
        right_layout.addWidget(self.stop_btn)

        # 水平布局包含图像显示区域和右侧信息面板
        middle_layout = QHBoxLayout()
        # 调整左右布局的宽度占比，让右侧更宽
        middle_layout.addLayout(left_layout, 65)
        middle_layout.addLayout(right_layout, 35)

        # 将中间布局添加到主布局
        main_layout.addLayout(middle_layout)

        self.setLayout(main_layout)

        # 按钮事件
        self.start_btn.clicked.connect(self.startGrabbing)
        self.stop_btn.clicked.connect(self.stopGrabbing)
        self.stop_btn.setEnabled(False)

    def initCameras(self):
        MvCamera.MV_CC_Initialize()
        device_list = MV_CC_DEVICE_INFO_LIST()
        if MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, device_list) != 0:
            raise RuntimeError("未找到相机设备")

        self.controllers = []
        for i in range(device_list.nDeviceNum):
            dev_info = cast(device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            controller = CameraController(i, dev_info)
            # 连接信号到UI更新
            controller.signals.update_image.connect(self.updateImage)
            controller.signals.update_filename.connect(lambda name: self.filenames.append(name))
            controller.signals.update_trigger_no.connect(self.updateTriggerNo)  # 连接更新trigger_no的信号
            controller.signals.update_system_info.connect(self.updateSystemInfo)  # 连接更新系统信息的信号
            self.controllers.append(controller)
            # 显示相机信息
            if dev_info.nTLayerType == MV_GIGE_DEVICE:
                model_name = bytes(dev_info.SpecialInfo.stGigEInfo.chModelName).decode('utf-8').rstrip('\x00')
                serial_number = bytes(dev_info.SpecialInfo.stGigEInfo.chSerialNumber).decode('utf-8').rstrip('\x00')
            elif dev_info.nTLayerType == MV_USB_DEVICE:
                model_name = bytes(dev_info.SpecialInfo.stUsb3VInfo.chModelName).decode('utf-8').rstrip('\x00')
                serial_number = bytes(dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber).decode('utf-8').rstrip('\x00')
            else:
                model_name = "未知型号"
                serial_number = "未知序列号"
            info_str = f"相机{i}: 型号 - {model_name}, 序列号 - {serial_number}"
            self.camera_info.append(info_str)

    def updateImage(self, cam_idx, pos_idx, img):
        """更新指定相机的指定位置显示"""
        if cam_idx >= len(self.image_grid) or pos_idx >= 4:
            return
        label = self.image_grid[cam_idx][pos_idx]
        h, w, _ = img.shape
        bytes_per_line = 3 * w
        q_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img).scaled(label.width(), label.height(), Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

    def updateTriggerNo(self, trigger_no):
        """更新trigger_no的显示"""
        self.trigger_no_label.setText(f"Trigger No: {trigger_no}")

    def updateSystemInfo(self, info):
        """更新系统信息框的内容"""
        self.system_info.append(info)

    def startGrabbing(self):
        for c in self.controllers:
            try:
                c.start_grabbing()
            except Exception as e:
                print(f"启动失败: {e}")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stopGrabbing(self):
        for c in self.controllers:
            c.stop_grabbing()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def closeEvent(self, event):
        for c in self.controllers:
            c.release()
        MvCamera.MV_CC_Finalize()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

