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

# 图像保存路径
SAVE_PATH = "./photo/"
os.makedirs(SAVE_PATH, exist_ok=True)

# 全局变量线程安全控制
icount_lock = Lock()
icount_1 = 1

# ----------------------------------------------
# 回调函数实现图像捕获和保存
# ----------------------------------------------
FrameInfoCallBack = CFUNCTYPE(None, POINTER(c_ubyte), POINTER(MV_FRAME_OUT_INFO_EX), c_void_p)


def image_callback(pData, pFrameInfo, pUser):
    frame_info = pFrameInfo.contents
    print(f"\n捕获到帧: 宽[{frame_info.nWidth}], 高[{frame_info.nHeight}], 格式[{frame_info.enPixelType}]")

    # 转换图像数据
    data_ptr = cast(pData, POINTER(c_ubyte * frame_info.nFrameLen))
    image_data = np.frombuffer(data_ptr.contents, dtype=np.uint8)

    # 根据像素格式处理图像
    # import pdb;pdb.set_trace()
    if frame_info.enPixelType == 34603039:  # YUV422
        img = image_data.reshape((frame_info.nHeight, frame_info.nWidth, -1))
        img = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_Y422)
    elif frame_info.enPixelType == 0x01080001:  # Mono8
        img = image_data.reshape((frame_info.nHeight, frame_info.nWidth))
        img = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB)
    elif frame_info.enPixelType == 0x02180014:  # RGB8
        img = image_data.reshape((frame_info.nHeight, frame_info.nWidth, 3))
    else:
        print(f"不支持的像素格式: 0x{frame_info.enPixelType:x}")
        return

    # 生成唯一文件名
    timestamp = time.time()
    sec = int(timestamp)
    ms = int((timestamp - sec) * 1000)
    formatted_time = datetime.datetime.fromtimestamp(sec).strftime('%Y%m%d_%H%M%S')

    with icount_lock:
        global icount_1
        filename = os.path.join(SAVE_PATH, f"hw_trigger_{formatted_time}_{ms:04d}_{icount_1:04d}.bmp")
        icount_1 += 1

    cv2.imwrite(filename, img)
    print(f"已保存图像: {filename}")


# ----------------------------------------------
# 主程序流程
# ----------------------------------------------
def main():
    # 初始化SDK
    MvCamera.MV_CC_Initialize()

    try:
        # 枚举设备（原有代码，保持不变）
        device_list = MV_CC_DEVICE_INFO_LIST()
        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, device_list)
        if ret != 0 or device_list.nDeviceNum == 0:
            raise RuntimeError("未找到设备" if device_list.nDeviceNum == 0 else f"枚举设备失败 [0x{ret:x}]")

        ## 显示设备信息
        print(f"找到 {device_list.nDeviceNum} 个设备:")
        for i in range(device_list.nDeviceNum):
            dev_info = cast(device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            name = bytes(dev_info.SpecialInfo.stGigEInfo.chModelName).decode('utf-8').strip('\x00')
            print(f"[{i}] {name}")

        # 选择设备
        sel = int(input("输入要连接的设备编号: "))
        if sel < 0 or sel >= device_list.nDeviceNum:
            raise ValueError("无效的设备编号")

        # 创建相机实例
        global cam
        cam = MvCamera()
        dev_info = cast(device_list.pDeviceInfo[sel], POINTER(MV_CC_DEVICE_INFO)).contents

        # 创建句柄并连接
        if cam.MV_CC_CreateHandle(dev_info) != 0 or cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0) != 0:
            raise RuntimeError("设备连接失败")

        # 配置相机参数
        ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON)
        if cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON) != 0:
            raise RuntimeError("无法启用触发模式")

        cam.MV_CC_SetFloatValue("ExposureTime", float(10000))
        cam.MV_CC_SetFloatValue("Gain", float(5))

        # ----------------------------------------
        # 注册回调并开始采集
        # ----------------------------------------
        callback = FrameInfoCallBack(image_callback)
        if cam.MV_CC_RegisterImageCallBackEx(callback, None) != 0:
            raise RuntimeError("无法注册回调函数")

        if cam.MV_CC_StartGrabbing() != 0:
            raise RuntimeError("开始采集失败")

        print("\n硬件触发模式已就绪，等待外部触发信号...")

        # ----------------------------------------
        # 关键修改2：优化主循环（避免CPU空转）
        # ----------------------------------------
        try:
            while True:
                time.sleep(0.1)  # 降低CPU占用
        except KeyboardInterrupt:
            print("\n用户中断采集")

    except Exception as e:
        print(f"错误发生: {str(e)}")
    finally:
        if 'cam' in globals():
            cam.MV_CC_StopGrabbing()
            cam.MV_CC_CloseDevice()
            cam.MV_CC_DestroyHandle()
        MvCamera.MV_CC_Finalize()


if __name__ == "__main__":
    main()