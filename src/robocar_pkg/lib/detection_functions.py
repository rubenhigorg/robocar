import math
import numpy as np
import cv2 as cv


def perspective_foto(img):
    """
    En esta funcion cambia la perspectiva de la imagen para verla desde arrriba
    """
    ht = img.shape[0] #height altura de la imagen
    wd = img.shape[1] #width anchura de la imagen

    pts1 = np.float32([[30, 175],[wd-50, 175],[0, ht],[wd, ht]]) #top left, top right, bottomb left, bottom right (area we want to be selected)
    pts2 = np.float32([[0,0],[wd,0],[0,ht],[wd,ht]]) #dimension de imagen que queremos obtener

    matrix=cv.getPerspectiveTransform(pts1,pts2)
    result=cv.warpPerspective(img,matrix,(wd,ht))

    return result


def detect_edges(frame, saturacion):
    """
    En esta funcion detecta los bordes del frame, se le pasa la saturacion usada en el filtro canny
    """
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV) #COLOR_BGR2HSV para detectar el azul

    lower_blue = np.array([90, saturacion, 0])
    upper_blue = np.array([140, 255, 150])

    mask = cv.inRange(hsv, lower_blue, upper_blue)

    edges = cv.Canny(mask, 250, 300)

    return edges


def detect_line_segments(cropped_edges):
	"""
	En esta funcion detecta lineas en el frame que se le pase
	"""
	line_segments = cv.HoughLinesP(cropped_edges, 8, np.pi/60, 100, np.array([]), 15, 3)

	return line_segments


def average_slope_intercept(frame, line_segments):
    """
    This function combines line segments into one or two lane lines
    If all line slopes are < -0.5: then we only have detected left lane
    If all line slopes are > 0.5: then we only have detected right lane
    """
    lane_lines = []
    if line_segments is None:
        return lane_lines

    height, width, _ = frame.shape
    left_fit = []
    right_fit = []

    boundary = 2/3
    left_region_boundary = width * (1 - boundary) # left lane line segment could be on left 2/3 of the screen
    right_region_boundary = width * boundary # right lane line segment could be on left 2/3 of the screen


    for line_segment in line_segments:
        for x1, y1, x2, y2 in line_segment:
            if x1 == x2:
                continue
    fit = np.polyfit((x1, x2), (y1, y2), 1)
    slope = fit[0]
    intercept = fit[1]

    if slope < -0.5: #left lane detected
        if x1 < left_region_boundary and x2 < left_region_boundary:
            left_fit.append((slope, intercept))
        elif slope >0.5: #rigth lane detected
            if x1 > right_region_boundary and x2 > right_region_boundary:
                right_fit.append((slope, intercept))


    left_fit_average = np.average(left_fit, axis=0)
    if len(left_fit) > 0:
        lane_lines.append(make_points(frame, left_fit_average))

    right_fit_average = np.average(right_fit, axis=0)
    if len(right_fit) > 0:
        lane_lines.append(make_points(frame, right_fit_average))

    return lane_lines


def make_points(frame, line):
	height, width, _ = frame.shape
	slope, intercept = line

	y1 = height # bottom of the frame
	y2 = int(y1 * 1 / 1.3) # make points from middle of the frame down

	# bound the coordinates within the frame
	x1 = max(-width, min(2 * width, int((y1 - intercept) / slope)))
	x2 = max(-width, min(2 * width, int((y2 - intercept) / slope)))
	return [[x1, y1, x2, y2]]


def display_lines(frame, lines):
    """
    En esta funcion se superpone el frame con las lineas del carril
    """
    blank_image = np.zeros((frame.shape[0], frame.shape[1], 3), np.uint8)

    for line in lines:
        for x1, y1, x2, y2 in line:
            cv.line(blank_image, (x1, y1), (x2, y2), (250, 0, 250), 2)

    color_image_line = cv.addWeighted(frame, 0.8, blank_image, 1, 0.0)
    return color_image_line


def get_angle(frame, lane_lines, lane_lines_image):
    """
    En esta funcion se calcula el angulo de direccion si se han detectado las dos lineas del carril
    """

    height, width, _ = frame.shape

    if len(lane_lines) == 2:

        left_x1, left_y1, left_x2, left_y2 = lane_lines[0][0]
        right_x1, right_y1, right_x2, right_y2 = lane_lines[1][0]

        x_offset = (left_x2 + right_x2) / 2
        y_offset=(left_y2 + right_y2) / 2

        x_bajo=(left_x1 + right_x1) / 2
        y_bajo=(left_y1 + right_y1) / 2

        #se dibujan circulos en los extremos de las lineas
        cv.circle(lane_lines_image, (left_x2,left_y2),5,(255,0,0),5)
        cv.circle(lane_lines_image, (right_x2,right_y2),5,(255,0,0),5)
        cv.circle(lane_lines_image, (int(x_offset),int(y_offset)),5,(255,308,0),5)
        cv.circle(lane_lines_image, (200,308),5,(255,308,0),5)
        cv.line(lane_lines_image, (int(x_offset),int(y_offset)), (200,308), (0, 0, 255), 5) #linea roja del medio

        p_med=200 #coordenada x centrada en el carril
        if(x_offset<p_med): #se esta girando a la izquierda
            angle_to_mid_radian = (math.pi - math.atan(y_offset / (p_med-x_offset)))-(math.pi/2)

        elif (x_offset>p_med): #se esta girando a la izquierda
            angle_to_mid_radian = math.atan(y_offset / (x_offset-p_med))-(math.pi/2)

        else: #no se esta girando
            angle_to_mid_radian = math.pi/2-(math.pi/2) #si el punto esta justo en el medio entonces el angulo son 90 grados

        return angle_to_mid_radian