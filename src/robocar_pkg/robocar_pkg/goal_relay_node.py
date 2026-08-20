#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Relay: /goal_pose (PoseStamped) -> accion NavigateToPose de Nav2.
#
# La web publica un TOPIC facil (/goal_pose); Nav2 recibe el destino por una ACCION
# (NavigateToPose). Este nodo hace de puente: recibe el topic y llama a la accion. Es
# exactamente lo que hace RViz por dentro con su boton "Nav2 Goal".
#
#   /goal_pose (PoseStamped) --> [goal_relay] --accion NavigateToPose--> Nav2
#   /nav2_relay/cancel (Empty) --> cancela el destino en curso
#   /nav2_relay/status (String) <-- estado legible para la web (navegando, alcanzado, abortado)
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String, Empty


class GoalRelay(Node):
    def __init__(self):
        super().__init__('goal_relay')
        self.ac = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.create_subscription(PoseStamped, '/goal_pose', self.gcb, 10)
        self.create_subscription(Empty, '/nav2_relay/cancel', self.cancel_cb, 10)
        self.status = self.create_publisher(String, '/nav2_relay/status', 10)
        self.goal_handle = None
        self._last = None
        self.get_logger().info('goal_relay listo (/goal_pose -> NavigateToPose)')

    def _st(self, t):
        if t == self._last:          # dedupe: no republicar el mismo texto (alivia a rosbridge)
            return
        self._last = t
        m = String(); m.data = t; self.status.publish(m)

    def gcb(self, msg):
        if not self.ac.wait_for_server(timeout_sec=2.0):
            self._st('Nav2 no disponible'); return
        g = NavigateToPose.Goal()
        g.pose = msg
        if not g.pose.header.frame_id:
            g.pose.header.frame_id = 'map'
        self.get_logger().info('goal -> (%.2f, %.2f) [%s]' %
                               (msg.pose.position.x, msg.pose.position.y, g.pose.header.frame_id))
        self._st('destino (%.2f, %.2f) enviado' % (msg.pose.position.x, msg.pose.position.y))
        self.ac.send_goal_async(g, feedback_callback=self.fb).add_done_callback(self.accepted_cb)

    def accepted_cb(self, fut):
        gh = fut.result()
        if not gh.accepted:
            self._st('destino RECHAZADO (fuera del mapa?)'); return
        self.goal_handle = gh
        self._st('destino aceptado, navegando')
        gh.get_result_async().add_done_callback(self.result_cb)

    def fb(self, fb):
        d = fb.feedback.distance_remaining
        if d < 0.05:
            self._st('buscando ruta...')          # aun no hay plan (distancia 0)
        else:
            self._st('navegando: quedan %.1f m' % d)   # redondeo a 0.1 m + dedupe -> mucho menos churn

    def result_cb(self, fut):
        st = fut.result().status
        txt = {
            4: 'DESTINO ALCANZADO',
            5: 'cancelado',
            6: 'No pudo llegar: destino inalcanzable (sobre obstaculo, habitacion cerrada o fuera del mapa). Elige zona despejada (fuera del rojo).',
        }.get(st, 'fin (%d)' % st)
        self._st(txt)
        self.goal_handle = None

    def cancel_cb(self, _):
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
            self._st('cancelando destino...')


def main():
    rclpy.init(); n = GoalRelay()
    # OJO: rclpy.spin() gira sin freno mientras hay una accion NavigateToPose activa (una
    # guard condition del goal handle queda siempre "lista" en Humble) -> ~35% de CPU inutil.
    # Bucle con frecuencia acotada: atiende feedback/resultado/cancel con <20 ms de retardo
    # (imperceptible) pero elimina el busy-spin.
    try:
        while rclpy.ok():
            rclpy.spin_once(n, timeout_sec=0.1)
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
