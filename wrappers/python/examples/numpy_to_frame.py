# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2025 RealSense, Inc. All Rights Reserved.

import numpy as np
import pyrealsense2 as rs
import cv2

W = 640
H = 480
BPP = {'depth': 2, 'color': 3}  # z16 和 bgr8 格式的每像素字节数


def create_video_stream(mode):
    vs = rs.video_stream()
    if mode == 'depth':
        vs.type, vs.fmt = rs.stream.depth, rs.format.z16
    else:
        vs.type, vs.fmt = rs.stream.color, rs.format.bgr8
    vs.width, vs.height = W, H
# 可在此设置其他属性（如 fps、uid）
    return vs


def create_frame(np_frame, mode, stream_profile):
    frame = rs.software_video_frame()
    frame.pixels = np_frame.data
    frame.bpp = BPP[mode]
    frame.profile = stream_profile.as_video_stream_profile()
    frame.stride = W * BPP[mode]
# 可在此设置其他帧属性（如时间戳、帧号）
    return frame


class NumpyToFrame:
    def __init__(self, mode='depth'):
        """
        mode: 'depth' or 'color'
        """
        self.mode = mode.lower()
        if self.mode not in BPP:
            raise ValueError("Invalid mode. Choose 'depth' or 'color'.")

        self.queue = rs.frame_queue(100)
        self.dev = rs.software_device()
        self.sensor = self.dev.add_sensor(self.mode.capitalize())  # “Depth”或“Color”
        self.stream = self.sensor.add_video_stream(create_video_stream(self.mode))

        self.sensor.open(self.stream)
        self.sensor.start(self.queue)

    def __del__(self):
        self.sensor.stop()
        self.sensor.close()

    def convert(self, numpy_array):
# 将数组注入传感器
        self.sensor.on_video_frame(create_frame(numpy_array, self.mode, self.stream))
# 从帧队列中以帧的形式获取该数组
        frame = self.queue.wait_for_frame()
        return frame.as_depth_frame() if self.mode == 'depth' else frame.as_video_frame()


# =========================================================================
# 基本思路是：将 NumPy 数组传入软件设备并进行传输，以获取帧，流程如下：
# 帧 → NumPy 数组（及其修改结果）→ 帧（使用软件设备）
# =========================================================================
# 为该示例配置深度帧和彩色帧
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, W, H, rs.format.z16, 30)
config.enable_stream(rs.stream.color, W, H, rs.format.bgr8, 30)
pipeline.start(config)
frameset = pipeline.wait_for_frames()
depth_frame = frameset.get_depth_frame()
color_frame = frameset.get_color_frame()
pipeline.stop()
# =========================================================================
# 水平翻转深度帧的示例
np_depth = np.asanyarray(depth_frame.get_data())
modified_depth = np.ascontiguousarray(np_depth[:, ::-1])

numpy_to_depth_frame = NumpyToFrame(mode='depth')
converted_depth_frame = numpy_to_depth_frame.convert(modified_depth)

# 对深度帧，可将修改后的帧传给 calculate()：
pc = rs.pointcloud()
pc.calculate(converted_depth_frame)
print("Depth conversion test:", np.array_equal(modified_depth, np.asanyarray(converted_depth_frame.get_data())))

# =========================================================================
# 水平翻转彩色帧的示例
np_color = np.asanyarray(color_frame.get_data())
modified_color = np.ascontiguousarray(np_color[:, ::-1])

numpy_to_color_frame = NumpyToFrame(mode='color')
converted_color_frame = numpy_to_color_frame.convert(modified_color)
print("Color conversion test:", np.array_equal(modified_color, np.asanyarray(converted_color_frame.get_data())))

cv2.imshow("Color Frame Conversion - Original vs converted",
           cv2.hconcat([np_color, np.ones((np_color.shape[0], 50, np_color.shape[2]), dtype=np_color.dtype),
                        np.asanyarray(converted_color_frame.get_data())]))
cv2.waitKey(0)
