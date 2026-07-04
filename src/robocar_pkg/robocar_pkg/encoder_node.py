import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
import smbus2


class EncoderNode(Node):
    """Publica la velocidad lineal de la rueda dentada leida del Arduino esclavo I2C.

    El Arduino (0x08) cuenta los impulsos de la rueda y expone, en el registro 0
    (2 bytes little-endian), el numero de impulsos de la ULTIMA ventana de 1 s;
    es decir, la frecuencia en impulsos/segundo, refrescada a ~1 Hz (NO es un
    contador acumulativo).

        impulsos/s = valor leido
        vueltas/s  = impulsos/s / pulses_per_rev
        velocidad  = vueltas/s * pi * wheel_diameter_m   [m/s]

    Notas:
    - La fuente se refresca a 1 Hz, por lo que la velocidad es una media del
      ultimo segundo (baja resolucion temporal, hasta ~1 s de latencia).
    - El encoder es de un solo canal: no da signo (velocidad siempre >= 0).
    """

    def __init__(self):
        super().__init__('encoder_node')

        # --- Parametros (calibrables sin recompilar) ---
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_address', 0x08)
        self.declare_parameter('pulses_per_rev', 20.0)      # PLACEHOLDER: calibrar (nÂº de dientes)
        self.declare_parameter('wheel_diameter_m', 0.065)   # PLACEHOLDER: medir la rueda
        self.declare_parameter('publish_rate_hz', 5.0)
        self.declare_parameter('frame_id', 'base_link')

        self.i2c_address = self.get_parameter('i2c_address').value
        self.pulses_per_rev = float(self.get_parameter('pulses_per_rev').value)
        self.wheel_diameter_m = float(self.get_parameter('wheel_diameter_m').value)
        self.frame_id = self.get_parameter('frame_id').value
        rate = float(self.get_parameter('publish_rate_hz').value)
        bus_num = self.get_parameter('i2c_bus').value

        # Factor que convierte impulsos/s -> m/s
        self.meters_per_pulse_sec = (math.pi * self.wheel_diameter_m) / self.pulses_per_rev

        self.bus = smbus2.SMBus(bus_num)
        self.publisher_ = self.create_publisher(TwistStamped, 'wheel_speed', 10)
        self.timer = self.create_timer(1.0 / rate, self.timer_callback)
        self.get_logger().info(
            'encoder_node listo (addr=0x%02X, PPR=%.1f, diam=%.3f m)'
            % (self.i2c_address, self.pulses_per_rev, self.wheel_diameter_m))

    def read_pulses_per_sec(self):
        """Lee los impulsos de la ultima ventana de 1 s (2 bytes, little-endian)."""
        try:
            data = self.bus.read_i2c_block_data(self.i2c_address, 0, 2)
            return data[0] | (data[1] << 8)
        except Exception as e:
            self.get_logger().warn('Error leyendo el encoder: %s' % e)
            return None

    def timer_callback(self):
        pps = self.read_pulses_per_sec()
        if pps is None:
            return

        speed = pps * self.meters_per_pulse_sec

        now = self.get_clock().now()
        msg = TwistStamped()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = self.frame_id
        msg.twist.linear.x = speed
        self.publisher_.publish(msg)
        self.get_logger().info('wheel_speed: %.3f m/s (%d imp/s)' % (speed, pps))


def main(args=None):
    rclpy.init(args=args)
    node = EncoderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
