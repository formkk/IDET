# -*- coding: utf-8 -*-
import sys
import os
import cv2
import numpy as np
import time
import datetime
from ctypes import *
from threading import Lock
sys.path.append("./MvImport")
from MvImport.MvCameraControl_class import *

# 全局配置
SAVE_PATH = "./multi_cam_photos/"
os.makedirs(SAVE_PATH, exist_ok=True)
TRIGGER_SOURCE = 0x0001  # 假设所有相机使用Line0作为触发源
FrameInfoCallBack = CFUNCTYPE(None, POINTER(c_ubyte), POINTER(MV_FRAME_OUT_INFO_EX), c_void_p)

class CameraController:
    def __init__(self, cam_idx, dev_info):
        self.cam_idx = cam_idx
        self.dev_info = dev_info
        self.cam = MvCamera()
        self.frame_counter = 1
        self.lock = Lock()
        self.is_grabbing = False

        # 初始化相机实例
        if self.cam.MV_CC_CreateHandle(dev_info) != 0:
            raise RuntimeError(f"Camera {cam_idx} 创建句柄失败")
        if self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0) != 0:
            raise RuntimeError(f"Camera {cam_idx} 连接失败")

        # 配置硬件触发
        self._setup_hardware_trigger()

        # 注册回调
        self.callback = FrameInfoCallBack(self.image_callback)
        if self.cam.MV_CC_RegisterImageCallBackEx(self.callback, None) != 0:
            raise RuntimeError(f"Camera {cam_idx} 注册回调失败")

    def _setup_hardware_trigger(self):
        """配置硬件触发参数"""
        params = [
            ("TriggerMode", MV_TRIGGER_MODE_ON)
            # ("TriggerSource", TRIGGER_SOURCE)
            # ("TriggerActivation", MV_TRIGGER_ACTIVATION_RISINGEDGE)
        ]
        for param, value in params:
            if self.cam.MV_CC_SetEnumValue(param, value) != 0:
                raise RuntimeError(f"Camera {self.cam_idx} 设置{param}失败")

    def start_grabbing(self):
        if self.cam.MV_CC_StartGrabbing() == 0:
            self.is_grabbing = True
            print(f"Camera {self.cam_idx} 开始采集")
        else:
            raise RuntimeError(f"Camera {self.cam_idx} 启动采集失败")

    def stop_grabbing(self):
        self.cam.MV_CC_StopGrabbing()
        self.is_grabbing = False

    def image_callback(self, pData, pFrameInfo, pUser):
        frame_info = pFrameInfo.contents
        print(f"Camera {self.cam_idx} 捕获帧: {frame_info.nFrameNum}")

        # 图像数据转换（根据实际格式调整）
        data_ptr = cast(pData, POINTER(c_ubyte * frame_info.nFrameLen))
        image_data = np.frombuffer(data_ptr.contents, dtype=np.uint8)
        if frame_info.enPixelType == 34603039:  # YUV422
            img = image_data.reshape((frame_info.nHeight, frame_info.nWidth, -1))
            img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_Y422)
        elif frame_info.enPixelType == 35127316:  # Mono8
            img = image_data.reshape((frame_info.nHeight, frame_info.nWidth))
            img = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB)
        elif frame_info.enPixelType == 17301505:  # RGB8
            img = image_data.reshape((frame_info.nHeight, frame_info.nWidth, 3))
        else:
            print(f"不支持的像素格式: 0x{frame_info.enPixelType:x}")
            return

        # 生成唯一文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        with self.lock:
            filename = os.path.join(
                SAVE_PATH,
                f"cam{self.cam_idx}_trig_{timestamp}_cnt{self.frame_counter}.bmp"
            )
            self.frame_counter += 1

        cv2.imwrite(filename, img)
        print(f"Camera {self.cam_idx} 保存: {filename}")

    def release(self):
        if self.is_grabbing:
            self.stop_grabbing()
        self.cam.MV_CC_CloseDevice()
        self.cam.MV_CC_DestroyHandle()

def main():
    # 初始化SDK
    MvCamera.MV_CC_Initialize()

    # 枚举所有设备
    device_list = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, device_list)
    if ret != 0 or device_list.nDeviceNum == 0:
        MvCamera.MV_CC_Finalize()
        raise RuntimeError("未找到可用设备")

    # 创建并初始化所有相机控制器
    controllers = []
    try:
        for i in range(device_list.nDeviceNum):
            dev_info = cast(device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            controller = CameraController(cam_idx=i, dev_info=dev_info)
            controller.start_grabbing()
            controllers.append(controller)
            print(f"已连接相机 {i}: {dev_info.SpecialInfo.stGigEInfo.chSerialNumber}")

        print("\n所有相机已就绪，等待硬件触发信号...")
        while True:
            time.sleep(1)  # 主线程保持运行

    except KeyboardInterrupt:
        print("\n用户终止采集")
    finally:
        for controller in controllers:
            controller.release()
        MvCamera.MV_CC_Finalize()

if __name__ == "__main__":
    main()