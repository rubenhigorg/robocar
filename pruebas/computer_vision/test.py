import cv2
import numpy as np
from Lane import Lane

def process_image(cv_image):
    lane = Lane(orig_frame=cv_image)
    binary = lane.get_line_markings()
    lane.plot_roi(plot=True)
    warped_img = lane.perspective_transform(plot=True)
    histogram = lane.calculate_histogram(plot=True)
    left_fit, right_fit = lane.get_lane_line_indices_sliding_windows(plot=True)
    lane.get_lane_line_previous_window(left_fit, right_fit, plot=False)
    frame_with_lane_lines = lane.overlay_lane_lines(plot=False)
    left_curvem, right_curvem = lane.calculate_curvature(print_to_terminal=True)
    offset = lane.calculate_car_position(print_to_terminal=True)

    frame_with_lane_lines = lane.display_curvature_offset(frame=frame_with_lane_lines, plot=True)


    offset = 0.0
    angle = 0.0
    return warped_img, offset, angle
















#     # warped_img = birdseye_view(roi_img, src, dst)

#     # Detectar bordes en la imagen transformada
#     edges = cv2.Canny(warped_img, 50, 150)
#     cv2.imshow("Edges", edges)
#     cv2.waitKey(0)

#     # Detectar las líneas del carril usando la Transformada de Hough
#     lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=50)
    
#     # Si se detectan líneas, calcular el offset y el ángulo
#     if lines is not None:
#         offset, angle = calculate_offset_and_angle(warped_img, lines)
#         # PINTAR LINEAS:
#         for line in lines:
#             x1, y1, x2, y2 = line[0]
#             cv2.line(warped_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
#     else:
#         offset, angle = 0, 0

#     return warped_img, offset, angle



# def calculate_offset_and_angle(image, lines):
#     height, width = image.shape[:2]
#     car_position = width / 2  # Asumimos que el coche está en el centro de la parte inferior de la imagen
    
#     left_lines = []  # Líneas del carril izquierdo
#     right_lines = []  # Líneas del carril derecho
    
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#         slope = (y2 - y1) / (x2 - x1) if (x2 - x1) != 0 else 999999.9  # Evitar división por cero
#         if abs(slope) > 0.5:  # Filtrar líneas casi horizontales
#             if slope < 0:
#                 if x2 < car_position:
#                     left_lines.append(line)
#                 elif x2 > car_position:
#                     right_lines.append(line)
#             elif slope > 0:
#                 if x1 < car_position:
#                     right_lines.append(line)
#                 elif x1 > car_position:
#                     left_lines.append(line)


#             # and x1 < car_position and x2 < car_position:
#             #     left_lines.append(line)
#             # elif slope > 0 and x1 > car_position and x2 > car_position:
#             #     right_lines.append(line)
    
#     left_lane = average_slope_intercept(left_lines, height)
#     right_lane = average_slope_intercept(right_lines, height)
    
#     if left_lane is not None and right_lane is not None:
#         lane_center = (left_lane[2] + right_lane[2]) / 2
#         offset = lane_center - car_position
#         angle = np.degrees(np.arctan((left_lane[0] + right_lane[0]) / 2))  # Convertir la pendiente media a grados
#     else:
#         offset, angle = 0, 0
    
#     return offset, angle

# def average_slope_intercept(lines, height):
#     if len(lines) == 0:
#         return None
    
#     slopes = []
#     intercepts = []
    
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#         slope = (y2 - y1) / (x2 - x1)
#         intercept = y1 - slope * x1
#         slopes.append(slope)
#         intercepts.append(intercept)
    
#     avg_slope = np.mean(slopes)
#     avg_intercept = np.mean(intercepts)
    
#     y1 = height
#     y2 = int(height * 0.6)
#     x1 = int((y1 - avg_intercept) / avg_slope)
#     x2 = int((y2 - avg_intercept) / avg_slope)
    
#     return (avg_slope, avg_intercept, (x1 + x2) / 2)


# Ejemplo de uso





if __name__ == "__main__":
    cv_image = cv2.imread("/home/rhiguera/robocar/pruebas/computer_vision/coche.jpg")  # Cargar una imagen de prueba
    processed_image, offset, angle = process_image(cv_image)
    
    print(f"Offset: {offset}, Angle: {angle}")
    
    cv2.imshow('Lane Detection', processed_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
