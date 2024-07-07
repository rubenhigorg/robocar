from picamera import PiCamera
import numpy as np
import io

# Crear una instancia de PiCamera
camera = PiCamera()

# Configurar la cámara (opcional, ajusta según necesites)
camera.resolution = (1024, 768)

# Iniciar la cámara
camera.start_preview()

# Esperar un poco para que la cámara ajuste su configuración de luz
camera.wait_recording(2)

# Capturar la imagen en un objeto BytesIO en formato 'rgb'
stream = io.BytesIO()
camera.capture(stream, format='rgb')

# Convertir el contenido del stream a un arreglo de numpy
stream.seek(0)  # Regresar al inicio del stream
frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)

# Cambiar la forma del arreglo para que coincida con la resolución y los canales de color
frame = frame.reshape((768, 1024, 3))

# Convertir el frame a un arreglo de bytes si es necesario
frame_bytes = frame.tobytes()

# Imprimir el tamaño del frame capturado
print(f"Tamaño del frame capturado: {len(frame_bytes)} bytes")

# Detener la vista previa de la cámara
camera.stop_preview()