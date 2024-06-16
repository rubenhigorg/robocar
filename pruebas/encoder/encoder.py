import smbus
import time

# Dirección I2C del Arduino esclavo
SLAVE_ADDRESS = 0x08

# Inicializar el bus I2C
bus = smbus.SMBus(1)  # 1 indica el bus I2C en la Raspberry Pi

def read_rpm():
    try:
        # Leer un byte de datos del esclavo
        rpm = bus.read_byte(SLAVE_ADDRESS)
        return rpm
    except Exception as e:
        print(f"Error al leer datos: {e}")
        return None

if __name__ == "__main__":
    while True:
        rpm = read_rpm()
        if rpm is not None:
            print(f"Received RPM: {rpm}")
        time.sleep(1)  # Esperar un segundo entre cada lectura
