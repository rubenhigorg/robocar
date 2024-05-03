import rclpy
from rclpy.node import Node
from messages_pkg.msg import Energy
from lib import SDL_Pi_INA3221
from lib import INA226Lib

class EnergyNode(Node):

    def __init__(self):
        super().__init__('energy_node')
        self.publisher_ = self.create_publisher(Energy, 'energy', 10)
        self.ina3221 = SDL_Pi_INA3221.SDL_Pi_INA3221()
        self.ina226 = INA226Lib.INA226(busnum=1, max_expected_amps=25)
        self.ina226.configure()
        timer_period = 1  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        msg = Energy()

        msg.voltage_battery_1 = round(self.ina3221.getBusVoltage_V(1), 2)
        msg.voltage_battery_2 = round(self.ina3221.getBusVoltage_V(2), 2)
        msg.voltage_battery_3 = round(self.ina3221.getBusVoltage_V(3), 2)
        msg.current = round(self.read_current(), 2)

        self.get_logger().info('Battery 1: "%s"' % msg.voltage_battery_1)
        self.get_logger().info('Battery 2: "%s"' % msg.voltage_battery_2)
        self.get_logger().info('Battery 3: "%s"' % msg.voltage_battery_3)
        self.get_logger().info('Current: "%s"' % msg.current)

        self.publisher_.publish(msg)
        self.get_logger().info('Published')

    def read_current(self):
        while not self.ina226.is_conversion_ready():
            self.get_logger().info('Waiting for conversion ready')
        return float (self.ina226.current())    
def main(args=None):
    rclpy.init(args=args)
    energy_node = EnergyNode()
    rclpy.spin(energy_node)
    energy_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()