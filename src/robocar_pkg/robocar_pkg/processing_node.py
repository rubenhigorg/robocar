import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2 as cv
import numpy as np

# Importa las funciones de detección desde tu archivo
import lib.detection_functions as df 

class ProcessingNode(Node):
    def __init__(self):
        super().__init__('image_processor')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            'camera_image',
            self.image_callback,
            10)
        self.lane_lines_anterior = []

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

        bird_sight = df.perspective_foto(cv_image)

        edges = df.detect_edges(bird_sight, 70)

        line_segments = df.detect_line_segments(edges)

        lane_lines = df.average_slope_intercept(cv_image, line_segments)

        if len(lane_lines) != 2:
            lane_lines = self.lane_lines_anterior
        else: 
            self.lane_lines_anterior = lane_lines
        
        lane_lines_image = df.display_lines(bird_sight, lane_lines)

        new_angle = df.get_angle(cv_image, lane_lines, lane_lines_image)

        if new_angle is not None: 
            texto = "angulo=" + str((new_angle*180/(math.pi)))

            cv.putText(lane_lines_image, texto, (10, 50), cv.FONT_HERSHEY_SIMPLEX,
                       0.5, (150, 255, 255), 1, cv.LINE_AA)
            
        cv.imshow("Lane lines", lane_lines_image)
        cv.waitKey(1)
        # Aquí puedes hacer algo con el ángulo y la imagen de las líneas del carril

def main(args=None):
    rclpy.init(args=args)
    image_processor = ProcessingNode()
    rclpy.spin(image_processor)
    image_processor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()