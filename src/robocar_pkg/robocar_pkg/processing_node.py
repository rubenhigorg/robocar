import rclpy
from rclpy.node import Node
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
from lib.line import Line
from lib.processor import ImageProcessor
from std_msgs.msg import Float32MultiArray
from lib.tracker import Tracker

class ProcessingNode(Node):
    def __init__(self):
        self.frame = 0
        super().__init__('processing_node')
        self.subscription = self.create_subscription(
            Image,
            'camera_image',
            self.image_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.publisher = self.create_publisher(Float32MultiArray, 'lane_info', 10)
        self.bridge = CvBridge()

        # Define the average positions for the left and right lanes.
        self.averageLeft = np.poly1d(np.array([-0.2674, 179.6]))
        self.averageRight = np.poly1d(np.array([0.2345, 480.0]))

        # Initalize the camera processor, defines the frame rate and frame size.
        self.processor = ImageProcessor((640, 480), 2)

        # Create a Kalman Filter for the left and right lanes.
        self.rightTracker = Tracker()
        self.leftTracker = Tracker()

        # PID values
        self.pid = 0
        self.sumError = 0
        self.averageError = 0
        self.prevError = 0
        self.dt = 1.0 / 20
    

    def image_callback(self, msg):
        # 1. Reads image:
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        save_img = cv_image.copy()
        self.get_logger().info('Received an image, doing Lane object...')

        # 2. Processes frame to extract lanes:
        processed_frame = self.processor.process(cv_image)

        # 3. Passes found lanes to Kalman filter:
        left = self.leftTracker.add(self.processor.left.poly)
        right = self.rightTracker.add(self.processor.right.poly)
        self.get_logger().info(f'Coeficientes de left: {left}')
        self.get_logger().info(f'Coeficientes de right: {right}')
        # 4. Calculates error on both lanes: 
        y0 = self.processor.roiY[1] * self.processor.h


        # Obtener lineas definitivas:
        final_left = self.processor.left.poly if self.processor.left.poly is not None else left
        final_right = self.processor.right.poly if self.processor.right.poly is not None else right

        leftError = self.averageLeft(y0) - final_left(y0)
        rightError = self.averageRight(y0) - final_right(y0)
        
        averageError = (leftError + rightError) / 2
        averageError *= 0.3

        if averageError > 30.0: 
            averageError = 30.0
        elif averageError < -30.0:
            averageError = -30.0
    
        self.get_logger().info(f'Average error: {averageError}')


        # Define PID constants.
        kp = 0.05
        ki = 0.05
        kd = 0.01

        # 5. Calculate the PID terms. 
        self.prevError = averageError
        self.sumError += averageError * ki * self.dt

        p = kp * averageError
        i = self.sumError
        d = (averageError - self.prevError) * kd / self.dt
        self.prevError = averageError

        # Calculate the control action (angle of turn).
        control_action = p + i + d

        # Calculate the turn angle based on the control action.
        turn_angle = self.calculate_angle(control_action)

        if turn_angle > 60: 
            turn_angle = 60
        elif turn_angle < -60:
            turn_angle = -60

        # Create and publish the message.
        lane_info_msg = Float32MultiArray()
        # lane_info_msg.data = [turn_angle]
        lane_info_msg.data = [averageError]
        self.publisher.publish(lane_info_msg)
        self.get_logger().info(f'Left error: {leftError}')
        self.get_logger().info(f'Right error: {rightError}')
        self.get_logger().info(f'Published turn angle: {averageError}')




        # Print info in frames
        filename = f'/home/lab/robocar/pruebas/computer_vision/log2/frame_{self.frame}.jpg'
        self.processor.drawPoly(cv_image, self.averageLeft, (255, 255, 255))
        self.processor.drawPoly(cv_image, self.averageRight, (255, 255, 255))
        self.processor.drawPoly(cv_image, self.processor.left.poly, (0, 255, 0))
        self.processor.drawPoly(cv_image, self.processor.right.poly, (0, 0, 255))
        # Displays the error on the frame.
        cv2.putText(cv_image, '%.2f' % (leftError), (int(self.averageLeft(y0)), int(y0) + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        cv2.putText(cv_image, '%.2f' % (rightError), (int(self.averageRight(y0)), int(y0) + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        self.print_offset(cv_image, averageError)
        cv2.imwrite(filename, cv_image)
        self.frame += 1


    def calculate_angle(self, offset):
        # calcular angulo de giro en funcion del offset:
        # si el offset es positivo, el coche debe girar a la derecha
        # si el offset es negativo, el coche debe girar a la izquierda
        # si el offset es 0, el coche debe ir recto

        proporcion_error_angulo = 0.6  # Grados de giro por unidad de error

        # Calcula el ángulo de giro necesario basado en el error promedio
        angulo_giro = offset * proporcion_error_angulo

        if angulo_giro > 60: 
            angulo_giro = 60
        elif angulo_giro < -60:
            angulo_giro = -60

        return angulo_giro
    
    def print_offset(self, cv_image, offset): 
        # Asumiendo que cv_image es tu imagen/frame
        alto, ancho = cv_image.shape[:2]

        # Calcular el centro de la imagen
        centro_x = ancho // 2
        centro_y = alto // 2

        # Punto central (necesitarás ajustar la posición para que el texto quede centrado según su tamaño)
        punto_central = (centro_x, centro_y)

        # Parámetros para cv2.putText
        texto = str(offset)
        fuente = cv2.FONT_HERSHEY_SIMPLEX
        escala_fuente = 1  # Tamaño de la fuente
        color = (255, 255, 255)  # Color del texto en BGR
        grosor = 2  # Grosor de la línea del texto

        # Calcular el tamaño del texto para ajustar el punto central
        (tamano_texto_ancho, tamano_texto_alto), _ = cv2.getTextSize(texto, fuente, escala_fuente, grosor)
        punto_inicio_texto = (centro_x - tamano_texto_ancho // 2, centro_y + tamano_texto_alto // 2)

        # Poner el texto en el frame
        cv2.putText(cv_image, texto, punto_inicio_texto, fuente, escala_fuente, color, grosor)





def main(args=None):
    rclpy.init(args=args)
    node = ProcessingNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
