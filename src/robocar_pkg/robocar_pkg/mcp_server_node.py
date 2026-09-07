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
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, qos_profile_sensor_data
from nav2_msgs.action import NavigateToPose, ComputePathToPose
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from std_msgs.msg import String, Empty
from sensor_msgs.msg import LaserScan
from fastmcp import FastMCP

NAV_TIMEOUT_S = 300.0     # default (parametrizable nav_timeout_s); real con maniobras 3-puntos = largo
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
        self.declare_parameter('nav_timeout_s', NAV_TIMEOUT_S)
        self.declare_parameter('accept_timeout_s', ACCEPT_TIMEOUT_S)
        self.nav_timeout = float(self.get_parameter('nav_timeout_s').value)
        self.accept_timeout = float(self.get_parameter('accept_timeout_s').value)
        # F2 (escritura controlada): estilo de conduccion + localizar en home
        self.cfg_pub = self.create_publisher(String, '/nav_config/set', 10)
        self.initpose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)  # F4: SOLO para parada dura (cero)
        # F1 (lectura): energia, laser, feedback de nav, planner para distancia
        self.energy = None
        self.scan = None
        self.nav_distance = None
        try:
            from messages_pkg.msg import Energy
            self.create_subscription(Energy, '/energy', self._energy_cb, 10)
        except Exception:
            self.get_logger().warn('messages_pkg/Energy no disponible; get_battery dara SIN_DATOS')
        self.create_subscription(LaserScan, '/scan', self._scan_cb, qos_profile_sensor_data)
        self.planner_ac = ActionClient(self, ComputePathToPose, '/compute_path_to_pose')
        self.declare_parameter('home_x', 0.13)
        self.declare_parameter('home_y', 0.56)
        self.declare_parameter('home_yaw', 1.676)
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
        if h.get('scenario') == 'NAV_REAL':
            with self.lock:
                localizado = self.pose is not None
            if not localizado:
                return 'no localizado: AMCL sin pose. Fija la pose del robot desde la web (pista) antes de navegar'
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
        if not self.ac.wait_for_server(timeout_sec=self.accept_timeout):
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
            self.nav_distance = None
        self.ac.send_goal_async(goal, feedback_callback=self._nav_feedback).add_done_callback(on_accepted)
        finished = done.wait(self.nav_timeout)
        with self.lock:
            gh = self.goal_handle
            self.goal_handle = None
            self.navigating_to = None
        if not finished:
            if gh is not None:
                gh.cancel_goal_async()
            return {'result': 'TIMEOUT',
                    'detalle': 'sin resultado en %.0f s; navegacion cancelada' % self.nav_timeout}
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

    def set_nav_config(self, changes):
        self.cfg_pub.publish(String(data=json.dumps(changes)))

    def find_home_zone(self):
        HOME = ('casa', 'home', 'base', 'dock')
        with self.lock:
            for a in self.areas:
                if a['name'] in HOME:
                    return a
        return None

    def localize_home(self):
        import math
        hx = float(self.get_parameter('home_x').value)
        hy = float(self.get_parameter('home_y').value)
        hyaw = float(self.get_parameter('home_yaw').value)
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = hx
        msg.pose.pose.position.y = hy
        msg.pose.pose.orientation.z = math.sin(hyaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(hyaw / 2.0)
        cov = [0.0] * 36
        cov[0] = 0.25; cov[7] = 0.25; cov[35] = 0.068
        msg.pose.covariance = cov
        self.initpose_pub.publish(msg)
        return {'x': round(hx, 3), 'y': round(hy, 3), 'yaw_deg': round(math.degrees(hyaw), 1)}

    def current_scenario(self):
        with self.lock:
            h = self.health
        return (h or {}).get('scenario')

    def log_action(self, action):
        self.get_logger().info('ACCION MCP: %s' % action)

    def hard_stop(self):
        import time as _t
        self.cancel_all()            # cancela el goal (web incluida)
        z = Twist()
        for _ in range(10):          # fuerza velocidad cero ~0.5 s
            self.cmd_pub.publish(z); _t.sleep(0.05)

    def _energy_cb(self, msg):
        with self.lock:
            self.energy = {'bateria_1_V': round(msg.voltage_battery_1, 2),
                           'bateria_2_V': round(msg.voltage_battery_2, 2),
                           'bateria_3_V': round(msg.voltage_battery_3, 2),
                           'corriente_A': round(msg.current, 2)}

    def _scan_cb(self, msg):
        self.scan = msg

    def _nav_feedback(self, fb):
        try:
            self.nav_distance = round(fb.feedback.distance_remaining, 2)
        except Exception:
            pass

    def surroundings(self):
        import math
        sc = self.scan
        if sc is None:
            return None
        sect = {'frente': [], 'izquierda': [], 'atras': [], 'derecha': []}
        for i, r in enumerate(sc.ranges):
            if r is None or r <= 0.0 or math.isinf(r) or math.isnan(r) or r < sc.range_min:
                continue
            ang = math.degrees(sc.angle_min + i * sc.angle_increment)
            a = (ang + 180.0) % 360.0 - 180.0
            if -30 <= a <= 30: sect['frente'].append(r)
            elif 60 <= a <= 120: sect['izquierda'].append(r)
            elif a >= 150 or a <= -150: sect['atras'].append(r)
            elif -120 <= a <= -60: sect['derecha'].append(r)
        return {k + '_min_m': (round(min(v), 2) if v else None) for k, v in sect.items()}

    def compute_distance(self, gx, gy):
        import threading, math
        if not self.planner_ac.wait_for_server(timeout_sec=self.accept_timeout):
            return None
        goal = ComputePathToPose.Goal()
        goal.goal = PoseStamped()
        goal.goal.header.frame_id = 'map'
        goal.goal.pose.position.x = float(gx)
        goal.goal.pose.position.y = float(gy)
        goal.goal.pose.orientation.w = 1.0
        goal.use_start = False
        done = threading.Event(); res = {}
        def on_res(fut):
            try: res['path'] = fut.result().result.path
            except Exception: res['path'] = None
            done.set()
        def on_acc(fut):
            gh = fut.result()
            if not gh.accepted:
                done.set(); return
            gh.get_result_async().add_done_callback(on_res)
        self.planner_ac.send_goal_async(goal).add_done_callback(on_acc)
        if not done.wait(10.0):
            return None
        path = res.get('path')
        if not path or not path.poses:
            return None
        d = 0.0; ps = path.poses
        for i in range(1, len(ps)):
            d += math.hypot(ps[i].pose.position.x - ps[i-1].pose.position.x,
                            ps[i].pose.position.y - ps[i-1].pose.position.y)
        return round(d, 2)


# ---------- tools MCP ----------

mcp = FastMCP('robocar')
bridge = None  # se asigna en main()

STYLES = {
    'lento':   {'velocidad': 0.15, 'velocidad_min_curva': 0.10, 'tolerancia_objetivo': 0.20},
    'normal':  {'velocidad': 0.30, 'velocidad_min_curva': 0.15, 'tolerancia_objetivo': 0.25},
    'rapido':  {'velocidad': 0.45, 'velocidad_min_curva': 0.20, 'tolerancia_objetivo': 0.30},
    'preciso': {'velocidad': 0.15, 'velocidad_min_curva': 0.10, 'tolerancia_objetivo': 0.10,
                'suavidad': 0.40, 'margen_seguridad': 0.20},
}


@mcp.tool()
def navigate_to(lugar: str, confirmar: bool = False, esperar: bool = True) -> dict:
    """Lleva el robot a un lugar etiquetado del mapa (p. ej. "cocina"). Usa nombres de
    list_known_places; NUNCA inventes lugares. La navegacion tarda decenas de segundos y esta
    llamada espera al resultado. Devuelve result: ARRIVED (llegue), BLOCKED (no pude llegar:
    NO reintentes a ciegas, informa al usuario), CANCELLED, TIMEOUT, UNKNOWN_PLACE (con la
    lista de lugares validos), UNHEALTHY (el sistema no esta listo; di que falla) o
    NAV_UNAVAILABLE. El robot es tipo coche (Ackermann): no gira sobre si mismo y en sitios
    estrechos maniobra en 3 puntos (k-turn); eso es normal, no un fallo. En NAV_REAL (coche real) requiere confirmar=true (avisa antes al usuario); en BANCO no hace falta."""
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
    if bridge.current_scenario() == 'NAV_REAL' and not confirmar:
        return {'result': 'PENDING_CONFIRM',
                'detalle': 'esto MOVERA el coche real hacia "%s". Avisa al usuario y vuelve a llamar con confirmar=true' % name}
    bridge.log_action('navigate_to %s (confirmar=%s, esperar=%s)' % (name, confirmar, esperar))
    if not esperar:
        import threading
        threading.Thread(target=lambda: bridge.navigate_blocking(name, area['goal'][0], area['goal'][1]),
                         daemon=True).start()
        return {'result': 'EN_CURSO', 'hacia': name, 'detalle': 'navegando; consulta get_nav_status / stop_navigation'}
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
    bridge.log_action('stop_navigation')
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


@mcp.tool()
def set_driving_style(estilo: str) -> dict:
    """Ajusta el ESTILO de conduccion (velocidad y prudencia). Estilos: "lento" (0.15 m/s, seguro),
    "normal" (0.30), "rapido" (0.45), "preciso" (lento y ce\u00f1ido, para maniobras finas). En caliente
    (no reinicia la navegacion). Devuelve OK con lo aplicado, o UNKNOWN_STYLE con la lista."""
    est = str(estilo).strip().lower()
    if est not in STYLES:
        return {'result': 'UNKNOWN_STYLE', 'estilos_validos': list(STYLES.keys())}
    bridge.log_action('set_driving_style %s' % est)
    bridge.set_nav_config(STYLES[est])
    return {'result': 'OK', 'estilo': est, 'aplicado': STYLES[est]}


@mcp.tool()
def go_home(confirmar: bool = False) -> dict:
    """Lleva el robot a su base (zona etiquetada casa/home/base/dock). Como navigate_to pero al punto
    de inicio. Devuelve ARRIVED/BLOCKED/... o NO_HOME si no hay zona de base definida (etiquetala en la web). En NAV_REAL requiere confirmar=true."""
    problem = bridge.health_problem()
    if problem:
        return {'result': 'UNHEALTHY', 'detalle': problem}
    snap = bridge.snapshot()
    if snap['navigating_to']:
        return {'result': 'BLOCKED', 'detalle': 'ya hay una navegacion en curso hacia "%s"' % snap['navigating_to']}
    area = bridge.find_home_zone()
    if area is None:
        return {'result': 'NO_HOME', 'detalle': 'no hay zona de base (casa/home/base/dock) etiquetada en el mapa'}
    if bridge.current_scenario() == 'NAV_REAL' and not confirmar:
        return {'result': 'PENDING_CONFIRM',
                'detalle': 'esto MOVERA el coche real a la base "%s". Avisa al usuario y vuelve con confirmar=true' % area['name']}
    bridge.log_action('go_home %s (confirmar=%s)' % (area['name'], confirmar))
    return bridge.navigate_blocking(area['name'], area['goal'][0], area['goal'][1])


@mcp.tool()
def localize_at_home() -> dict:
    """Fija la localizacion del robot en su punto de inicio CONOCIDO (home) del mapa. Usar SOLO si el
    robot esta fisicamente en ese punto. Util en NAV_REAL para localizar sin la web. Devuelve la pose
    fijada; despues conviene mover un poco el robot para que AMCL converja."""
    bridge.log_action('localize_at_home')
    p = bridge.localize_home()
    return {'result': 'OK', 'pose_fijada': p,
            'nota': 'verifica que el laser cuadra con el mapa; si no, corrige la pose desde la web'}


@mcp.tool()
def emergency_stop() -> dict:
    """PARADA DE EMERGENCIA: cancela la navegacion en curso Y fuerza al robot a detenerse en el
    acto (velocidad cero directa). Mas contundente que stop_navigation. Siempre segura de llamar,
    aunque el robot este parado. Usala si algo va mal o el usuario dice para/stop/emergencia."""
    bridge.log_action('EMERGENCY_STOP')
    bridge.hard_stop()
    return {'result': 'EMERGENCY_STOPPED'}


@mcp.tool()
def get_battery() -> dict:
    """Estado de energia: tensiones de las 3 baterias (V) y corriente (A). Util para decidir si hay
    bateria para una tarea. SIN_DATOS si el sensor de energia (/energy) no publica en este entorno."""
    with bridge.lock:
        e = dict(bridge.energy) if bridge.energy else None
    if e is None:
        return {'result': 'SIN_DATOS', 'detalle': 'el sensor de energia (/energy) no publica aqui'}
    return dict(result='OK', **e)


@mcp.tool()
def get_nav_status() -> dict:
    """Estado de la navegacion en curso: si esta navegando, hacia donde y distancia restante (m).
    Pensada para usar tras navigate_to(esperar=false) y seguir el progreso."""
    snap = bridge.snapshot()
    return {'navegando': snap['navigating_to'] is not None, 'hacia': snap['navigating_to'],
            'distancia_restante_m': bridge.nav_distance}


@mcp.tool()
def distance_to(lugar: str) -> dict:
    """Distancia por RUTA (m) y tiempo estimado (s) hasta un lugar etiquetado, SIN mover el robot
    (planifica y mide). UNKNOWN_PLACE si no existe; NO_PATH si no hay ruta posible."""
    name = str(lugar).strip().lower()
    snap = bridge.snapshot()
    area = next((a for a in snap['areas'] if a['name'] == name), None)
    if area is None:
        return {'result': 'UNKNOWN_PLACE', 'lugares_conocidos': [a['name'] for a in snap['areas']]}
    d = bridge.compute_distance(area['goal'][0], area['goal'][1])
    if d is None:
        return {'result': 'NO_PATH', 'detalle': 'no se pudo planificar una ruta al lugar'}
    vel = 0.25
    return {'result': 'OK', 'lugar': name, 'distancia_m': d, 'eta_s': round(d / vel, 1)}


@mcp.tool()
def describe_surroundings() -> dict:
    """Obstaculos alrededor del robot (del laser): distancia minima (m) por sector -- frente,
    izquierda, derecha, atras. null en un sector = despejado. SIN_DATOS si el laser no publica."""
    s = bridge.surroundings()
    if s is None:
        return {'result': 'SIN_DATOS', 'detalle': 'el laser (/scan) no publica aqui'}
    return dict(result='OK', **s)


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
