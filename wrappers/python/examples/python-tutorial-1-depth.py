## 许可证：Apache 2.0。请参阅根目录中的 LICENSE 文件。
## 版权所有(c) 2015-2017 RealSense, Inc. 保留所有权利。

#####################################################
## librealsense 教程 #1 - 访问深度数据 ##
#####################################################

# 首先导入库
import pyrealsense2 as rs

try:
    # 创建上下文对象。该对象拥有所有已连接 RealSense 设备的句柄
    pipeline = rs.pipeline()

    # 配置数据流
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    # 开始数据流传输
    pipeline.start(config)

    while True:
        # 此调用会等待，直到设备上有一组新的连贯帧可用
        # 在调用 wait_for_frames(...) 之前，对设备调用 get_frame_data(...) 和 get_frame_timestamp(...) 会返回稳定的值
        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()
        if not depth: continue

        # 将图像划分为 10×20 像素区域，并估算一米范围内像素的覆盖率，以打印简单的文本图像表示
        coverage = [0]*64
        for y in range(480):
            for x in range(640):
                dist = depth.get_distance(x, y)
                if 0 < dist and dist < 1:
                    coverage[x//10] += 1
            
            if y%20 is 19:
                line = ""
                for c in coverage:
                    line += " .:nhBXWW"[c//25]
                coverage = [0]*64
                print(line)
    exit(0)
#except rs.error as e:
#    # 对 librealsense 对象的方法调用可能会抛出 pylibrs.error 类型的异常
#    print("pylibrs.error was thrown when calling %s(%s):\n", % (e.get_failed_function(), e.get_failed_args()))
#    print("    %s\n", e.what())
#    exit(1)
except Exception as e:
    print(e)
    pass
