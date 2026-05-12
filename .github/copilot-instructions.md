# Copilot Instructions

## Project Overview

This is a ROS2 (Iron) robotics project running on a Raspberry Pi. It controls an autonomous/manual RC car with lane-following capabilities, ultrasonic distance sensors, an IMU, energy monitoring, and a camera for computer vision. Node-RED provides a dashboard UI.

## Architecture

### ROS2 Nodes (Python, in `src/robocar_pkg/robocar_pkg/`)

- **car_control_node** – Main motor/steering controller. Subscribes to joystick (`/joy`) for manual mode and lane detection (`/lane_info`) for autonomous mode. Drives servos via Adafruit ServoKit (PCA9685, 16-channel).
- **camera_node** – Captures frames from `/dev/video0` at ~3 FPS (640×480) and publishes to `/camera_image`.
- **processing_node** – Receives camera images, detects lane lines using OpenCV, applies Kalman filtering, computes PID-based steering error, and publishes to `/lane_info`.
- **distance_node** – Reads 3 HC-SR04 ultrasonic sensors (left/center/right) via GPIO, publishes to `/ultrasound_data` at 10 Hz.
- **energy_node** – Reads battery voltages (INA3221) and current (INA226) over I2C, publishes custom `Energy` message.
- **accelerometer_node** – Reads MPU6050 IMU data, publishes standard `Imu` messages.

### Custom Messages (`src/messages_pkg/msg/`)

- `Distance.msg` – left_distance, right_distance, center_distance, emergency_stop
- `Energy.msg` – voltage_battery_1/2/3, current

### Node-RED Integration

`flows.json` contains the Node-RED dashboard flows (battery, movement, distances, camera, RPi monitoring). Launched via `nodered.sh` with ROS2 bridge using `rclnodejs`.

### Hardware Libraries (`src/robocar_pkg/lib/`)

Custom drivers for INA3221, INA226, MPU6050, plus OpenCV-based lane detection (processor, line, tracker, edge_detection).

## ROS2 Topics

| Topic | Type | Publisher | Description |
|-------|------|-----------|-------------|
| `/joy` | `sensor_msgs/Joy` | teleop_twist_joy | Joystick input (PS3 controller) |
| `/camera_image` | `sensor_msgs/Image` | camera_node | Raw camera frames (640×480 BGR) |
| `/lane_info` | `std_msgs/Float32MultiArray` | processing_node | Lane error for steering correction |
| `/ultrasound_data` | `messages_pkg/Distance` | distance_node | 3 ultrasonic distances + emergency stop |
| `/energy` | `messages_pkg/Energy` | energy_node | Battery voltages and current |
| `/imu` | `sensor_msgs/Imu` | accelerometer_node | Accelerometer + gyroscope data |

## Driving Modes

The car has two modes toggled by pressing button X (index 0) on the PS3 controller:

- **Manual**: Joystick axes control steering and throttle directly.
- **Autonomous**: `processing_node` detects lanes via camera and publishes steering corrections to `/lane_info`, which `car_control_node` applies automatically.

## Build & Run

```bash
# Setup ROS2 environment
source /opt/ros/iron/setup.bash

# Build all ROS2 packages (from src/)
cd src
colcon build
source install/setup.sh

# Python virtualenv (for hardware libraries)
source .venv/bin/activate

# Run a single node
ros2 run robocar_pkg car_control_node

# Run all nodes (production)
bash launch.sh

# Launch Node-RED dashboard
bash nodered.sh
```

## Tests

```bash
# Run all tests for robocar_pkg
colcon test --packages-select robocar_pkg
colcon test-result --verbose

# Run a specific test file with pytest
cd src/robocar_pkg
python -m pytest test/test_flake8.py
```

## Lint

The project uses ament linters (flake8, pep257, copyright check):

```bash
ament_flake8 src/robocar_pkg
ament_pep257 src/robocar_pkg
```

## Key Conventions

- **Language**: Code comments and variable names mix Spanish and English. Follow the existing style of whichever file you're editing.
- **Node pattern**: Each ROS2 node follows the same structure: class inheriting `rclpy.node.Node`, publishers/subscribers in `__init__`, timer or subscription callbacks, standalone `main()` function.
- **Entry points**: New nodes must be registered in `src/robocar_pkg/setup.py` under `console_scripts`.
- **Custom messages**: Defined in `src/messages_pkg/msg/`. After adding/modifying, rebuild with `colcon build` and regenerate Node-RED messages if needed.
- **Servo mapping**: Servo channels are 0/1 (motors) and 2 (steering). Values are mapped from sensor ranges to servo angle ranges (40–170° for steering, ~90° neutral for motors).
- **Hardware access**: Nodes use I2C (`smbus2`), GPIO (`RPi.GPIO`), and PCA9685 (`adafruit-circuitpython-servokit`). Code must run on Raspberry Pi with physical peripherals connected.
