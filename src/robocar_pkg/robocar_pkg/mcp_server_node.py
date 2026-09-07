#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mcp_server_node: servidor MCP (Capa 3) — la fachada que un LLM usa para pilotar Robocar.
# Envoltorio FINO: la logica dura ya vive en el grafo (map_areas resuelve nombres, Nav2 navega,
# robocar_health vigila). Aqui solo se exponen 5 tools seguras con FastMCP sobre HTTP (:8090).
#
#   LEE:      /map_areas (String JSON, latched)   -> zonas {name, rect, goal}
#             /robocar/health (String JSON)       -> {scenario, ok, summary, checks}
#             /amcl_pose (PoseWithCovarianceStamped)
#   ESCRIBE:  accion /navigate_to_pose (NavigateToPose)  [cliente propio, como goal_relay]
#             /nav2_relay/cancel (Empty)          -> cancela tambien goals lanzados desde la web
#
# Frontera de seguridad: NO expone /cmd_vel, teleop, /initialpose, mapas ni lanzador de
# entornos. Solo puede hacer lo que la web ya hace: mandar un destino y cancelarlo.
# set_driving_style (nav_config) queda para v2 (exige disenar los clamps con calma).
#
# Host de prueba:  claude mcp add --transport http robocar http://robocar.local:8090/mcp
import json
import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSDurabilityPolicy
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import String, Empty
from fastmcp import FastMCP

NAV_TIMEOUT_S = 120.0     # tope de espera de una navegacion (banco: sobra; real: revisar)
ACCEPT_TIMEOUT_S = 5.0    # tope para que Nav2 acepte el goal


class RobocarBridge(Node):
    """Nodo rclpy: mantiene el estado (zonas, salud, pose) y ejecuta las acciones.
    Las tools MCP corren en otro hilo -> todo acceso a estado pasa por self.lock."""

    def __init__(self):
        super().__init__('mcp_server')
        self.lock = threading.Lock()
        self.areas = []          # [{name, rect, goal}]
        self.health = None       # {scenario, ok, summary, checks}
        self.pose = None         # (x, y)
        self.navigating_to = None
        self.goal_handle = None
        qos = QoSProfile(depth=1); qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        self.create_subscription(String, '/map_areas', self._areas_cb, qos)
        self.create_subscription(String, '/robocar/health', self._health_cb, 10)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self._pose_cb, 10)
        self.cancel_pub = self.create_publisher(Empty, '/nav2_relay/cancel', 10)
        self.ac = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.get_logger().info('mcp_server listo (tools MCP en :8090)')

    def _areas_cb(self, msg):
        try:
            areas = json.loads(msg.data).get('areas', [])
        except Exception:
            return
        with self.lock:
            self.areas = areas

    def _health_cb(self, msg):
        try:
            h = json.loads(msg.data)
        except Exception:
            return
        with self.lock:
            self.health = h

    def _pose_cb(self, msg):
        p = msg.pose.pose.position
        with self.lock:
            self.pose = (round(p.x, 3), round(p.y, 3))

    # ---- consultas (thread-safe) ----

    def snapshot(self):
        with self.lock:
            return dict(areas=list(self.areas), health=self.health,
                        pose=self.pose, navigating_to=self.navigating_to)

    def zone_of(self, x, y):
        with self.lock:
            for a in self.areas:
                x0, y0, x1, y1 = a['rect']
                if x0 <= x <= x1 and y0 <= y <= y1:
                    return a['name']
        return None

    def health_problem(self):
        """None si se puede navegar; si no, el texto del problema."""
        with self.lock:
            h = self.health
        if h is None:
            return 'sin datos de salud (robocar_health no publica); no se si el sistema esta listo'
        if h.get('scenario') not in ('BANCO', 'NAV_REAL'):
            return 'entorno %s activo: no hay pila de navegacion (hace falta BANCO o NAV_REAL)' % h.get('scenario')
        if not h.get('ok'):
            fails = '; '.join('%s (%s)' % (c['label'], c['info'])
                              for c in h.get('checks', []) if not c['ok']) or h.get('summary', '')
            return 'sistema con problemas: %s' % fails
        return None

    # ---- navegacion (bloqueante; se llama desde el hilo MCP) ----

    def navigate_blocking(self, name, gx, gy):
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.pose.position.x = float(gx)
        goal.pose.pose.position.y = float(gy)
        goal.pose.pose.orientation.w = 1.0
        if not self.ac.wait_for_server(timeout_sec=ACCEPT_TIMEOUT_S):
            return {'result': 'NAV_UNAVAILABLE', 'detalle': 'Nav2 no responde (accion /navigate_to_pose)'}
        done = threading.Event()
        outcome = {}

        def on_result(fut):
            st = fut.result().status  # 4=SUCCEEDED 5=CANCELED 6=ABORTED
            outcome['status'] = st
            done.set()

        def on_accepted(fut):
            gh = fut.result()
            if not gh.accepted:
                outcome['status'] = -1
                done.set(); return
            with self.lock:
                self.goal_handle = gh
            gh.get_result_async().add_done_callback(on_result)

        with self.lock:
            self.navigating_to = name
        self.ac.send_goal_async(goal).add_done_callback(on_accepted)
        finished = done.wait(NAV_TIMEOUT_S)
        with self.lock:
            gh = self.goal_handle
            self.goal_handle = None
            self.navigating_to = None
        if not finished:
            if gh is not None:
                gh.cancel_goal_async()
            return {'result': 'TIMEOUT',
                    'detalle': 'sin resultado en %.0f s; navegacion cancelada' % NAV_TIMEOUT_S}
        st = outcome.get('status')
        if st == 4:
            return {'result': 'ARRIVED'}
        if st == 5:
            return {'result': 'CANCELLED', 'detalle': 'la navegacion fue cancelada'}
        if st == -1:
            return {'result': 'BLOCKED', 'detalle': 'Nav2 rechazo el destino (¿fuera del mapa?)'}
        return {'result': 'BLOCKED',
                'detalle': 'no pudo llegar: destino inalcanzable (obstaculo, zona cerrada o fuera del mapa)'}

    def cancel_all(self):
        with self.lock:
            gh = self.goal_handle
        if gh is not None:
            gh.cancel_goal_async()
        self.cancel_pub.publish(Empty())   # tambien goals lanzados desde la web


