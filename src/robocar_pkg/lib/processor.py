#!/usr/bin/python3
# -*- coding: utf-8 -*-

import numpy as np
import cv2
from lib.line import Line

class ImageProcessor():
    """
        Implements the computer vision algorithms for detecting lanes in an image.
    """

    def __init__(self, frameDimensions, frameRate):

        # Define camera dimensions.
        self.frameDimensions = frameDimensions
        self.frameRate = frameRate
        self.w = self.frameDimensions[0]
        self.h = self.frameDimensions[1]

        # ROI dimensions in percentage.
        self.roiY = (1, 0.65)
        self.roiX = (1, 0.8)

        # Initialize the left and right lane classes.
        self.left = Line(self.frameDimensions, (0, 0, 255))
        self.right = Line(self.frameDimensions, (255, 0, 0))
        
        # Camera calibration
        # Scale the calibration matrix to the desired frame dimensions.
        self.calibrationResolution = (1280, 720)                            # Resolution at which the camera matrix is provided.
        kx = self.w / self.calibrationResolution[0]                         # Calculate the change in the -x axis.
        ky = self.h / self.calibrationResolution[1]                         # Calculate the change in the -y axis.
        cameraMatrix = np.array([                                           # Raw camera calibration matrix.
            [1.00612323e+03, 0.00000000e+00, 6.31540281e+02],
            [0.00000000e+00, 1.00551440e+03, 3.48207362e+02],
            [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]
        ])
        self.cameraMatrix = np.multiply(cameraMatrix, [                     # Adjust the camera calibration matrix.
            [kx, 1, kx],
            [1, ky, ky],
            [1, 1, 1]
        ])
        self.distortionCoefficients = np.array([[0.18541226, -0.32660915, 0.00088513, -0.00038131, -0.02052374]])
        self.newCameraMatrix, self.roi = cv2.getOptimalNewCameraMatrix(self.cameraMatrix, self.distortionCoefficients, self.frameDimensions, 1, self.frameDimensions)
        self.rectifyMapX, self.rectifyMapY = cv2.initUndistortRectifyMap(self.cameraMatrix, self.distortionCoefficients, None, self.newCameraMatrix, self.frameDimensions, 5)

    def doBlur(self, frame, iterations, kernelSize):
        """
            Performs a gaussian blur with the set number of iterations.
        """

        blured = frame.copy()
        while iterations > 0:
            blured =  cv2.GaussianBlur(blured, (kernelSize, kernelSize), sigmaX=0, sigmaY=0)
            iterations -= 1
        return blured

    def doRegionOfInterest(self, frame):
        """
            Obtains the region of interest from a frame. The dimensions of the ROI are set by the class
            properties roiX and roiY.
        """

        y0Px = self.h * self.roiY[0]
        y1Px = self.h * self.roiY[1]
        x0Px = (1 - self.roiX[0]) * self.w / 2
        x1Px = (1 - self.roiX[1]) * self.w / 2
        vertices = np.array([[
            (x0Px, y0Px),
            (x1Px, y1Px),
            (self.w - x1Px, y1Px),
            (self.w - x0Px, y0Px)
        ]], dtype=np.int32)
        mask = np.zeros_like(frame)
        cv2.fillPoly(mask, vertices, 255)
        return cv2.bitwise_and(frame, mask)

    def findLanes(self, frame, lines, drawAll=False):
        """
            Iterates through the results from the Hough Transform and filters the detected lines into
            those who belong to the left and right lane. Finally fits the data to a 1st order polynomial.
        """

        self.left.clear()
        self.right.clear()
        frame_center = frame.shape[1] / 2

        if type(lines) == type(np.array([])):
            for line in lines:
                for x1, y1, x2, y2 in line:
                    if x1 < frame_center and x2 < frame_center:
                        self.left.add(x1, y1, x2, y2)
                        if drawAll:
                            cv2.line(frame, (x1, y1), (x2, y2), self.left.color)
                    elif x1 > frame_center and x2 > frame_center:
                        self.right.add(x1, y1, x2, y2)
                        if drawAll:
                            cv2.line(frame, (x1, y1), (x2, y2), self.right.color)
        self.left.fit()
        self.right.fit()
        return frame
        
    def drawPoly(self, frame, poly, color, width=3):
        """
            Draws a 1-D polynomial into the frame. Uses the roiY for the -y coordinates.
        """

        y0 = self.h * self.roiY[0]
        y1 = self.h * self.roiY[1]
        y0Px = int(y0)
        y1Px = int(y1)
        if poly:
            x0Px = int(poly(y0))
            x1Px = int(poly(y1))
            cv2.line(frame, (x0Px, y0Px), (x1Px, y1Px), color, width)     
        else:
            cv2.line(frame, (0, y0Px), (0, y1Px), color, width)     

    def process(self, frame):
        """
            Main pipeline for detecting lanes on a frame.
        """
        binary_frame = self.get_line_markings(frame)
        blured = self.doBlur(binary_frame, iterations=3, kernelSize=7)
        canny = cv2.Canny(blured, threshold1=20, threshold2=40)
        roi = self.doRegionOfInterest(canny)
        houghLines = cv2.HoughLinesP(
            roi,
            rho = 1, 
            theta = np.pi / 180, 
            threshold = 20, 
            lines = np.array([]), 
            minLineLength = 5, 
            maxLineGap = 60
        )
        lanes = self.findLanes(frame, houghLines, drawAll=True)
        # self.drawPoly(lanes, self.left.poly, self.left.color, width=3)
        # self.drawPoly(lanes, self.right.poly, self.right.color, width=3)

        return lanes


    
    def get_line_markings(self, frame=None):
        """
        Isolates lane lines.
    
        :param frame: The camera frame that contains the lanes we want to detect
        :return: Binary (i.e. black and white) image containing the lane lines.
        """
        if frame is None:
            frame = self.orig_frame
    
        # Convertir la imagen a HSV
        imagen_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Definir los valores de HSV para la detección del color rojo
        lower_hsv = np.array([130, 55, 0])
        upper_hsv = np.array([179, 255, 255])

        # Aplicar las máscaras HSV a la imagen
        mask = cv2.inRange(imagen_hsv, lower_hsv, upper_hsv)

        # Convertir la máscara a una imagen binaria 
        imagen_binaria = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)[1]

        # Definir el kernel para las operaciones morfológicas
        kernel = np.ones((5,5), np.uint8)  # Puedes ajustar el tamaño del kernel según tus necesidades

        # Aplicar cierre morfológico para eliminar líneas finas
        cierre = cv2.morphologyEx(imagen_binaria, cv2.MORPH_CLOSE, kernel)

        # (Opcional) Aplicar apertura morfológica para limpiar ruido restante
        apertura = cv2.morphologyEx(cierre, cv2.MORPH_OPEN, kernel)

        return apertura
