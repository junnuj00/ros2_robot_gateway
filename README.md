
# ROS2–MQTT Robot Integration Gateway

ROS2와 MQTT 간 양방향 통신을 구현한 로봇 데이터 통합 게이트웨이 프로젝트입니다.

C++ 기반 ROS2 제어 노드와 Python MQTT Gateway를 연결하여 외부 명령을 검증하고, 안전 속도 명령을 다시 MQTT로 전달합니다.

## 1. Project Overview

본 프로젝트는 ROS2 기반 로봇 시스템과 외부 MQTT 시스템 사이의 데이터 교환을 목적으로 합니다.

주요 기능은 다음과 같습니다.

- ROS2 ↔ MQTT 양방향 통신
- MQTT JSON 메시지 검증 및 ROS2 Twist 변환
- C++ 기반 속도 제한 및 명령 Timeout 처리
- Timestamp 유효성 검증
- command_id 기반 중복 명령 차단
- MQTT 연결 장애 이후 자동 재연결
- 통합 테스트를 통한 통신 흐름 검증

## 2. System Architecture

```text
External MQTT Client
        │
        ▼
Mosquitto MQTT Broker
        │
        ▼
Python MQTT Gateway
  - JSON validation
  - Timestamp validation
  - Duplicate detection
        │
        ▼
ROS2 /robot/cmd_vel
        │
        ▼
C++ Robot Control Node
  - Velocity limits
  - Invalid value handling
  - Command timeout
        │
        ▼
ROS2 /robot/safe_cmd_vel
        │
        ▼
Python MQTT Gateway
        │
        ▼
MQTT robot/events/safe_velocity
```

MQTT 명령은 Python Gateway에서 검증한 뒤 ROS2로 전달됩니다.

C++ 제어 노드는 속도 제한과 Timeout 처리를 수행하고, 처리된 안전 속도 명령을 ROS2 토픽에 발행합니다.

Python Gateway는 해당 명령을 MQTT JSON 이벤트로 변환합니다.

## 3. Technology Stack

| Category | Technology |
|---|---|
| OS | Ubuntu 24.04 / WSL2 |
| Robotics Middleware | ROS2 Jazzy |
| Languages | C++17, Python |
| ROS2 Libraries | rclcpp, rclpy |
| Communication | MQTT, Mosquitto |
| MQTT Client | paho-mqtt |
| Message Format | JSON, geometry_msgs/Twist |
| Build & Test | colcon, GTest, pytest |
| Version Control | Git, GitHub |

## 4. Project Structure

```text
ros2_robot_gateway/
├── docs/
│   ├── ros_interface.md
│   └── mqtt_interface.md
├── src/
│   ├── robot_controller_cpp/
│   │   ├── include/
│   │   ├── src/
│   │   └── test/
│   └── mqtt_gateway_py/
│       ├── mqtt_gateway_py/
│       │   ├── gateway_node.py
│       │   ├── mqtt_client.py
│       │   └── message_converter.py
│       └── test/
├── .gitignore
└── README.md
```

## 5. Communication Interfaces

### ROS2 Topics

| Topic | Type | Description |
|---|---|---|
| /robot/cmd_vel | geometry_msgs/Twist | 입력 속도 명령 |
| /robot/safe_cmd_vel | geometry_msgs/Twist | 안전 처리된 속도 명령 |

### MQTT Topics

| Topic | Direction | QoS |
|---|---|---|
| robot/commands/velocity | MQTT → ROS2 | 1 |
| robot/events/safe_velocity | ROS2 → MQTT | 1 |

자세한 데이터 구조와 검증 규칙은 다음 문서를 참조합니다.

- [ROS2 Interface](docs/ros_interface.md)
- [MQTT Interface](docs/mqtt_interface.md)

## 6. Build and Run

ROS2 Jazzy, colcon, Mosquitto 및 프로젝트에 필요한 Python 의존성이 설치된 Ubuntu 24.04 환경을 기준으로 합니다.

### Build

프로젝트 루트 디렉터리에서 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### Start MQTT Broker

```bash
sudo systemctl start mosquitto
systemctl is-active mosquitto
```

### Run Python Gateway

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run mqtt_gateway_py gateway_node
```

### Run C++ Robot Controller

다른 터미널에서 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run robot_controller_cpp robot_control_node
```

### Subscribe to MQTT Events

```bash
mosquitto_sub -h 127.0.0.1 -p 1883 \
  -t robot/events/safe_velocity -q 1 -v
```

### Publish a Test Command

새 터미널에서 실행합니다.

```bash
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ID="cmd-test-$(date +%s%N)"

mosquitto_pub -h 127.0.0.1 -p 1883 -q 1 \
  -t robot/commands/velocity \
  -m "{\"schema_version\":\"1.0\",\"command_id\":\"$ID\",\"timestamp\":\"$TS\",\"linear_x\":2.0,\"angular_z\":0.5}"
```

입력값 `linear_x = 2.0`은 C++ 제어 노드에서 `1.0`으로 제한됩니다.

이후 새로운 명령이 없으면 약 1초 뒤 정지 명령이 발행됩니다.

## 7. Validation and Testing

2026-10-15에 다음 항목을 검증했습니다.

| Test | Result |
|---|---|
| MQTT → ROS2 명령 전달 | Passed |
| ROS2 → MQTT 이벤트 발행 | Passed |
| C++ 속도 제한 | Passed |
| Command Timeout | Passed |
| 오래된 MQTT 명령 차단 | Passed |
| 미래 Timestamp 명령 차단 | Passed |
| 중복 command_id 차단 | Passed |
| 신규 command_id 허용 | Passed |
| Broker 재연결 후 명령 수신 | Passed |
| 전체 양방향 통합 통신 | Passed |

### Integration Test Result

MQTT Input:

```json
{
  "linear_x": 2.0,
  "angular_z": 0.5
}
```

Safe Velocity Output:

```json
{
  "linear_x": 1.0,
  "angular_z": 0.5
}
```

Timeout Output:

```json
{
  "linear_x": 0.0,
  "angular_z": 0.0
}
```

위 JSON은 주요 속도 필드만 발췌한 결과입니다.

### Automated Tests

```bash
colcon test
colcon test-result --verbose
```

C++ 제어 노드의 단위 테스트와 Python 패키지의 자동화 검사를 수행했습니다.

## 8. Limitations

- 실제 로봇 하드웨어에서 테스트하지 않았습니다.
- 안전 속도 명령은 실제 측정된 로봇 속도가 아닙니다.
- ROS2 Twist 메시지에는 MQTT command_id가 전달되지 않습니다.
- 중복 명령 기록은 메모리에 보관되어 Gateway 재시작 시 초기화됩니다.
- MQTT 이벤트 발행 요청 성공이 실제 로봇의 명령 수행 완료를 의미하지는 않습니다.

## 9. Planned Work

- PostgreSQL 기반 명령 처리 로그 저장
- 정상 및 거부 명령 이력 조회
- 데이터베이스 연결 장애 검증
- 최종 테스트 및 실행 문서 보완
