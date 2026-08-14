## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2025 RealSense, Inc. All Rights Reserved.
#####################################################################################################
#                                                                                                  ##
#    在软件设备中使用预采集图像将深度图对齐到彩色图                                               ##
#                                                                                                  ##
##  目的：                                                                                         ##
##    本示例先从 RealSense 相机采集深度与彩色图像，再在软件设备中使用预采集图像进行深度对齐。    ##
##                                                                                                 ##
##  步骤：                                                                                         ##
##    1) 传输深度 640×480@30fps 与彩色 1280×720@30fps 图像；                                      ##
##    2) 获取相机深度和彩色流的内参、外参；                                                       ##
##    3) 采集深度和彩色图像，并以 npy 格式保存；                                                  ##
##    4) 使用保存的内参、外参、深度和彩色图像构建软件设备；                                       ##
##    5) 将预采集深度图像对齐到彩色图像。                                                         ##
##                                                                                                 ##
#####################################################################################################

import logging
import cv2
import pyrealsense2 as rs
import numpy as np
import os
import time

fps = 30                  # 帧率
tv = 1000.0 / fps         # 帧之间的时间间隔（毫秒）

max_num_frames  = 100      # 保存为 npy 文件并由软件设备处理的最大帧集数

depth_file_name = "depth"  # depth_file_name + str(i) + ".npy"
color_file_name = "color"  # color_file_name + str(i) + ".npy"

# 从相机获取内参和外参
camera_depth_intrinsics          = rs.intrinsics()  # 相机深度流内参
camera_color_intrinsics          = rs.intrinsics()  # 相机彩色流内参
camera_depth_to_color_extrinsics = rs.extrinsics()  # 相机深度到彩色流的外参


######################## start of first part - capture images from live device #######################################
# 从已连接的 RealSense 相机传输深度和彩色流，并将帧以 npy 格式保存到文件
try:
# 创建上下文对象；该对象持有所有已连接 RealSense 设备的句柄
    ctx = rs.context()
    devs = list(ctx.query_devices())
    
    if len(devs) > 0:
        print("Devices: {}".format(devs))
    else:
        print("No camera detected. Please connect a realsense camera and try again.")
        exit(0)
    
    pipeline = rs.pipeline()

# 配置数据流
    config = rs.config()
    config.enable_stream(rs.stream.depth)
    config.enable_stream(rs.stream.color)

# 开始数据流传输
    cfg = pipeline.start(config)
    
# 获取深度比例尺
    depth_sensor = cfg.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()

# 获取内参
    camera_depth_profile = cfg.get_stream(rs.stream.depth)                                      # 获取深度流配置文件
    camera_depth_intrinsics = camera_depth_profile.as_video_stream_profile().get_intrinsics()   # 向下转换为 video_stream_profile 并获取内参
    
    camera_color_profile = cfg.get_stream(rs.stream.color)                                      # 获取彩色流配置文件
    camera_color_intrinsics = camera_color_profile.as_video_stream_profile().get_intrinsics()   # 向下转换为 video_stream_profile 并获取内参
    
    camera_depth_to_color_extrinsics = camera_depth_profile.get_extrinsics_to(camera_color_profile)
 

    print("camera depth intrinsic:", camera_depth_intrinsics)
    print("camera color intrinsic:", camera_color_intrinsics)
    print("camera depth to color extrinsic:", camera_depth_to_color_extrinsics)

    print("streaming attached camera and save depth and color frames into files in npy format ...")

    i = 0
    while i < max_num_frames:
# 等待设备提供一组新的时间同步帧
        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()
        color = frames.get_color_frame()

# 确认两帧都有效
        if not depth or not color:
            continue
        
# 将图像转换为 NumPy 数组
        depth_image = np.asanyarray(depth.get_data())
        color_image = np.asanyarray(color.get_data())
