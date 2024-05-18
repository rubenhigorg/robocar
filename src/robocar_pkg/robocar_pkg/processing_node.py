import rclpy
from rclpy.node import Node
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
from lib.Lane import Lane
from std_msgs.msg import Float32MultiArray

class ProcessingNode(Node):
    def __init__(self):
        super().__init__('processing_node')
        self.subscription = self.create_subscription(
            Image,
            'camera_image',
            self.image_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.publisher = self.create_publisher(Float32MultiArray, 'lane_info', 10)
        self.bridge = CvBridge()
    

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.get_logger().info('Received an image, doing Lane object...')
        lane = Lane(orig_frame=cv_image, logger=self.get_logger())
        lane_line_markings = lane.get_line_markings()
        lane.plot_roi(plot=False)

        wrapped = lane.perspective_transform(plot=False)
        histogram = lane.calculate_histogram(plot=False)
        left_fit, right_fit = lane.get_lane_line_indices_sliding_windows(plot=False)
        lane.get_lane_line_previous_window(left_fit, right_fit, plot=False)
        frame_with_lane_lines = lane.overlay_lane_lines(plot=False)
        left_curvem, right_curvem = lane.calculate_curvature(print_to_terminal=False)
        offset = lane.calculate_car_position(print_to_terminal=False)
        
         # Publicar la información de carriles
        lane_info = Float32MultiArray()
        lane_info.data = [offset, left_curvem, right_curvem]
        self.publisher.publish(lane_info)
        self.get_logger().info(f'Offset: {offset}, Left curvature: {left_curvem}, Right curvature: {right_curvem}')

        
        frame_2 = lane.display_curvature_offset(frame=frame_with_lane_lines, plot=False)
        #cv2.imshow('Frame with lane lines', frame_2)
        #cv2.waitKey(1)



def main(args=None):
    rclpy.init(args=args)
    node = ProcessingNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
