#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# nav_config: CONTRATO de configuracion de navegacion (autodescrito), consumible por la WEB
# hoy y por el MCP/LLM manana (Capa 3). El LLM lee /nav_config para saber que puede tocar y
# que hace cada cosa, y escribe /nav_config/set para ajustar el comportamiento del robot.
#
#   /nav_config       (String JSON, latched)  -> GET: params (clave/etiqueta/rango/unidad/desc/valor/restart)
#   /nav_config/set   (String JSON)           -> SET: {"clave": valor, ...}
#
# Dos formas de aplicar (verificado empiricamente):
#   * EN CALIENTE (servicio de parametros): velocidad, tolerancia_objetivo, margen_seguridad.
#   * REQUIERE REINICIO de Nav2: marcha_atras y radio_giro_min -> cambiar motion_model del Smac
#     en caliente CUELGA el planner, asi que se reescribe el yaml y se reinician los servidores.
import json, os, re, subprocess, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType
from rclpy.qos import QoSProfile, QoSDurabilityPolicy

YAML = os.path.expanduser('~/robocar/src/robocar_pkg/config/nav2_bench.yaml')
RESTART_SH = os.path.expanduser('~/robocar/scripts/restart_nav2.sh')
RESTART_KEYS = {'marcha_atras', 'radio_giro_min'}

PARAMS = [
    {"key": "velocidad", "label": "Velocidad de crucero", "unit": "m/s",
     "min": 0.1, "max": 0.5, "step": 0.05, "default": 0.3, "restart": False,
     "desc": "Velocidad a la que avanza el robot. Mas alta = llega antes pero controla peor. (en caliente)"},
    {"key": "marcha_atras", "label": "Marcha atras", "type": "bool", "default": False, "restart": True,
     "desc": "Permite RETROCEDER para giros cerrados (Reeds-Shepp). Off = solo adelante (Dubin). "
             "REINICIA Nav2 (~15 s)."},
    {"key": "radio_giro_min", "label": "Radio de giro minimo", "unit": "m",
     "min": 0.4, "max": 1.5, "step": 0.05, "default": 0.93, "restart": True,
     "desc": "Lo cerrado que puede girar (Ackermann real ~0.93 m). Menor = giros mas cerrados. REINICIA Nav2 (~15 s)."},
    {"key": "tolerancia_objetivo", "label": "Tolerancia al objetivo", "unit": "m",
     "min": 0.1, "max": 0.6, "step": 0.05, "default": 0.25, "restart": False,
     "desc": "A que distancia del destino se da por LLEGADO. Mayor = mas facil de alcanzar. (en caliente)"},
    {"key": "margen_seguridad", "label": "Margen de seguridad", "unit": "m",
     "min": 0.05, "max": 0.4, "step": 0.05, "default": 0.15, "restart": False,
     "desc": "Distancia de seguridad a paredes (inflado). Mayor = mas seguro pero puede CERRAR puertas. (en caliente)"},
    {"key": "orientacion_final", "label": "Orientacion final", "type": "bool", "default": False, "restart": False,
     "desc": "Si el robot debe LLEGAR mirando a la orientacion pedida (util para aparcar/apuntar a algo). "
             "Off = solo importa el punto, llega mirando a cualquier lado. (en caliente)"},
    {"key": "distancia_paredes", "label": "Tendencia al centro", "unit": "",
     "min": 1.5, "max": 6.0, "step": 0.5, "default": 3.0, "restart": False,
     "desc": "Bajo = el robot va mas por el CENTRO de los pasillos (mas holgura); alto = puede ir mas "
             "PEGADO a las paredes (pasa por sitios mas justos). (en caliente)"},
    {"key": "suavidad", "label": "Suavidad de conduccion", "unit": "m",
     "min": 0.3, "max": 1.2, "step": 0.1, "default": 0.6, "restart": False,
     "desc": "Mayor = conduccion mas SUAVE (corta curvas, comoda); menor = mas CENIDA a la ruta "
             "(precisa pero brusca). (en caliente)"},
]


