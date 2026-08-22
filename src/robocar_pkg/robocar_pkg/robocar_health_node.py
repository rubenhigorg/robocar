#!/usr/bin/env python3
# robocar_health_node: detecta QUE entorno esta activo y si esta SANO (sin duplicados, sin
# residuos de otros entornos, sin faltas). Publica /robocar/health (String JSON) para la web.
# Parte de la capa compartida: lo lanza cada bringup.
#
#   /robocar/health -> {"scenario","ok","summary","checks":[{"label","ok","info"}]}
import json, subprocess
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# patron (substring en la linea de comando del proceso) por nodo
SHARED = {'robot_state_publisher': 'robot_state_publisher',
          'rosbridge': 'lib/rosbridge_server/rosbridge_websocket',
          'panel(:8080)': 'http.server 8080'}
BANCO = {'sim_motion': 'sim_motion_node', 'sim_sensors': 'sim_sensors_node',
         'sim_map_grid': 'sim_map_grid_node', 'planner': 'nav2_planner/planner_server',
         'controller': 'nav2_controller/controller_server', 'bt_navigator': 'nav2_bt_navigator',
         'amcl': 'nav2_amcl/amcl', 'collision_monitor': 'nav2_collision_monitor',
         'goal_relay': 'goal_relay_node', 'nav_config': 'nav_config_node', 'map_areas': 'map_areas_node'}
SLAM = {'rplidar': 'rplidar_node', 'encoder': 'encoder_node', 'imu': 'accelerometer_node',
        'car_control': 'car_control_node', 'ekf': 'ekf_node', 'cartographer': 'cartographer_node',
        'occupancy_grid': 'cartographer_occupancy_grid_node'}
NAV_REAL = {'rplidar': 'rplidar_node', 'encoder': 'encoder_node', 'imu': 'accelerometer_node',
            'car_control': 'car_control_node', 'ekf': 'ekf_node', 'map_server': 'nav2_map_server',
            'amcl': 'nav2_amcl/amcl', 'planner': 'nav2_planner/planner_server',
            'controller': 'nav2_controller/controller_server'}
# nodos "firma" y singletons
SINGLETONS = {'rosbridge': 'lib/rosbridge_server/rosbridge_websocket', 'panel/lanzador': 'robocar_launcher',
              'robot_state_publisher': 'robot_state_publisher'}


class Health(Node):
    def __init__(self):
        super().__init__('robocar_health')
        self.pub = self.create_publisher(String, '/robocar/health', 10)
        self.create_timer(2.0, self.tick)
        self.get_logger().info('robocar_health listo')

    def _proc_lines(self):
        try:
            return subprocess.check_output(['ps', '-eo', 'args'], text=True, timeout=4).splitlines()
        except Exception:
            return []

    def tick(self):
        lines = self._proc_lines()
        def cnt(pat):
            return sum(1 for l in lines if pat in l)
        def present(d):
            return any(cnt(p) > 0 for p in d.values())

        sim = cnt('sim_map_grid_node') > 0 or cnt('sim_motion_node') > 0 or cnt('sim_sensors_node') > 0
        carto = cnt('cartographer_node') > 0
        mapsrv = cnt('nav2_map_server') > 0

        # escenario activo
        if sim and carto:
            scenario, expect, others = 'MIXTO (roto)', {}, {}
        elif sim:
            scenario, expect = 'BANCO', BANCO
            others = {'SLAM': SLAM, 'NAV_REAL': {'map_server': 'nav2_map_server'}}
        elif carto:
            scenario, expect = 'SLAM', SLAM
            others = {'BANCO': {'sim_map_grid': 'sim_map_grid_node', 'sim_motion': 'sim_motion_node',
                                'sim_sensors': 'sim_sensors_node'}}
        elif mapsrv:
            scenario, expect = 'NAV_REAL', NAV_REAL
            others = {'BANCO': {'sim_map_grid': 'sim_map_grid_node', 'sim_motion': 'sim_motion_node'},
                      'SLAM': {'cartographer': 'cartographer_node'}}
        else:
            scenario, expect, others = 'NINGUNO', {}, {}

        checks = []
        def add(label, ok, info=''):
            checks.append({'label': label, 'ok': bool(ok), 'info': info})

        if scenario == 'MIXTO (roto)':
            add('Entornos mezclados: banco + cartografia a la vez', False,
                'para cartographer o el banco; no pueden convivir')
        # singletons (unico de cada uno)
        for name, pat in SINGLETONS.items():
            c = cnt(pat)
            if scenario == 'NINGUNO' and c == 0:
                continue
            add('%s unico' % name, c == 1, '%d instancias' % c if c != 1 else '')
        if scenario not in ('NINGUNO', 'MIXTO (roto)'):
            # nodos del escenario completos
            missing = [k for k, p in expect.items() if cnt(p) == 0]
            add('nodos de %s completos' % scenario, not missing,
                ('faltan: ' + ', '.join(missing)) if missing else 'todos presentes')
            # sin duplicados en nodos clave del escenario
            dups = ['%s(%d)' % (k, cnt(p)) for k, p in expect.items() if cnt(p) > 1]
            add('sin nodos duplicados', not dups, (', '.join(dups)) if dups else '')
            # sin residuos de otros entornos
            residues = []
            for oname, od in others.items():
                for k, p in od.items():
                    if cnt(p) > 0:
                        residues.append('%s:%s' % (oname, k))
            add('sin residuos de otros entornos', not residues,
                ('presentes: ' + ', '.join(residues)) if residues else '')
            # 1 publicador de topics clave (conflictos)
            for topic in ('/map', '/scan', '/odometry/filtered'):
                n = self.count_publishers(topic)
                add('1 publicador de %s' % topic, n == 1, '%d publicadores' % n if n != 1 else '')

        ok = all(c['ok'] for c in checks) and scenario not in ('MIXTO (roto)',)
        if scenario == 'NINGUNO':
            ok = False
            summary = 'Sin entorno activo (arranca banco o cartografia)'
        else:
            summary = '%s · %s' % (scenario, 'SANO' if ok else 'PROBLEMAS')
        self.pub.publish(String(data=json.dumps(
            {'scenario': scenario, 'ok': ok, 'summary': summary, 'checks': checks})))


def main():
    rclpy.init()
    n = Health()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