# ---------- tools MCP ----------

mcp = FastMCP('robocar')
bridge = None  # se asigna en main()


@mcp.tool()
def navigate_to(lugar: str) -> dict:
    """Lleva el robot a un lugar etiquetado del mapa (p. ej. "cocina"). Usa nombres de
    list_known_places; NUNCA inventes lugares. La navegacion tarda decenas de segundos y esta
    llamada espera al resultado. Devuelve result: ARRIVED (llegue), BLOCKED (no pude llegar:
    NO reintentes a ciegas, informa al usuario), CANCELLED, TIMEOUT, UNKNOWN_PLACE (con la
    lista de lugares validos), UNHEALTHY (el sistema no esta listo; di que falla) o
    NAV_UNAVAILABLE. El robot es tipo coche (Ackermann): no gira sobre si mismo y en sitios
    estrechos maniobra en 3 puntos (k-turn); eso es normal, no un fallo."""
    problem = bridge.health_problem()
    if problem:
        return {'result': 'UNHEALTHY', 'detalle': problem}
    snap = bridge.snapshot()
    if snap['navigating_to']:
        return {'result': 'BLOCKED',
                'detalle': 'ya hay una navegacion en curso hacia "%s"; usa stop_navigation primero'
                           % snap['navigating_to']}
    name = str(lugar).strip().lower()
    area = next((a for a in snap['areas'] if a['name'] == name), None)
    if area is None:
        return {'result': 'UNKNOWN_PLACE',
                'lugares_conocidos': [a['name'] for a in snap['areas']]}
    return bridge.navigate_blocking(name, area['goal'][0], area['goal'][1])


@mcp.tool()
def get_current_location() -> dict:
    """Posicion actual del robot: coordenadas (x, y) en metros en el frame del mapa y, si cae
    dentro de una zona etiquetada, el nombre de la zona (si no, zona: null). Si no hay pose
    es que la localizacion (AMCL) aun no ha publicado."""
    snap = bridge.snapshot()
    if snap['pose'] is None:
        return {'error': 'sin pose: la localizacion (AMCL) aun no ha publicado'}
    x, y = snap['pose']
    return {'x': x, 'y': y, 'zona': bridge.zone_of(x, y)}


@mcp.tool()
def list_known_places() -> dict:
    """Lista los lugares etiquetados del mapa a los que se puede navegar. Si esta vacia, aun
    no se han etiquetado zonas (se hace desde la web del panel) y navigate_to no tiene destinos."""
    snap = bridge.snapshot()
    return {'lugares': [a['name'] for a in snap['areas']]}


@mcp.tool()
def stop_navigation() -> dict:
    """Detiene INMEDIATAMENTE la navegacion en curso (tambien si se lanzo desde la web).
    Siempre segura de llamar, aunque el robot este parado."""
    bridge.cancel_all()
    return {'result': 'STOPPED'}


@mcp.tool()
def get_situation() -> dict:
    """Foto del estado del sistema: entorno activo (BANCO = simulacion, el coche real NO se
    mueve; NAV_REAL = navegacion con el coche fisico; SLAM = cartografiando, no se puede
    navegar; NINGUNO = apagado), si esta sano (y que falla si no), lugares conocidos, pose y
    si hay navegacion en curso. Llamala antes de planear varias acciones o si algo falla."""
    snap = bridge.snapshot()
    h = snap['health'] or {}
    return {
        'entorno': h.get('scenario', 'DESCONOCIDO'),
        'sano': bool(h.get('ok')),
        'problemas': [('%s: %s' % (c['label'], c['info'])).strip(': ')
                      for c in h.get('checks', []) if not c['ok']],
        'lugares': [a['name'] for a in snap['areas']],
        'pose': snap['pose'],
        'navegando_hacia': snap['navigating_to'],
    }


def main():
    global bridge
    rclpy.init()
    bridge = RobocarBridge()

    # executor rclpy en hilo aparte; MISMO patron anti busy-spin que goal_relay (en Humble,
    # un goal activo deja una guard condition siempre "lista" y spin() gira sin freno)
    def spin():
        import time
        while rclpy.ok():
            rclpy.spin_once(bridge, timeout_sec=0.1)
            time.sleep(0.05)
    threading.Thread(target=spin, daemon=True).start()

    try:
        mcp.run(transport='streamable-http', host='0.0.0.0', port=8090)
    except KeyboardInterrupt:
        pass
    bridge.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
