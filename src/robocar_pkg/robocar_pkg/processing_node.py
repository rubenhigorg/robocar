import rclpy
from rclpy.node import Node
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np

class ProcessingNode(Node):
    def __init__(self):
        super().__init__('processing_node')
        self.subscription = self.create_subscription(
            Image,
            'camera_image',
            self.image_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.bridge = CvBridge()
    

    def image_callback(self, msg):
        try:
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error('Error converting ROS Image to OpenCV image: %s' % e)
            return

        # Detectar carriles en la imagen
        result = self.detect_lanes(cv_image)

        # Publicar la imagen resultante
        try:
            processed_image_msg = self.cv_bridge.cv2_to_imgmsg(result, 'bgr8')
            self.publisher.publish(processed_image_msg)
        except Exception as e:
            self.get_logger().error('Error converting OpenCV image to ROS Image: %s' % e)

    def detect_lanes(self, image):
        # Convertir la imagen a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Binarizar la imagen utilizando umbralización
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

        # Detección de contornos
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filtrar contornos por área y forma
        filtered_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Filtrar contornos pequeños
                epsilon = 0.1 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) == 4:  # Filtrar contornos cuadrados (carriles)
                    filtered_contours.append(contour)

        # Dibujar contornos filtrados en la imagen original
        lanes_image = image.copy()
        cv2.drawContours(lanes_image, filtered_contours, -1, (0, 255, 0), 3)

        # Ajustar líneas a los contornos
        lanes_lines = []
        for contour in filtered_contours:
            # Ajustar línea a cada contorno
            [vx, vy, x, y] = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
            slope = vy / vx
            intercept = y - slope * x
            x1 = int(x - 1000 * vx)
            y1 = int(y - 1000 * vy)
            x2 = int(x + 1000 * vx)
            y2 = int(y + 1000 * vy)
            lanes_lines.append(((x1, y1), (x2, y2)))

        # Dibujar líneas ajustadas en la imagen original
        for line in lanes_lines:
            cv2.line(lanes_image, line[0], line[1], (0, 0, 255), 2)

        return lanes_image


def main(args=None):
    rclpy.init(args=args)
    node = ProcessingNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
