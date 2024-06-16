import smbus
import time

# Dirección I2C del Arduino esclavo
SLAVE_ADDRESS = 0x08

# Inicializar el bus I2C
bus = smbus.SMBus(1)  # 1 indica el bus I2C en la Raspberry Pi

def read_counter():
    try:
        # Leer dos bytes de datos del esclavo
        data = bus.read_i2c_block_data(SLAVE_ADDRESS, 0, 2)
        # Convertir los bytes en un valor entero
        counter = data[0] | (data[1] << 8)
        return counter
    except Exception as e:
        print(f"Error al leer datos: {e}")
        return None

if __name__ == "__main__":
    while True:
        counter = read_counter()
        if counter is not None:
            print(f"Received Counter: {counter}")
        time.sleep(1)  # Esperar un segundo entre cada lectura