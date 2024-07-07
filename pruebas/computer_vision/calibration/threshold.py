import cv2
import numpy as np

# Ruta de la imagen
ruta_imagen = "coche.jpg"

# Cargar la imagen en color
imagen = cv2.imread(ruta_imagen)

# Convertir la imagen a HSV
imagen_hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)

# Definir los valores de HSV para la detección del color rojo
lower_hsv = np.array([160, 100, 100])
upper_hsv = np.array([179, 255, 255])

# Aplicar las máscaras HSV a la imagen
mask = cv2.inRange(imagen_hsv, lower_hsv, upper_hsv)

# Convertir la máscara a una imagen binaria 
imagen_binaria = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)[1]

cv2.imshow("Imagen binaria", imagen_binaria)
cv2.waitKey(0)
cv2.destroyAllWindows()


# imagen_resultado = cv2.bitwise_and(imagen, imagen, mask=mask)

# Convertir la imagen resultado a escala de grises
# imagen_gris = cv2.cvtColor(imagen_resultado, cv2.COLOR_BGR2GRAY)

# # Crear una ventana para los controles deslizantes
# cv2.namedWindow('Controles')

# # Crear los controles deslizantes para los valores de HSV
# cv2.createTrackbar('Ajuste', 'Controles', 0, 255, lambda x: None)

# while True:
#     # Obtener los valores de los controles deslizantes
#     a = cv2.getTrackbarPos('Ajuste', 'Controles')

#     # Aplicar el umbral a la imagen en escala de grises
#     _, imagen_umbral = cv2.threshold(imagen_gris, a, 255, cv2.THRESH_BINARY)

#     # Mostrar la imagen umbral
#     cv2.imshow("Imagen umbral", imagen_umbral)

#     # Salir del bucle si se presiona la tecla 'q'
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cv2.destroyAllWindows()