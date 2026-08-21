#!/usr/bin/env python3
# slam_checkpoint_node: gestion del SLAM para cartografiar el piso.
#
#  CHECKPOINTS (sobrevivir a derrapes): en cuanto una rueda patina, la odometria miente, Cartographer
#  salta de pose y el mapa deja de ser valido; con checkpoints frecuentes un derrape solo cuesta lo
#  mapeado desde el ultimo guardado.
#    /slam/checkpoint       (std_msgs/Empty)  -> guarda AHORA
#    /slam/checkpoint_auto  (std_msgs/Bool)   -> guardado automatico (cada 30 s) ON/OFF
#    /slam/checkpoint_status(std_msgs/String) -> estado para la web
#  Reanudar:  bash ~/robocar/scripts/bringupSLAM.sh --resume-latest
#
#  REINICIAR + CHEQUEO:
#    /slam/reinit           (std_msgs/Empty)  -> reinicia Cartographer (mapa vacio, nuevo 0,0) y
#                                                comprueba toda la cadena; avisa "PREPARADO".
#    /slam/reinit_status    (std_msgs/String) -> progreso/resultado del reinicio+chequeo.
import os, glob, time, threading, subprocess
import rclpy
from rclpy.node import Node
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

        self.cli = self.create_client(WriteState, '/write_state')
        self.pub = self.create_publisher(String, '/slam/checkpoint_status', 10)
        self.rpub = self.create_publisher(String, '/slam/reinit_status', 10)
        self.create_subscription(Empty, '/slam/checkpoint', lambda m: self.save('manual'), 10)
        self.create_subscription(Bool, '/slam/checkpoint_auto', self._toggle, 10)
        self.create_subscription(Empty, '/slam/reinit', lambda m: self.reinit(), 10)

        # liveness de la cadena (para el chequeo de salud)
        self._seen = {}
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

    def _on_tf(self, m):
        now = time.time()
        for t in m.transforms:
            pair = t.header.frame_id + '>' + t.child_frame_id
            if pair == 'map>odom':
                self._seen['map_odom'] = now
            elif pair == 'odom>base_link':
                self._seen['odom_base'] = now

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
        req = WriteState.Request()
        req.filename = fn
        req.include_unfinished_submaps = True
        fut = self.cli.call_async(req)

        def done(f):
            self._busy = False
            try:
                f.result()
                ok = os.path.exists(fn) and os.path.getsize(fn) > 0
                self.rotate()
                self.status('%s guardado (%s)' % (os.path.basename(fn), tag) if ok
                            else 'aviso: %s no aparecio' % os.path.basename(fn))
            except Exception as e:
                self.status('ERROR al guardar: %s' % str(e)[:60])
        fut.add_done_callback(done)

    def rotate(self):
        files = sorted(glob.glob(os.path.join(self.dir, 'ckpt_*.pbstream')))
        for old in (files[:-self.keep] if self.keep > 0 else []):
            try:
                os.remove(old)
            except Exception:
                pass

    # ---------- reiniciar + chequeo ----------
    def reinit(self):
        if self._reiniting:
            return
        self._reiniting = True
        threading.Thread(target=self._do_reinit, daemon=True).start()

    def _do_reinit(self):
        try:
            self.rstatus('reiniciando cartografia (mapa vacio, nuevo 0,0)...')
            # Reinicia SOLO Cartographer (mantiene rplidar/EKF/sensores). Rapido.
            for p in ('robocar_slam slam.launch', 'cartographer_occupancy_grid_node', 'cartographer_node'):
                subprocess.run(['pkill', '-9', '-f', p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2.5)
            env = dict(os.environ)
            env.pop('SLAM_LOAD_STATE', None)   # fresco: sin cargar checkpoint
            log = open(os.path.expanduser('~/robocar/logs/slam.log'), 'ab', buffering=0)
            subprocess.Popen(['ros2', 'launch', 'robocar_slam', 'slam.launch.py'],
                             env=env, stdout=log, stderr=log, start_new_session=True)
            self.rstatus('cartografia arrancando, comprobando la cadena...')
            # Espera a que cartographer publique de nuevo y chequea (hasta ~15 s)
            t0 = time.time(); ok = False
            while time.time() - t0 < 15:
                time.sleep(2.0)
                ok = self._health_check(final=False)
                if ok:
                    break
            self._health_check(final=True)
        except Exception as e:
            self.rstatus('ERROR reinit: %s' % str(e)[:70])
        finally:
            self._reiniting = False

    def _health_check(self, final=True):
        now = time.time()
        items = [
            ('scan',      3.0, 'LIDAR /scan'),
            ('odom',      3.0, 'odometria /odometry/filtered'),
            ('odom_base', 3.0, 'TF odom->base (EKF)'),
            ('map_odom',  6.0, 'TF map->odom (Cartographer)'),
            ('map',       8.0, '/map'),
        ]
        bad = []
        for k, maxage, label in items:
            t = self._seen.get(k)
            if t is None or (now - t) > maxage:
                bad.append(label)
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
