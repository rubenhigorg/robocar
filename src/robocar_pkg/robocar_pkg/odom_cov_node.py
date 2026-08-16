import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class OdomCov(Node):
    """Estampa una covarianza sana en la odometria del laser (rf2o).

    rf2o publica /odom_rf2o con la matriz de covarianza a CEROS. El EKF de
    robot_localization interpreta covarianza cero como confianza infinita y el
    filtro diverge (pose -> 1e13). Este adaptador copia el mensaje y le pone una
    covarianza diagonal razonable en x, y, yaw (y grande en los ejes no usados),
    y lo republica para el EKF.
    """

    BIG = 1e6

    def __init__(self):
        super().__init__('odom_cov_node')
        self.declare_parameter('input_topic', 'odom_rf2o')
        self.declare_parameter('output_topic', 'odom_rf2o_cov')
        self.declare_parameter('xy_variance', 0.05)    # (m)^2  ~ std 0.22 m
        self.declare_parameter('yaw_variance', 0.02)   # (rad)^2 ~ std 0.14 rad

        inp = self.get_parameter('input_topic').value
        out = self.get_parameter('output_topic').value
        self.xy = float(self.get_parameter('xy_variance').value)
        self.yaw = float(self.get_parameter('yaw_variance').value)

        self.pub = self.create_publisher(Odometry, out, 10)
        self.sub = self.create_subscription(Odometry, inp, self.callback, 10)
        self.get_logger().info(
            'odom_cov_node: %s -> %s (covarianza xy=%.3f, yaw=%.3f)'
            % (inp, out, self.xy, self.yaw))

    def _cov(self):
        c = [0.0] * 36
        c[0] = self.xy      # x
        c[7] = self.xy      # y
        c[14] = self.BIG    # z
        c[21] = self.BIG    # roll
        c[28] = self.BIG    # pitch
        c[35] = self.yaw    # yaw
        return c

    def callback(self, msg):
        msg.pose.covariance = self._cov()
        msg.twist.covariance = self._cov()
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = OdomCov()
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
