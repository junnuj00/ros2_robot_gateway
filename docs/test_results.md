# Test Results

## ROS2–MQTT Robot Integration Gateway

Test date: 2026-10-16

## 1. Test Environment

- OS: Ubuntu 24.04 (WSL2)
- ROS2: Jazzy
- Robot Controller: C++ / rclcpp
- MQTT Gateway: Python / rclpy
- MQTT Broker: Mosquitto
- Database: PostgreSQL

## 2. Automated Tests

Command:

```bash
colcon test --packages-select robot_controller_cpp mqtt_gateway_py
colcon test-result --verbose
```

Results:

| Metric | Result |
|---|---|
| Packages | 2 |
| Total tests | 32 |
| Passed | 27 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 5 |

Both packages completed without test failures or errors.

## 3. MQTT–ROS2 Integration Test

A velocity command was sent through MQTT.

Input:

- linear_x: 2.0
- angular_z: 0.5

Observed output:

| Stage | linear_x | angular_z |
|---|---:|---:|
| MQTT input | 2.0 | 0.5 |
| Safe velocity output | 1.0 | 0.5 |
| Timeout stop | 0.0 | 0.0 |

The C++ controller limited linear velocity to 1.0.
After approximately one second without a new command,
the controller published a stop command.

## 4. Command Validation and Database Logging

The following results were verified in the
PostgreSQL `command_logs` table.

| Case | Status | Reason |
|---|---|---|
| Valid command | ACCEPTED | - |
| First command with duplicate test ID | ACCEPTED | - |
| Repeated command ID | DUPLICATE | Duplicate command |
| Command with timestamp 10 seconds old | REJECTED | Stale MQTT command |

The stale command was rejected without storing
linear or angular velocity values.

## 5. Verified Behaviors

- MQTT command reception and JSON processing
- MQTT-to-ROS2 velocity command forwarding
- C++ velocity limiting
- Timeout-based stop command
- ROS2-to-MQTT safe velocity event publishing
- Duplicate command detection
- Stale timestamp rejection
- Asynchronous PostgreSQL command logging

## 6. Notes and Limitations

- The safe velocity event represents the controller's
  output command, not measured robot motion.
- Testing was performed without physical robot hardware.
- Five automated tests were skipped.
- Database logging is asynchronous and does not provide
  durable storage guarantees during prolonged outages.