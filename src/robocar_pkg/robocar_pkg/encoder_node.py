import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped, Twist
import smbus2


class EncoderNode(Node):
    """Publica la velocidad lineal de la rueda dentada leida del Arduino Nano (I2C 0x08).

    Firmware nuevo (v2): el Nano expone un CONTADOR ACUMULATIVO de 16 bits (2 bytes
    little-endian) que incrementa por interrupcion en cada pulso. Este nodo lo lee a
    alta frecuencia (~30 Hz) y deriva la velocidad como delta_cuenta/delta_t, con
    manejo de desbordamiento de 16 bits (leyendo rapido, delta < 65536 siempre).
    Esto sustituye al firmware antiguo de 1 Hz/1 s de latencia.

        velocidad = delta_cuenta * meters_per_pulse / delta_t   [m/s]
        meters_per_pulse = pi * wheel_diameter_m / pulses_per_rev  (o param directo)

    Sentido: el encoder no lo detecta (cuenta magnitud). Se firma la velocidad con el
    signo del ultimo /cmd_vel (car_control conduce segun /cmd_vel). Ver Fase 1 del plan.
    """

    def __init__(self):
        super().__init__('encoder_node')

        # --- Parametros ---
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_address', 0x08)
        self.declare_parameter('pulses_per_rev', 143.8)     # calibrar (firmware v2, flancos RISING)
        self.declare_parameter('wheel_diameter_m', 0.068)
        self.declare_parameter('meters_per_pulse', 0.0)     # si >0, anula pulses_per_rev+diam (calibracion directa)
        self.declare_parameter('publish_rate_hz', 30.0)     # ahora rapido
        self.declare_parameter('frame_id', 'base_link')
        self.declare_parameter('max_dt', 0.5)               # s: si el intervalo es mayor, no derivar (reinicio)
        # --- Sentido inferido de /cmd_vel ---
        self.declare_parameter('use_cmd_direction', True)
        self.declare_parameter('cmd_topic', '/cmd_vel')
        self.declare_parameter('dir_deadband', 0.02)

        self.i2c_address = self.get_parameter('i2c_address').value
        ppr = float(self.get_parameter('pulses_per_rev').value)
        diam = float(self.get_parameter('wheel_diameter_m').value)
        mpp = float(self.get_parameter('meters_per_pulse').value)
        self.meters_per_pulse = mpp if mpp > 0.0 else (math.pi * diam) / ppr
        self.frame_id = self.get_parameter('frame_id').value
        rate = float(self.get_parameter('publish_rate_hz').value)
        bus_num = self.get_parameter('i2c_bus').value
        self.use_cmd_direction = bool(self.get_parameter('use_cmd_direction').value)
        self.dir_deadband = float(self.get_parameter('dir_deadband').value)
        self.max_dt = float(self.get_parameter('max_dt').value)

        self.direction = 1.0
        self.last_count = None
        self.last_time = None
        self._log_div = 0

        self.bus = smbus2.SMBus(bus_num)
        self.publisher_ = self.create_publisher(TwistStamped, 'wheel_speed', 10)
        if self.use_cmd_direction:
            self.create_subscription(Twist, self.get_parameter('cmd_topic').value, self.cmd_cb, 10)
        self.timer = self.create_timer(1.0 / rate, self.timer_callback)
        self.get_logger().info(
            'encoder_node v2 listo (0x%02X, m/pulso=%.6f, %.0f Hz, sentido_por_cmd=%s)'
            % (self.i2c_address, self.meters_per_pulse, rate, self.use_cmd_direction))

    def cmd_cb(self, msg):
        vx = msg.linear.x
        if vx > self.dir_deadband:
            self.direction = 1.0
        elif vx < -self.dir_deadband:
            self.direction = -1.0

    def read_count(self):
        """Lee el contador acumulativo de 16 bits (2 bytes, little-endian)."""
        try:
            data = self.bus.read_i2c_block_data(self.i2c_address, 0, 2)
            return data[0] | (data[1] << 8)
        except Exception as e:
            self.get_logger().warn('Error leyendo el encoder: %s' % e)
            return None

    def timer_callback(self):
        count = self.read_count()
        if count is None:
            return
        now = self.get_clock().now()
        if self.last_count is None:
            self.last_count = count
            self.last_time = now
            return
        dt = (now - self.last_time).nanoseconds / 1e9
        delta = (count - self.last_count) & 0xFFFF     # desbordamiento de 16 bits
        self.last_count = count
        self.last_time = now
        if dt <= 0.0 or dt > self.max_dt:
            return
        speed = delta * self.meters_per_pulse / dt
        if self.use_cmd_direction:
            speed *= self.direction

        msg = TwistStamped()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = self.frame_id
        msg.twist.linear.x = speed
        self.publisher_.publish(msg)

        self._log_div = (self._log_div + 1) % 15    # log a ~2 Hz
        if self._log_div == 0:
            self.get_logger().info('wheel_speed: %+.3f m/s (delta=%d, dir=%+d)'
                                   % (speed, delta, int(self.direction)))


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
