import rclpy
from rclpy.node import Node
import cv2
from sensor_msgs.msg import Image

class CannyEdgeDetectionNode(Node):
    def __init__(self):
        super().__init__('processing_node')
        self.subscription = self.create_subscription(
            Image,
            'camera_image',
            self.image_callback,
            10)
        self.subscription  # prevent unused variable warning

    def image_callback(self, msg):
        # Convert ROS2 Image message to OpenCV format
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Apply Canny edge detection
        edges = cv2.Canny(cv_image, 100, 200)

        # Process the detected edges further if needed

        # Display the result or publish it to a ROS2 topic
        cv2.imshow('Canny Edges', edges)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = CannyEdgeDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
