#!/usr/bin/env python3
# Puente TF -> /amcl_pose: publica la pose map->base_link (la que da Cartographer-localization)
# como geometry_msgs/PoseWithCovarianceStamped en /amcl_pose. Asi el panel (trayectorias.html, que
# consume /amcl_pose) y cualquier consumidor funcionan SIN cambios usando Cartographer en vez de AMCL.
import rclpy
from rclpy.node import Node
import tf2_ros
from geometry_msgs.msg import PoseWithCovarianceStamped


class TfToAmcl(Node):
    def __init__(self):
        super().__init__('tf_to_amclpose')
        self.buf = tf2_ros.Buffer()
        self.listener = tf2_ros.TransformListener(self.buf, self)
        self.pub = self.create_publisher(PoseWithCovarianceStamped, '/amcl_pose', 10)
        self.create_timer(0.1, self.tick)   # 10 Hz
        self.get_logger().info('tf_to_amclpose listo (map->base_link -> /amcl_pose)')

    def tick(self):
        try:
            t = self.buf.lookup_transform('map', 'base_link', rclpy.time.Time())
        except Exception:
            return   # aun no hay TF map->base_link (cartographer no ha localizado todavia)
        m = PoseWithCovarianceStamped()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = 'map'
        m.pose.pose.position.x = t.transform.translation.x
        m.pose.pose.position.y = t.transform.translation.y
        m.pose.pose.position.z = 0.0
        m.pose.pose.orientation = t.transform.rotation
        cov = [0.0] * 36
        cov[0] = 0.01; cov[7] = 0.01; cov[35] = 0.01   # baja -> el panel muestra LOCALIZADO estable
        m.pose.covariance = cov
        self.pub.publish(m)


def main():
    rclpy.init()
    n = TfToAmcl()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
