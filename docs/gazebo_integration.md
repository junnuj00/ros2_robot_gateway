# Gazebo Harmonic Integration

## Overview

This project was integrated with Gazebo Harmonic to demonstrate
MQTT-based control of a simulated differential-drive robot.

The integration uses the existing Python MQTT Gateway and
C++ Robot Controller without modifying their control logic.

## Environment

- Ubuntu 24.04 / WSL2
- ROS2 Jazzy
- Gazebo Harmonic 8.15.0
- ros_gz_bridge
- Mosquitto MQTT Broker
- PostgreSQL

## System Flow

MQTT Command
→ Python MQTT Gateway
→ ROS2 /robot/cmd_vel
→ C++ Robot Controller
→ ROS2 /robot/safe_cmd_vel
→ ros_gz_bridge
→ Gazebo vehicle_blue

The MQTT Gateway also records command-processing results
asynchronously in PostgreSQL.

## 1. Launch Gazebo

```bash
source /opt/ros/jazzy/setup.bash
gz sim -r diff_drive.sdf
```

The example world contains two differential-drive vehicles:
vehicle_blue and vehicle_green.

Only vehicle_blue is controlled in this integration test.

## 2. Launch ROS2–Gazebo Bridge

```bash
source /opt/ros/jazzy/setup.bash

ros2 run ros_gz_bridge parameter_bridge \
  '/model/vehicle_blue/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist' \
  --ros-args \
  -r '/model/vehicle_blue/cmd_vel:=/robot/safe_cmd_vel'
```

This bridge forwards ROS2 safe velocity commands to
Gazebo's vehicle_blue command topic.

## 3. Launch C++ Robot Controller

```bash
cd ~/ros2_robot_gateway
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run robot_controller_cpp robot_control_node
```

The controller limits velocity commands and publishes a
stop command after approximately one second without input.

## 4. Launch Python MQTT Gateway

```bash
cd ~/ros2_robot_gateway
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run mqtt_gateway_py gateway_node
```

## 5. Send MQTT Commands

Run the following in an additional terminal while the
four components above are running.

```bash
for i in {1..10}; do
    TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    ID="gazebo-demo-$(date +%s%N)"

    mosquitto_pub -h 127.0.0.1 -p 1883 -q 1 \
      -t robot/commands/velocity \
      -m "{\"schema_version\":\"1.0\",\"command_id\":\"$ID\",\"timestamp\":\"$TS\",\"linear_x\":2.0,\"angular_z\":0.4}"

    sleep 0.4
done
```

## 6. Verified Results

- MQTT commands were received and accepted by the Gateway.
- The C++ Controller applied its configured velocity limits.
- ROS2–Gazebo Bridge forwarded safe velocity commands.
- The blue simulated robot moved in Gazebo.
- The robot stopped after command transmission ended.
- All 10 test commands were logged as ACCEPTED in PostgreSQL.

Database verification:

```sql
SELECT status, COUNT(*) AS command_count
FROM command_logs
WHERE command_id LIKE 'gazebo-demo-%'
GROUP BY status;
```

Observed result:

| Status | Command Count |
|---|---:|
| ACCEPTED | 10 |

## Limitations

- Testing was performed in simulation, not on physical hardware.
- The Gazebo example robot has additional built-in velocity limits.
- Simulated movement was confirmed visually, without quantitative
  trajectory accuracy measurements.
- The safe velocity event represents a commanded velocity,
  not actual measured robot velocity.