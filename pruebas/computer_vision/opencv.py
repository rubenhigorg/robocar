import cv2

# Ruta de la imagen
ruta_imagen = "nombre_de_la_imagen.jpg"

# Cargar la imagen en escala de grises
imagen = cv2.imread(ruta_imagen, 0)

# Aplicar umbralización para convertir la imagen en binaria
_, imagen_binaria = cv2.threshold(imagen, 127, 255, cv2.THRESH_BINARY)

# Mostrar la imagen binaria
cv2.imshow("Imagen binaria", imagen_binaria)
cv2.waitKey(1)
cv2.destroyAllWindows()