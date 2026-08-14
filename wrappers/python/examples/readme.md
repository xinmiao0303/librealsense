# RealSense Python 封装示例代码

这些示例演示如何使用 SDK 的 Python 封装。

## 示例列表

1. [教程 1](./python-tutorial-1-depth.py) - 演示如何从相机启动深度帧传输，并在控制台中以 ASCII 字符画显示图像。
2. [NumPy 和 OpenCV](./opencv_viewer_example.py) - 使用 OpenCV 和 NumPy 渲染深度图像与彩色图像的示例。
3. [数据流对齐](./align-depth2color.py) - 通过将深度图像对齐到彩色图像，并进行简单计算以去除背景的示例。
4. [RS400 高级模式](./python-rs400-advanced-mode-example.py) - 使用高级模式接口控制 D400 系列相机不同选项的示例。
5. [RealSense 后端](./pybackend_example_1_general.py) - 使用后端接口控制设备的示例。
6. [读取 bag 文件](./read_bag_example.py) - 读取 bag 文件，并使用伪彩色器以 Jet 色图显示录制深度流的示例。
7. [多相机箱体尺寸测量](./box_dimensioner_multicam/box_dimensioner_multicam_demo.py) - 使用多台相机计算物体长、宽、高的简单示例。
8. [D400 自校准演示](./depth_auto_calibration_example.py) - 提供 D400 自校准流程的参考实现。脚本依次执行片上校准、焦距校准和标定校准。有关校准方法的详细说明，请参阅[白皮书](https://dev.realsenseai.com/docs/self-calibration-for-depth-cameras)。
9. [NumPy 转帧](./numpy_to_frame.py) - 使用软件设备将 NumPy 数组转换为 pyrealsense 帧的示例。
10. [使用软件设备进行数据流对齐](./align-with-software-device.py) - 使用软件设备对齐深度图像和 RGB 图像的示例。
## 点云可视化

1. [OpenCV 软件渲染器](https://github.com/realsenseai/librealsense/blob/development/wrappers/python/examples/opencv_pointcloud_viewer.py)
2. [PyGlet 点云渲染器](https://github.com/realsenseai/librealsense/blob/development/wrappers/python/examples/pyglet_pointcloud_viewer.py) - 需要执行 `pip install pyglet`

## 交互式示例

1. [物体距离](https://github.com/realsenseai/librealsense/blob/jupyter/notebooks/distance_to_object.ipynb) [![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/realsenseai/librealsense/jupyter?filepath=notebooks/distance_to_object.ipynb)
2. [深度滤波器](https://github.com/realsenseai/librealsense/blob/jupyter/notebooks/depth_filters.ipynb) [![Binder](https://mybinder.org/v2/gh/realsenseai/librealsense/jupyter?filepath=notebooks/depth_filters.ipynb)
