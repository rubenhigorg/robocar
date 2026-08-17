#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Fase 4 - evitacion de obstaculos REACTIVA con los 3 ultrasonidos delanteros.
# Distancias en cm (left/center/right). Logica:
#   - libre delante  -> avanza recto
#   - obstaculo delante (center < SLOW) -> frena y gira hacia el lado MAS LIBRE
#   - muy cerca (center < STOP) o encajonado -> para (o gira fuerte)
# Param dry_run=true -> NO publica /cmd_vel, solo imprime la decision (para probar
# la logica sin mover el coche). dry_run=false -> conduce.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from messages_pkg.msg import Distance

FAR = 300.0    # cm que asignamos a lectura invalida (-1 = sin eco)

class Avoider(Node):
    def __init__(self):
        super().__init__('obstacle_avoid')
        self.declare_parameter('dry_run', True)
        self.declare_parameter('drive_speed', 0.20)
        self.declare_parameter('max_angular', 0.4)
        self.declare_parameter('stop_cm', 25.0)     # < esto delante: critico
        self.declare_parameter('slow_cm', 55.0)     # < esto delante: esquivar
        self.declare_parameter('side_cm', 22.0)     # < esto a un lado: lado bloqueado
        self.dry = bool(self.get_parameter('dry_run').value)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Distance, '/ultrasound_data', self.cb, 10)
        self.n = 0
        self.get_logger().info('obstacle_avoid listo (dry_run=%s)' % self.dry)

    @staticmethod
    def clean(d):
        return FAR if (d is None or d < 2.0) else d   # <2cm o -1 -> invalido -> lejos

    def cb(self, msg):
        c = self.clean(msg.center_distance)
        l = self.clean(msg.left_distance)
        r = self.clean(msg.right_distance)
        drive = self.get_parameter('drive_speed').value
        maxw = self.get_parameter('max_angular').value
        stop = self.get_parameter('stop_cm').value
        slow = self.get_parameter('slow_cm').value
        side = self.get_parameter('side_cm').value

        if c > slow and l > side and r > side:
            v, w, act = drive, 0.0, 'AVANZA'
        elif c <= stop or (l < side and r < side and c < slow):
            # critico / encajonado
            if l < side and r < side:
                v, w, act = 0.0, 0.0, 'STOP (encajonado)'
            else:
                w = maxw if l > r else -maxw
                v, w, act = 0.0, w, 'GIRA %s (parado, muy cerca)' % ('IZQ' if w > 0 else 'DER')
        else:
            # obstaculo delante -> esquivar hacia el lado mas libre, despacio
            w = maxw if l > r else -maxw
            v, w, act = drive * 0.6, w, 'ESQUIVA %s' % ('IZQ' if w > 0 else 'DER')

        if not self.dry:
            t = Twist(); t.linear.x = float(v); t.angular.z = float(w); self.pub.publish(t)

        self.n = (self.n + 1) % 5     # ~2 Hz
        if self.n == 0:
            self.get_logger().info('c=%.0f l=%.0f r=%.0f -> %-22s (v=%.2f w=%+.2f)%s'
                                   % (c, l, r, act, v, w, '' if not self.dry else '  [DRY]'))


def main():
    rclpy.init()
    n = Avoider()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    if not n.dry:
        n.pub.publish(Twist())
    n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