# 以 npy 格式保存图像
        depth_file = depth_file_name + str(i) + ".npy"
        color_file = color_file_name + str(i) + ".npy"
        print("saving frame set ", i, depth_file, color_file)
        
        with open(depth_file, 'wb') as f1:
            np.save(f1,depth_image)
        
        with open(color_file, 'wb') as f2:
            np.save(f2,color_image)

# 下一组帧
        i = i +1

except Exception as e:
    logging.error("An error occurred: %s", e, exc_info=True)
    exit(1)

######################## end of first part - capture images from live device #######################################



######################## start of second part - align depth to color in software device #############################
# 在软件设备中使用上面预采集的图像，将深度图对齐到彩色图

# 软件设备
sdev = rs.software_device()

# 软件深度传感器
depth_sensor: rs.software_sensor = sdev.add_sensor("Depth")

# 深度流内参
depth_intrinsics = rs.intrinsics()

depth_intrinsics.width  = camera_depth_intrinsics.width
depth_intrinsics.height = camera_depth_intrinsics.height

depth_intrinsics.ppx = camera_depth_intrinsics.ppx
depth_intrinsics.ppy = camera_depth_intrinsics.ppy

depth_intrinsics.fx = camera_depth_intrinsics.fx
depth_intrinsics.fy = camera_depth_intrinsics.fy

depth_intrinsics.coeffs = camera_depth_intrinsics.coeffs       ## [0.0, 0.0, 0.0, 0.0, 0.0]
depth_intrinsics.model = camera_depth_intrinsics.model         ## rs.pyrealsense2.distortion.brown_conrady

# 深度流
depth_stream = rs.video_stream()
depth_stream.type = rs.stream.depth
depth_stream.width = depth_intrinsics.width
depth_stream.height = depth_intrinsics.height
depth_stream.fps = fps
depth_stream.bpp = 2                              # 深度 z16 格式每像素 2 字节
depth_stream.fmt = rs.format.z16
depth_stream.intrinsics = depth_intrinsics
depth_stream.index = 0
depth_stream.uid = 1

depth_profile = depth_sensor.add_video_stream(depth_stream)

# 软件彩色传感器
color_sensor: rs.software_sensor = sdev.add_sensor("Color")

# 彩色流内参：
color_intrinsics = rs.intrinsics()
color_intrinsics.width = camera_color_intrinsics.width
color_intrinsics.height = camera_color_intrinsics.height

color_intrinsics.ppx = camera_color_intrinsics.ppx
color_intrinsics.ppy = camera_color_intrinsics.ppy

color_intrinsics.fx = camera_color_intrinsics.fx
color_intrinsics.fy = camera_color_intrinsics.fy

color_intrinsics.coeffs = camera_color_intrinsics.coeffs
color_intrinsics.model = camera_color_intrinsics.model

color_stream = rs.video_stream()
color_stream.type = rs.stream.color
color_stream.width = color_intrinsics.width
color_stream.height = color_intrinsics.height
color_stream.fps = fps
color_stream.bpp = 3                                # 本示例的彩色流 rgb8 格式每像素 3 字节
color_stream.fmt = rs.format.rgb8
color_stream.intrinsics = color_intrinsics
color_stream.index = 0
color_stream.uid = 2

color_profile = color_sensor.add_video_stream(color_stream)

# 深度到彩色流的外参；等同于 depth_profile.get_extrinsics_to(other_profile)
depth_to_color_extrinsics = rs.extrinsics()
depth_to_color_extrinsics.rotation = camera_depth_to_color_extrinsics.rotation
depth_to_color_extrinsics.translation = camera_depth_to_color_extrinsics.translation
depth_profile.register_extrinsics_to(color_profile, depth_to_color_extrinsics)

# 启动软件传感器
depth_sensor.open(depth_profile)
color_sensor.open(color_profile)

# 同步深度流和彩色流的帧
camera_syncer = rs.syncer()
depth_sensor.start(camera_syncer)
color_sensor.start(camera_syncer)

