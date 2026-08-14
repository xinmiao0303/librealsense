## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2017 RealSense, Inc. All Rights Reserved.

#####################################################
##              Align Depth to Color               ##
#####################################################

# 首先导入库
import pyrealsense2 as rs
# 导入 NumPy，便于操作数组
import numpy as np
# 导入 OpenCV，便于渲染图像
import cv2

# 创建管线
pipeline = rs.pipeline()

# 创建配置对象，并配置管线传输不同分辨率的彩色流和深度流
config = rs.config()

# 获取设备产品线，以便设置其支持的分辨率
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
device_product_line = str(device.get_info(rs.camera_info.product_line))

found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# 开始数据流传输
profile = pipeline.start(config)

# 获取深度传感器的深度比例尺（说明参见 rs-align 示例）
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)

# 将移除距离超过 clipping_distance_in_meters 米的物体背景
clipping_distance_in_meters = 1 # 1 米
clipping_distance = clipping_distance_in_meters / depth_scale

# 创建对齐对象
# rs.align 可将深度帧对齐到其他帧
# “align_to” 是要将深度帧对齐到的目标流类型。
align_to = rs.stream.color
align = rs.align(align_to)

# 数据流循环
try:
    while True:
# 获取包含彩色帧和深度帧的帧集
        frames = pipeline.wait_for_frames()
# frames.get_depth_frame() 返回 640×360 的深度图像

# 将深度帧对齐到彩色帧
        aligned_frames = align.process(frames)

# 获取对齐后的帧
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame 是 640×480 的深度图像
        color_frame = aligned_frames.get_color_frame()

# 确认两帧都有效
        if not aligned_depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

# 移除背景：将距离大于裁剪距离的像素设为灰色
        grey_color = 153
        depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) # 深度图像为单通道，彩色图像为三通道
        bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), grey_color, color_image)

# 渲染图像：
# 左侧为对齐到彩色图像的深度图像，右侧为彩色图像
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        images = np.hstack((bg_removed, depth_colormap))

        cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
        cv2.imshow('Align Example', images)
        key = cv2.waitKey(1)
# 按 Esc 或 “q” 关闭图像窗口
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
finally:
    pipeline.stop()
