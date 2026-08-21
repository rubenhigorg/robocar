#!/usr/bin/env python3
# slam_checkpoint_node: gestion del SLAM para cartografiar el piso.
#
#  CHECKPOINTS (sobrevivir a derrapes): en cuanto una rueda patina, la odometria miente, Cartographer
#  salta de pose y el mapa deja de ser valido; con checkpoints frecuentes un derrape solo cuesta lo
#  mapeado desde el ultimo guardado. Cada checkpoint guarda el .pbstream Y la POSE del robot (sidecar
#  .json) para poder REENGANCHAR justo donde estaba al reanudar.
#    /slam/checkpoint       (std_msgs/Empty)  -> guarda AHORA
#    /slam/checkpoint_auto  (std_msgs/Bool)   -> guardado automatico (cada 30 s) ON/OFF
#    /slam/checkpoint_status(std_msgs/String) -> estado para la web
#
#  REINICIAR / VOLVER + CHEQUEO:
#    /slam/reinit (Empty) -> Cartographer fresco (mapa vacio, nuevo 0,0)
#    /slam/resume (Empty) -> carga el ultimo checkpoint y reengancha en SU pose (start_trajectory)
#    /slam/reinit_status (String) -> progreso/resultado + chequeo de la cadena ("PREPARADO").
import os, glob, time, json, math, threading, subprocess
import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from std_msgs.msg import Empty, Bool, String
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry, OccupancyGrid
from tf2_msgs.msg import TFMessage
from cartographer_ros_msgs.srv import WriteState