# 创建深度对齐对象
# rs.align 可将深度帧对齐到其他帧
# “align_to”是要将深度帧对齐到的目标流类型
# 将深度帧对齐到彩色帧
align_to = rs.stream.color
align = rs.align(align_to)

# 用于渲染深度图的伪彩色器
colorizer = rs.colorizer()

paused = False

# 遍历预采集的帧
for i in range(0, max_num_frames):
    print("\nframe set:", i)
    
# 预采集的深度和彩色图像文件（npy 格式）
    df = depth_file_name + str(i) + ".npy"
    cf = color_file_name + str(i) + ".npy"

    if (not os.path.exists(cf)) or (not os.path.exists(df)): continue

# 从预采集的 npy 文件加载深度帧
    print('loading depth frame ', df)
    depth_npy = np.load(df, mmap_mode='r')

# 创建软件深度帧
    depth_swframe = rs.software_video_frame()
    depth_swframe.stride = depth_stream.width * depth_stream.bpp
    depth_swframe.bpp = depth_stream.bpp
    depth_swframe.timestamp = i * tv
    depth_swframe.pixels = depth_npy
    depth_swframe.domain = rs.timestamp_domain.hardware_clock
    depth_swframe.frame_number = i
    depth_swframe.profile = depth_profile.as_video_stream_profile()
    depth_swframe.depth_units = depth_scale
    depth_sensor.on_video_frame(depth_swframe)

# 从预采集的 npy 文件加载彩色帧
    print('loading color frame ', cf)
    color_npy = np.load(cf, mmap_mode='r')
 
# 创建软件彩色帧
    color_swframe = rs.software_video_frame()
    color_swframe.stride = color_stream.width * color_stream.bpp
    color_swframe.bpp = color_stream.bpp
    color_swframe.timestamp = i * tv
    color_swframe.pixels = color_npy
    color_swframe.domain = rs.timestamp_domain.hardware_clock
    color_swframe.frame_number = i
    color_swframe.profile = color_profile.as_video_stream_profile()
    color_sensor.on_video_frame(color_swframe)
    
# 同步深度帧和彩色帧，并接收为帧集
    frames = camera_syncer.wait_for_frames()
    print("frame set:", frames.size(), " ", frames)

# 获取未对齐的深度帧
    unaligned_depth_frame = frames.get_depth_frame()
    if not unaligned_depth_frame: continue

# 将深度帧对齐到彩色帧
    aligned_frames = align.process(frames)

    aligned_depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()

    if (not aligned_depth_frame) or (not color_frame): continue

    aligned_depth_frame = colorizer.colorize(aligned_depth_frame)    
    npy_aligned_depth_image = np.asanyarray(aligned_depth_frame.get_data())

    npy_color_image = np.asanyarray(color_frame.get_data())

# 渲染对齐后的图像：
# 深度图对齐到彩色图；左侧为对齐深度图，右侧为彩色图
    images = np.hstack((npy_aligned_depth_image, npy_color_image))
    cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
    cv2.imshow('Align Example', images)
    key = cv2.waitKey(1)

# 渲染原始未对齐深度图，作为参考
    # colorized_unaligned_depth_frame = colorizer.colorize(unaligned_depth_frame)
    # npy_unaligned_depth_image = np.asanyarray(colorized_unaligned_depth_frame.get_data())
    # cv2.imshow("Unaligned Depth", npy_unaligned_depth_image)
    
# 按 Enter 或空格键，使图像窗口暂停 5 秒

    if key == 13 or key == 32: paused = not paused
        
    if paused:
        print("Paused for 5 seconds ...", i, ", press ENTER or SPACEBAR key anytime for additional pauses.")
        time.sleep(5)
        paused = not paused

# 第二部分结束：在软件设备中使用预采集图像将深度图对齐到彩色图
######################## End of second part - align depth to color in software device #############################
    
cv2.destroyAllWindows()
