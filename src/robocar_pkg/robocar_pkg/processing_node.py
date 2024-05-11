import rclpy
from rclpy.node import Node
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np

class CannyEdgeDetectionNode(Node):
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
        # Convert ROS2 Image message to OpenCV format
        self.get_logger().info('IMAGE RECEIVED. Executing callback')
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        cv2.imshow('result', cv_image)
        # Process the image
        canny_image = self.canny(cv_image)
        lines = cv2.HoughLinesP(canny_image, 2, np.pi/180, 100, np.array([]), minLineLength=40, maxLineGap=5)
        self.get_logger().info(lines)




        # canny_image = self.canny(cv_image)
        # # cropped_image = self.region_of_interest(canny_image)
        # lines = cv2.HoughLinesP(canny_image, 2, np.pi/180, 100, np.array([]), minLineLength=40, maxLineGap=5)
        # # cv2.imshow('result', _image)
        # averaged_lines = self.average_slope_intercept(cv_image, lines)
        # self.get_logger.info(averaged_lines)

        # if all(line is not None for line in averaged_lines):
        #     self.get_logger().info('Drawing lines')
        #     line_image = self.display_lines(cv_image, averaged_lines)
        #     combo_image = cv2.addWeighted(cv_image, 0.8, line_image, 1, 1)
        #     cv2.imshow('result', combo_image)
        # else: 
        #     cv2.imshow('result', cv_image)
        # cv2.waitKey(1)


    def detect_black_lines(self, image):
        # Convertir la imagen a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar umbralización para obtener una imagen binaria de las líneas negras
        _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        
        # Encontrar contornos en la imagen binaria
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Crear una máscara dinámica basada en los contornos de las líneas negras
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, contours, -1, (255), thickness=cv2.FILLED)
        
        # Aplicar la máscara a la imagen original
        result = cv2.bitwise_and(image, image, mask=mask)
        
        return result
    
    # This function is responsible for translating the mathematical slope-intercept form of a line to pixel coordinates.
    def make_coordinates(self, image, line_parameters):
        # Unpack the line parameters
        slope, intercept = line_parameters
        y1 = image.shape[0]  # bottom of the image
        y2 = int(y1 * (3/5)) # somewhat lower than the middle of the image
        # Calculate the x-coordinates based on the slope and intercept
        x1 = int((y1 - intercept)/slope)
        x2 = int((y2 - intercept)/slope)
        # Return the line coordinates
        return np.array([x1,y1,x2,y2]) 

    # This function determines the average position of lane lines in an image
    def average_slope_intercept(self, image, lines):
        left_fit = []  # List to store parameters of lines on the left
        right_fit = [] # List to store parameters of lines on the right
        for line in lines:  # For each line detected in the image...
            x1,y1,x2,y2 = line.reshape(4)  # Unpack line points
            # Calculate the line's slope and intercept
            parameters = np.polyfit((x1,x2),(y1,y2),1)
            slope = parameters[0]
            intercept = parameters[1]
            if slope<0:  # If the slope is negative, the line is on the left
                left_fit.append((slope,intercept))
            else:  # Otherwise, it's on the right
                right_fit.append((slope,intercept))
        
        # If there are any lines on the left or right, calculate their average position
        left_line = right_line = None
        if left_fit:
            left_fit_average = np.average(left_fit,axis=0)
            left_line = self.make_coordinates(image,left_fit_average)
        if right_fit:
            right_fit_average = np.average(right_fit,axis=0)
            right_line = self.make_coordinates(image,right_fit_average)
        
        return left_line, right_line

    # This function applies the Canny edge detection algorithm to an image
    def canny(self, image):
        gray = cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)  # Convert the image to grayscale
        blur = cv2.GaussianBlur(gray,(5,5),0)   # Apply a Gaussian blur
        canny = cv2.Canny(blur,50,150)  # Apply the Canny algorithm
        return canny

    # This function draws detected lines on an image
    def display_lines(self, image, lines):
        line_image = np.zeros_like(image)  # Create an empty image to draw the lines on
        if lines is not None:  # If there are any lines...
            for line in lines:  # For each line...
                x1,y1,x2,y2 = line.reshape(4)  # Unpack line points
                # Draw the line on the image
                cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),10) # Draw a Blue Line(BGR in OpenCV)
        return line_image

    # This function masks everything outside a given region of interest
    def region_of_interest(self, image):
        height = image.shape[0]  # Get the height of the image
        # Define the polygon for the region of interest
        polygons = np.array([
            [(200,height),(1100,height),(550,250)]
        ])
        mask = np.zeros_like(image)   # Create a black mask
        cv2.fillPoly(mask,polygons,255)     # Fill the region of interest with white on the mask
        # Apply the mask to the image
        masked_image = cv2.bitwise_and(image,mask)
        return masked_image

def main(args=None):
    rclpy.init(args=args)
    node = CannyEdgeDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
