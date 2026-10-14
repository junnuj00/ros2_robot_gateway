
# MQTT Gateway Interface Design

## 1. Purpose

Python Gateway를 통해 MQTT JSON 메시지와
ROS2 Twist 메시지를 양방향으로 변환한다.

현재 문서는 구현 전 설계 초안이다.

## 2. Communication Architecture

MQTT Broker
    ↕ JSON
Python MQTT Gateway
    ↕ ROS2 Topics
C++ RobotControlNode
    ↓
Robot / Simulator

## 3. MQTT Topics

### robot/commands/velocity
- Direction: MQTT → ROS2
- ROS2 topic: /robot/cmd_vel
- ROS2 type: geometry_msgs/msg/Twist

### robot/events/safe_velocity
- Direction: ROS2 → MQTT
- ROS2 topic: /robot/safe_cmd_vel
- ROS2 type: geometry_msgs/msg/Twist

## 4. Incoming JSON Schema

{
  "schema_version": "1.0",
  "command_id": "cmd-001",
  "timestamp": "2026-10-14T06:00:00Z",
  "linear_x": 0.5,
  "angular_z": 0.2
}

Field definitions:
- schema_version: string
- command_id: string
- timestamp: ISO 8601 UTC string
- linear_x: finite number, m/s
- angular_z: finite number, rad/s

## 5. Outgoing JSON Schema

{
  "schema_version": "1.0",
  "event_type": "safe_velocity_command",
  "timestamp": "2026-10-14T06:00:01Z",
  "linear_x": 0.5,
  "angular_z": 0.2
}

Output represents a safe velocity command,
not measured robot velocity.

## 6. MVP Validation

- JSON 형식 확인
- 필수 필드 및 자료형 확인
- NaN / Infinity 거부
- schema_version 확인
- Twist 메시지 변환
- C++ 노드에서 속도 제한 및 Timeout 처리

## 7. Planned Communication Settings

- MQTT QoS: 1
- Retained messages: false
- Broker: Mosquitto
- Python libraries: rclpy, paho-mqtt

QoS 1은 중복 전달 가능성이 있으므로,
향후 command_id 기반 중복 처리 로직을 검토한다.

## 8. Planned Extensions

- 명령 ID 중복 검사
- 오래된 timestamp 검사
- MQTT 연결 끊김 및 재연결 처리
- 명령 및 오류 로그 저장
- PostgreSQL 연동
- 실제 로봇 상태 피드백

## 9. Limitations

- MQTT 연동은 아직 구현되지 않음
- ROS2 Twist에는 command_id와 timestamp가 없음
- 현재 출력은 실제 로봇 상태가 아님
- MQTT QoS와 ROS2 QoS는 서로 별도로 설정해야 함