class Ckpt(Node):
    def __init__(self):
        super().__init__('slam_checkpoint')
        self.declare_parameter('dir', os.path.expanduser('~/robocar/maps/checkpoints'))
        self.declare_parameter('keep', 8)
        self.declare_parameter('auto_interval', 30.0)
        self.dir = self.get_parameter('dir').value
        os.makedirs(self.dir, exist_ok=True)
        self.keep = int(self.get_parameter('keep').value)
        self.interval = float(self.get_parameter('auto_interval').value)
        try:
            self.cfg_dir = os.path.join(get_package_share_directory('robocar_slam'), 'config')
        except Exception:
            self.cfg_dir = os.path.expanduser('~/robocar/src/install/robocar_slam/share/robocar_slam/config')

        self.cli = self.create_client(WriteState, '/write_state')
        self.pub = self.create_publisher(String, '/slam/checkpoint_status', 10)
        self.rpub = self.create_publisher(String, '/slam/reinit_status', 10)
        self.create_subscription(Empty, '/slam/checkpoint', lambda m: self.save('manual'), 10)
        self.create_subscription(Bool, '/slam/checkpoint_auto', self._toggle, 10)
        self.create_subscription(Empty, '/slam/reinit', lambda m: self.reinit(), 10)
        self.create_subscription(Empty, '/slam/resume', lambda m: self.resume(), 10)

        # liveness + valores de TF (para chequeo de salud y para guardar la pose del robot)
        self._seen = {}
        self._tf = {}
        self.create_subscription(LaserScan, '/scan', lambda m: self._mark('scan'), 10)
        self.create_subscription(Odometry, '/odometry/filtered', lambda m: self._mark('odom'), 10)
        self.create_subscription(OccupancyGrid, '/map', lambda m: self._mark('map'), 1)
        self.create_subscription(TFMessage, '/tf', self._on_tf, 10)

        self._busy = False
        self._timer = None
        self._reiniting = False
        self.get_logger().info('slam_checkpoint listo (dir=%s, keep=%d)' % (self.dir, self.keep))
        self.status('listo')

    # ---------- utilidades ----------
    def _mark(self, k):
        self._seen[k] = time.time()

    @staticmethod
    def _yaw(q):
        return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

    def _on_tf(self, m):
        now = time.time()
        for t in m.transforms:
            pair = t.header.frame_id + '>' + t.child_frame_id
            if pair in ('map>odom', 'odom>base_link'):
                self._seen['map_odom' if pair == 'map>odom' else 'odom_base'] = now
                tr = t.transform.translation
                self._tf[pair] = (tr.x, tr.y, self._yaw(t.transform.rotation))

    def _map_base(self):
        """Pose actual del robot en el frame del mapa (map->odom * odom->base)."""
        mo = self._tf.get('map>odom'); ob = self._tf.get('odom>base_link')
        if not mo or not ob:
            return None
        c, s = math.cos(mo[2]), math.sin(mo[2])
        return {'x': mo[0] + ob[0] * c - ob[1] * s,
                'y': mo[1] + ob[0] * s + ob[1] * c,
                'yaw': mo[2] + ob[2]}

    def status(self, msg):
        self.get_logger().info('checkpoint: ' + msg)
        self.pub.publish(String(data=msg))

    def rstatus(self, msg):
        self.get_logger().info('reinit: ' + msg)
        self.rpub.publish(String(data=msg))

    # ---------- checkpoints ----------
    def _toggle(self, m):
        if m.data and self._timer is None:
            self._timer = self.create_timer(self.interval, lambda: self.save('auto'))
            self.status('auto ON (cada %ds)' % int(self.interval))
        elif not m.data and self._timer is not None:
            self._timer.cancel(); self._timer = None
            self.status('auto OFF')

    def save(self, tag):
        if self._busy:
            return
        if not (self.cli.service_is_ready() or self.cli.wait_for_service(timeout_sec=2.0)):
            self.status('ERROR: /write_state no disponible (arranco cartographer?)'); return
        self._busy = True
        fn = os.path.join(self.dir, 'ckpt_%s.pbstream' % time.strftime('%Y%m%d_%H%M%S'))
        pose = self._map_base()   # se captura AHORA (antes de la llamada asincrona)
        req = WriteState.Request()
        req.filename = fn
        req.include_unfinished_submaps = True
        fut = self.cli.call_async(req)

        def done(f):
            self._busy = False
            try:
                f.result()
                ok = os.path.exists(fn) and os.path.getsize(fn) > 0
                if ok and pose:
                    try:
                        json.dump(pose, open(fn[:-len('.pbstream')] + '.json', 'w'))
                    except Exception:
                        pass
                self.rotate()
                self.status('%s guardado (%s)%s' % (os.path.basename(fn), tag,
                            '' if pose else ' [sin pose]') if ok
                            else 'aviso: %s no aparecio' % os.path.basename(fn))
            except Exception as e:
                self.status('ERROR al guardar: %s' % str(e)[:60])
        fut.add_done_callback(done)

    def rotate(self):
        files = sorted(glob.glob(os.path.join(self.dir, 'ckpt_*.pbstream')))
        for old in (files[:-self.keep] if self.keep > 0 else []):
            for f in (old, old[:-len('.pbstream')] + '.json'):
                try:
                    os.remove(f)
                except Exception:
                    pass

    # ---------- reiniciar / volver a checkpoint + chequeo ----------
    def reinit(self):
        self._start_restart(resume=False)

    def resume(self):
        self._start_restart(resume=True)

    def _start_restart(self, resume):
        if self._reiniting:
            return
        self._reiniting = True
        threading.Thread(target=lambda: self._do_restart(resume), daemon=True).start()

    def _do_restart(self, resume):
        try:
            load = ''
            pose = None
            if resume:
                files = sorted(glob.glob(os.path.join(self.dir, 'ckpt_*.pbstream')))
                if not files:
                    self.rstatus('NO hay checkpoints guardados para volver.'); return
                load = files[-1]
                jf = load[:-len('.pbstream')] + '.json'
                if os.path.exists(jf):
                    try:
                        pose = json.load(open(jf))
                    except Exception:
                        pose = None
                self.rstatus('volviendo al ultimo checkpoint (%s)%s...' % (
                    os.path.basename(load), '' if pose else ' [sin pose -> reengancha por laser]'))
            else:
                self.rstatus('reiniciando cartografia (mapa vacio, nuevo 0,0)...')

            # Reinicia SOLO Cartographer (mantiene rplidar/EKF/sensores). Rapido, ~6 s.
            for p in ('robocar_slam slam.launch', 'cartographer_occupancy_grid_node', 'cartographer_node'):
                subprocess.run(['pkill', '-9', '-f', p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2.5)
            env = dict(os.environ)
            env.pop('SLAM_LOAD_STATE', None); env.pop('SLAM_NO_AUTOSTART', None)
            if load:
                env['SLAM_LOAD_STATE'] = load
                if pose:
                    env['SLAM_NO_AUTOSTART'] = '1'   # la trayectoria la arranca este nodo con la pose
            log = open(os.path.expanduser('~/robocar/logs/slam.log'), 'ab', buffering=0)
            subprocess.Popen(['ros2', 'launch', 'robocar_slam', 'slam.launch.py'],
                             env=env, stdout=log, stderr=log, start_new_session=True)

            if load and pose:
                self._start_trajectory(pose)   # reengancha en la pose del checkpoint
            else:
                self.rstatus('cartografia arrancando, comprobando la cadena...')

            t0 = time.time()
            while time.time() - t0 < 15:
                time.sleep(2.0)
                if self._health_check(final=False):
                    break
            self._health_check(final=True)
        except Exception as e:
            self.rstatus('ERROR: %s' % str(e)[:70])
        finally:
            self._reiniting = False

    def _start_trajectory(self, pose):
        # Via subprocess (ros2 service call): llamar el servicio desde este hilo con rclpy
        # deadlockea con el executor de spin. Espera a que cartographer levante el servicio.
        self.rstatus('reenganchando en la pose del checkpoint (%.2f, %.2f)...' % (pose['x'], pose['y']))
        qz, qw = math.sin(pose['yaw'] / 2.0), math.cos(pose['yaw'] / 2.0)
        arg = ("{configuration_directory: %s, configuration_basename: robocar_2d.lua, "
               "use_initial_pose: true, initial_pose: {position: {x: %f, y: %f, z: 0.0}, "
               "orientation: {x: 0.0, y: 0.0, z: %f, w: %f}}, relative_to_trajectory_id: 0}"
               % (self.cfg_dir, float(pose['x']), float(pose['y']), qz, qw))
        try:
            r = subprocess.run(['ros2', 'service', 'call', '/start_trajectory',
                                'cartographer_ros_msgs/srv/StartTrajectory', arg],
                               env=os.environ, timeout=25,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = r.stdout.decode(errors='ignore')
            if 'code=0' in out or 'Success' in out:
                self.rstatus('reenganchado en la pose del checkpoint, comprobando...')
            else:
                self.rstatus('aviso: start_trajectory no OK: %s' % out.strip().split(chr(10))[-1][:70])
        except Exception as e:
            self.rstatus('aviso: start_trajectory fallo: %s' % str(e)[:60])

    def _health_check(self, final=True):
        now = time.time()
        items = [
            ('scan',      3.0, 'LIDAR /scan'),
            ('odom',      3.0, 'odometria /odometry/filtered'),
            ('odom_base', 3.0, 'TF odom->base (EKF)'),
            ('map_odom',  6.0, 'TF map->odom (Cartographer)'),
            ('map',       8.0, '/map'),
        ]
        bad = [label for k, maxage, label in items
               if self._seen.get(k) is None or (now - self._seen[k]) > maxage]
        if not final:
            return len(bad) == 0
        if not bad:
            self.rstatus('PREPARADO: todo OK (LIDAR + odometria + TF + mapa). Listo para cartografiar.')
        else:
            self.rstatus('NO listo. Falta/no llega: ' + ' ; '.join(bad))
        return len(bad) == 0


def main():
    rclpy.init()
    n = Ckpt()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
