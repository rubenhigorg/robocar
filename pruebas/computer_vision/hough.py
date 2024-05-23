import cv2
import numpy as np


# Ruta de la imagen
ruta_imagen = "coche.jpg"

# Cargar la imagen en color
frame = cv2.imread(ruta_imagen)

# Convertir la imagen a HSV
imagen_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# Definir los valores de HSV para la detección del color rojo
lower_hsv = np.array([20, 30, 0])
upper_hsv = np.array([179, 255, 255])

# Aplicar las máscaras HSV a la imagen
mask = cv2.inRange(imagen_hsv, lower_hsv, upper_hsv)

# Convertir la máscara a una imagen binaria 
imagen_binaria = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)[1]
cv2.imshow('Frame with detected lines', imagen_binaria)
cv2.waitKey(0)

# Aplicar un filtro de Canny para detectar bordes
edges = cv2.Canny(imagen_binaria, 50, 150, apertureSize=3)
cv2.imshow('Edges', edges)
cv2.waitKey(0)

# Usar la Transformada de Hough Probabilística para detectar líneas
lines = cv2.HoughLinesP(frame, 1, np.pi/180, 100, minLineLength=100, maxLineGap=100)

# Dibujar las líneas detectadas en la imagen original
for line in lines:
    x1, y1, x2, y2 = line[0]
    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

cv2.imshow('Frame with detected lines', frame)
cv2.waitKey(0)
cv2.destroyAllWindows()