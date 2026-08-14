#####################################################
##               Read bag from file                ##
#####################################################


# 首先导入库
import pyrealsense2 as rs
# 导入 NumPy，便于操作数组
import numpy as np
# 导入 OpenCV，便于渲染图像
import cv2
# 导入 argparse，处理命令行选项
import argparse
# 导入 os.path，处理文件路径
import os.path

# 创建用于解析命令行选项的对象
parser = argparse.ArgumentParser(description="Read recorded bag file and display depth stream in jet colormap.\
                                Remember to change the stream fps and format to match the recorded.")
# 添加参数：输入 bag 文件路径
parser.add_argument("-i", "--input", type=str, help="Path to the bag file")
# 将命令行参数解析为对象
args = parser.parse_args()
# 未提供参数时的保护处理
if not args.input:
    print("No input paramater have been given.")
    print("For help type --help")
    exit()
# 检查给定文件是否具有 .bag 扩展名
if os.path.splitext(args.input)[1] != ".bag":
    print("The given file is not of correct file format.")
    print("Only .bag files are accepted")
    exit()
try:
# 创建管线
    pipeline = rs.pipeline()

# 创建配置对象
    config = rs.config()

# 告知配置对象：使用文件中的录制设备，并通过回放供管线使用。
    rs.config.enable_device_from_file(config, args.input)

# 配置管线传输深度流
# 根据录制的 bag 文件分辨率修改这些参数
    config.enable_stream(rs.stream.depth, rs.format.z16, 30)

# 从文件开始数据流传输
    pipeline.start(config)

# 创建用于渲染图像的 OpenCV 窗口
    cv2.namedWindow("Depth Stream", cv2.WINDOW_AUTOSIZE)
    
# 创建伪彩色器对象
    colorizer = rs.colorizer()

# 数据流循环
    while True:
# 获取深度帧集
        frames = pipeline.wait_for_frames()

# 获取深度帧
        depth_frame = frames.get_depth_frame()

# 使用 Jet 色图对深度帧进行伪彩色处理
        depth_color_frame = colorizer.colorize(depth_frame)

# 将 depth_frame 转换为 NumPy 数组，以便通过 OpenCV 渲染
        depth_color_image = np.asanyarray(depth_color_frame.get_data())

# 在 OpenCV 窗口中渲染图像
        cv2.imshow("Depth Stream", depth_color_image)
        key = cv2.waitKey(1)
# 按下 Esc 键时退出程序
        if key == 27:
            cv2.destroyAllWindows()
            break

finally:
    pass