class NavConfig(Node):
    def __init__(self):
        super().__init__('nav_config')
        self.vals = {p["key"]: p["default"] for p in PARAMS}
        qos = QoSProfile(depth=1)
        qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        self.pub = self.create_publisher(String, '/nav_config', qos)
        self.create_subscription(String, '/nav_config/set', self.on_set, 10)
        servers = ['controller_server', 'global_costmap/global_costmap', 'local_costmap/local_costmap']
        self.cli = {s: self.create_client(SetParameters, '/%s/set_parameters' % s) for s in servers}
        self.publish_config('listo')
        self.get_logger().info('nav_config listo (GET /nav_config, SET /nav_config/set)')

    def publish_config(self, status=''):
        params = [dict(p, value=self.vals[p["key"]]) for p in PARAMS]
        m = String(); m.data = json.dumps({"status": status, "params": params})
        self.pub.publish(m)

    def _pv(self, value):
        v = ParameterValue()
        if isinstance(value, bool):
            v.type = ParameterType.PARAMETER_BOOL; v.bool_value = value
        elif isinstance(value, str):
            v.type = ParameterType.PARAMETER_STRING; v.string_value = value
        else:
            v.type = ParameterType.PARAMETER_DOUBLE; v.double_value = float(value)
        return v

    def _set(self, server, name, value):
        cl = self.cli.get(server)
        if cl is None:
            return
        if not cl.service_is_ready():
            cl.wait_for_service(timeout_sec=1.5)   # por si aun no se descubrio (arranque en frio)
        if not cl.service_is_ready():
            self.get_logger().warn('%s no listo' % server); return
        req = SetParameters.Request(); req.parameters = [Parameter(name=name, value=self._pv(value))]
        cl.call_async(req)   # fire-and-forget

    def apply_live(self, key, value):
        if key == 'velocidad':
            self._set('controller_server', 'FollowPath.desired_linear_vel', float(value))
        elif key == 'tolerancia_objetivo':
            self._set('controller_server', 'general_goal_checker.xy_goal_tolerance', float(value))
        elif key == 'margen_seguridad':
            self._set('global_costmap/global_costmap', 'inflation_layer.inflation_radius', float(value))
            self._set('local_costmap/local_costmap', 'inflation_layer.inflation_radius', float(value))
        elif key == 'orientacion_final':
            self._set('controller_server', 'general_goal_checker.yaw_goal_tolerance', 0.5 if value else 3.15)
        elif key == 'distancia_paredes':
            self._set('global_costmap/global_costmap', 'inflation_layer.cost_scaling_factor', float(value))
            self._set('local_costmap/local_costmap', 'inflation_layer.cost_scaling_factor', float(value))
        elif key == 'suavidad':
            self._set('controller_server', 'FollowPath.lookahead_dist', float(value))

    def rewrite_yaml(self):
        try:
            s = open(YAML).read()
        except Exception as e:
            self.get_logger().warn('no puedo leer yaml: %s' % e); return
        mm = 'REEDS_SHEPP' if self.vals['marcha_atras'] else 'DUBIN'
        rev = 'true' if self.vals['marcha_atras'] else 'false'
        s = re.sub(r'motion_model_for_search:\s*"[^"]*"', 'motion_model_for_search: "%s"' % mm, s)
        s = re.sub(r'allow_reversing:\s*\w+', 'allow_reversing: %s' % rev, s)
        s = re.sub(r'minimum_turning_radius:\s*[0-9.]+', 'minimum_turning_radius: %.3f' % float(self.vals['radio_giro_min']), s)
        s = re.sub(r'desired_linear_vel:\s*[0-9.]+', 'desired_linear_vel: %.3f' % float(self.vals['velocidad']), s)
        s = re.sub(r'xy_goal_tolerance:\s*[0-9.]+', 'xy_goal_tolerance: %.3f' % float(self.vals['tolerancia_objetivo']), s)
        s = re.sub(r'inflation_radius:\s*[0-9.]+', 'inflation_radius: %.3f' % float(self.vals['margen_seguridad']), s)
        yt = '0.5' if self.vals['orientacion_final'] else '3.15'
        s = re.sub(r'yaw_goal_tolerance:\s*[0-9.]+', 'yaw_goal_tolerance: %s' % yt, s)
        s = re.sub(r'cost_scaling_factor:\s*[0-9.]+', 'cost_scaling_factor: %.2f' % float(self.vals['distancia_paredes']), s)
        s = re.sub(r'(?m)^(\s*)lookahead_dist:\s*[0-9.]+',
                   lambda m: m.group(1) + ('lookahead_dist: %.2f' % float(self.vals['suavidad'])), s)
        open(YAML, 'w').write(s)

    def restart_nav2(self):
        self.rewrite_yaml()
        subprocess.Popen(['bash', RESTART_SH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def on_set(self, msg):
        try:
            changes = json.loads(msg.data)
        except Exception:
            self.publish_config('JSON invalido'); return
        applied = []; need_restart = False
        for k, v in changes.items():
            if k not in self.vals:
                continue
            self.vals[k] = v; applied.append(k)
            if k in RESTART_KEYS:
                need_restart = True
            else:
                self.apply_live(k, v)
        self.get_logger().info('SET %s (restart=%s)' % (applied, need_restart))
        if need_restart:
            self.publish_config('Reiniciando Nav2 (~15 s). Cuando vuelva, reenvia el destino.')
            self.restart_nav2()
        else:
            self.publish_config('Aplicado en caliente: ' + ', '.join(applied))


def main():
    rclpy.init(); n = NavConfig()
    try: rclpy.spin(n)
    except KeyboardInterrupt: pass
    n.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
