import cv2
import numpy as np

# Ruta de la imagen
ruta_imagen = "coche.jpg"

# Cargar la imagen en color
imagen = cv2.imread(ruta_imagen)

# Convertir la imagen a HSV
imagen_hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)

# Crear una ventana para los controles deslizantes
cv2.namedWindow('Controles')

# Crear los controles deslizantes para los valores de HSV
cv2.createTrackbar('Hue', 'Controles', 0, 179, lambda x: None)
cv2.createTrackbar('Saturation', 'Controles', 0, 255, lambda x: None)
cv2.createTrackbar('Value', 'Controles', 0, 255, lambda x: None)

while True:
    # Obtener los valores de los controles deslizantes
    h = cv2.getTrackbarPos('Hue', 'Controles')
    s = cv2.getTrackbarPos('Saturation', 'Controles')
    v = cv2.getTrackbarPos('Value', 'Controles')

    # Crear un array con los valores de HSV
    lower_hsv = np.array([h, s, v])
    upper_hsv = np.array([179, 255, 255])

    # Aplicar la máscara HSV a la imagen
    mask = cv2.inRange(imagen_hsv, lower_hsv, upper_hsv)
    imagen_resultado = cv2.bitwise_and(imagen, imagen, mask=mask)

    # Mostrar la imagen resultado
    cv2.imshow("Imagen resultado", imagen_resultado)

    # Salir del bucle si se presiona la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()