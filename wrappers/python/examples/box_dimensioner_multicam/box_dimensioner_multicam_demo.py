###########################################################################################################################
##                          许可证：Apache 2.0。请参阅根目录中的 LICENSE 文件。                                        ##
###########################################################################################################################
##                            多相机简单箱体尺寸测量：主示例文件                                                        ##
###########################################################################################################################
## 工作流程：                                                                                                            ##
## 1. 将标定棋盘置于所有 RealSense 相机的视野中；若使用其他尺寸，请更新脚本中的棋盘参数。                              ##
## 2. 启动程序。                                                                                                        ##
## 3. 等待标定完成；程序提示时，将待测物体放在标定板上。物体的长和宽不得超过标定板。                                   ##
## 4. 程序将以毫米显示物体包围盒的长、宽、高。                                                                          ##
###########################################################################################################################

# 导入 RealSense、OpenCV 和 NumPy
import pyrealsense2 as rs
import cv2
import numpy as np

# 导入封装 RealSense、OpenCV 和 Kabsch 校准操作的辅助函数与类
from collections import defaultdict
from realsense_device_manager import DeviceManager
from calibration_kabsch import PoseEstimation
from helper_functions import get_boundary_corners_2D
from measurement_task import calculate_boundingbox_points, calculate_cumulative_pointcloud, visualise_measurements

def run_demo():

# 定义常量
	resolution_width = 1280 # pixels
	resolution_height = 720 # pixels
	frame_rate = 15  # fps

	dispose_frames_for_stablisation = 30  # frames

	chessboard_width = 6 # squares
	chessboard_height = 9 	# squares
	square_size = 0.0253 # meters

	try:
# 启用所有 Intel RealSense 设备的数据流
		rs_config = rs.config()
		rs_config.enable_stream(rs.stream.depth, resolution_width, resolution_height, rs.format.z16, frame_rate)
		rs_config.enable_stream(rs.stream.infrared, 1, resolution_width, resolution_height, rs.format.y8, frame_rate)
		rs_config.enable_stream(rs.stream.color, resolution_width, resolution_height, rs.format.bgr8, frame_rate)

# 使用设备管理器类启用设备并获取帧
		device_manager = DeviceManager(rs.context(), rs_config)
		device_manager.enable_all_devices()

# 预留若干帧，使自动曝光控制器稳定下来
		for frame in range(dispose_frames_for_stablisation):
			frames = device_manager.poll_frames()

		assert( len(device_manager._available_devices) > 0 )
		"""
		1: Calibration
		Calibrate all the available devices to the world co-ordinates.
		For this purpose, a chessboard printout for use with opencv based calibration process is needed.

		"""
# 获取 RealSense 设备内参
		intrinsics_devices = device_manager.get_device_intrinsics(frames)

# 设置用于校准的棋盘参数
		chessboard_params = [chessboard_height, chessboard_width, square_size]

# 使用 Kabsch 方法估计棋盘在世界坐标系中的位姿
		calibrated_device_count = 0
		while calibrated_device_count < len(device_manager._available_devices):
			frames = device_manager.poll_frames()
			pose_estimator = PoseEstimation(frames, intrinsics_devices, chessboard_params)
			transformation_result_kabsch  = pose_estimator.perform_pose_estimation()
			object_point = pose_estimator.get_chessboard_corners_in3d()
			calibrated_device_count = 0
			for device_info in device_manager._available_devices:
				device = device_info[0]
				if not transformation_result_kabsch[device][0]:
					print("Place the chessboard on the plane where the object needs to be detected..")
				else:
					calibrated_device_count += 1

# 将所有设备的变换对象保存到数组中，用于测量
		transformation_devices={}
		chessboard_points_cumulative_3d = np.array([-1,-1,-1]).transpose()
		for device_info in device_manager._available_devices:
			device = device_info[0]
			transformation_devices[device] = transformation_result_kabsch[device][1].inverse()
			points3D = object_point[device][2][:,object_point[device][3]]
			points3D = transformation_devices[device].apply_transformation(points3D)
			chessboard_points_cumulative_3d = np.column_stack( (chessboard_points_cumulative_3d,points3D) )

# 提取用于计算物体尺寸的边界范围
# 本示例要求物体的长和宽小于棋盘的长和宽
		chessboard_points_cumulative_3d = np.delete(chessboard_points_cumulative_3d, 0, 1)
		roi_2D = get_boundary_corners_2D(chessboard_points_cumulative_3d)

		print("Calibration completed... \nPlace the box in the field of view of the devices...")


		"""
                2: Measurement and display
                Measure the dimension of the object using depth maps from multiple RealSense devices
                The information from Phase 1 will be used here

                """

# 启用设备的发射器
		device_manager.enable_emitter(True)

# 加载 JSON 设置文件，以启用 RealSense 的高精度预设
		device_manager.load_settings_json("./HighResHighAccuracyPreset.json")

# 获取设备外参，供后续使用
		extrinsics_devices = device_manager.get_depth_to_color_extrinsics(frames)

# 以字典形式获取校准信息，以便将测量结果显示在彩色图像而非红外图像上
		calibration_info_devices = defaultdict(list)
		for calibration_info in (transformation_devices, intrinsics_devices, extrinsics_devices):
			for key, value in calibration_info.items():
				calibration_info_devices[key].append(value)

# 持续采集，直到用户按 Ctrl+C 终止
		while 1:
# 获取所有设备的帧
				frames_devices = device_manager.poll_frames()

# 使用所有设备的深度帧计算点云
				point_cloud = calculate_cumulative_pointcloud(frames_devices, calibration_info_devices, roi_2D)

# 在彩色成像器坐标系中获取点云的包围盒
				bounding_box_points_color_image, length, width, height = calculate_boundingbox_points(point_cloud, calibration_info_devices )

# 在彩色图像上绘制包围盒顶点并显示结果
				visualise_measurements(frames_devices, bounding_box_points_color_image, length, width, height)

	except KeyboardInterrupt:
		print("The program was interupted by the user. Closing the program...")

	finally:
		device_manager.disable_streams()
		cv2.destroyAllWindows()


if __name__ == "__main__":
	run_demo()
