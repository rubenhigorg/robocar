import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import ByteMultiArray
from cv_bridge import CvBridge
import cv2

class CameraPublisher(Node):

    def __init__(self):
        super().__init__('camera_publisher')
        self.publisher_ = self.create_publisher(Image, 'camera_image', 10)
        # self.publisher_nodered = self.create_publisher(ByteMultiArray,'camera_image_nodered', 10)

        self.timer_period = 0.1  # seconds
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.i = 0
        self.bridge = CvBridge()
        self.camera = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L)
    # definimos la calidad del frame
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 120) 
       

    def timer_callback(self):
        ret, frame = self.camera.read()
        self.get_logger().info('Resultado:' + str(ret))
        if ret:
            msg = self.bridge.cv2_to_imgmsg(frame, "bgr8")
            # is_success, buffer = cv2.imencode(".jpg", frame)
            # byte_image = buffer.tobytes()
            # msg_nodered = ByteMultiArray()
            # msg_nodered.data = byte_image
            self.get_logger().info('BEFORE IMAGE')
            self.publisher_.publish(msg)
            self.get_logger().info('AFTER IMAGE')
            # self.publisher_nodered.publish(msg_nodered)
            # self.get_logger().info('Publishing image #%d' % self.i)
            self.i += 1

def main(args=None):
    rclpy.init(args=args)

    camera_publisher = CameraPublisher()

    rclpy.spin(camera_publisher)

    camera_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()