# ROS2–MQTT Robot Integration Gateway

ROS2 기반 로봇과 외부 MQTT 시스템 사이에서 명령과 데이터를 주고받는 로봇 통합 게이트웨이 프로젝트입니다.

Python으로 MQTT 메시지 검증과 ROS2 연동을 구현하고, C++ 제어 노드에서 속도 제한과 명령 Timeout을 처리하도록 구성했습니다. 명령 처리 결과는 PostgreSQL에 비동기로 저장하며, Gazebo Harmonic 시뮬레이션을 통해 로봇의 이동과 정지 동작을 확인했습니다.

## 1. Project Overview

이 프로젝트는 서로 다른 통신 환경을 사용하는 로봇 시스템과 외부 서비스를 연결하고, 명령 전달 과정에서 발생할 수 있는 오류와 장애를 처리하는 것을 목표로 합니다.

주요 구현 기능은 다음과 같습니다.

- ROS2와 MQTT 간 양방향 통신
- MQTT JSON 메시지 검증 및 ROS2 Twist 메시지 변환
- C++ 기반 속도 제한 및 명령 Timeout 처리
- Timestamp 유효성 검사 및 command_id 중복 명령 차단
- MQTT Broker 연결 장애 이후 자동 재연결
- PostgreSQL 비동기 로그 저장 및 DB 장애 대응
- Gazebo Harmonic을 이용한 로봇 제어 검증
- C++ 단위 테스트, Python 자동화 검사 및 통합 통신 테스트

## 2. System Architecture

```text
External MQTT Client
        │
        ▼
Mosquitto MQTT Broker
        │  robot/commands/velocity
        ▼
Python MQTT Gateway ───────► DB Logger ───────► PostgreSQL
 - JSON validation               - Queue / Worker Thread
 - Timestamp validation          - Command processing logs
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
        ├───────────────────────► ROS2–Gazebo Integration
        │                         - Simulated robot control
        ▼
Python MQTT Gateway
        │  robot/events/safe_velocity
        ▼
Mosquitto MQTT Broker
        │
        ▼
External MQTT Client
```

외부 MQTT 클라이언트에서 전달한 속도 명령은 Python Gateway에서 JSON 형식, Timestamp, command_id를 검증한 뒤 ROS2 토픽으로 전달합니다.

C++ 제어 노드는 입력 속도에 제한을 적용하고, 새로운 명령이 일정 시간 들어오지 않으면 정지 명령을 발행합니다.

안전 처리된 속도 명령은 Python Gateway를 통해 MQTT 이벤트로 반환되며, PostgreSQL에는 명령의 수신 및 처리 결과가 기록됩니다.

이때 MQTT로 반환되는 값은 안전 처리된 속도 명령이며, 로봇이 실제로 측정한 속도나 명령 수행 완료 여부를 나타내지는 않습니다.

전체 시스템 구조와 모듈별 역할은 [아키텍처 문서](docs/architecture.md)에 정리했습니다.

## 3. Technology Stack

| Category | Technology |
|---|---|
| OS | Ubuntu 24.04 / WSL2 |
| Robotics Middleware | ROS2 Jazzy |
| Languages | C++17, Python |
| ROS2 Libraries | rclcpp, rclpy |
| Communication | MQTT, Mosquitto, paho-mqtt |
| Message Format | JSON, geometry_msgs/Twist |
| Database | PostgreSQL, psycopg2 |
| Simulation | Gazebo Harmonic |
| Build & Test | colcon, GTest, pytest |
| Version Control | Git, GitHub |

## 4. Project Structure

```text
ros2_robot_gateway/
├── db/
│   └── schema.sql
├── docs/
│   ├── architecture.md
│   ├── gazebo_integration.md
│   ├── mqtt_interface.md
│   ├── ros_interface.md
│   └── test_results.md
├── src/
│   ├── robot_controller_cpp/
│   │   ├── include/robot_controller_cpp/
│   │   │   └── robot_controller.hpp
│   │   ├── src/
│   │   │   ├── robot_control_node.cpp
│   │   │   └── robot_controller.cpp
│   │   └── test/
│   │       └── test_robot_controller.cpp
│   └── mqtt_gateway_py/
│       ├── mqtt_gateway_py/
│       │   ├── gateway_node.py
│       │   ├── mqtt_client.py
│       │   ├── message_converter.py
│       │   └── db_logger.py
│       └── test/
├── .gitignore
└── README.md
```

주요 구성 요소의 역할은 다음과 같습니다.

- `robot_controller_cpp`: 속도 제한, 입력값 검사, Timeout 처리
- `mqtt_gateway_py`: MQTT 메시지 수신, 검증, ROS2 연동 및 이벤트 발행
- `db_logger.py`: 명령 처리 결과를 비동기로 PostgreSQL에 저장
- `db/schema.sql`: 명령 기록 테이블 정의
- `docs/`: 인터페이스, 시스템 구조 및 검증 과정 문서

위 구조에는 주요 파일만 표시했습니다.

## 5. Communication Interfaces

### ROS2 Topics

| Topic | Type | Description |
|---|---|---|
| `/robot/cmd_vel` | `geometry_msgs/Twist` | 입력 속도 명령 |
| `/robot/safe_cmd_vel` | `geometry_msgs/Twist` | 안전 처리된 속도 명령 |

### MQTT Topics

| Topic | Direction | QoS |
|---|---|---|
| `robot/commands/velocity` | MQTT → ROS2 | 1 |
| `robot/events/safe_velocity` | ROS2 → MQTT | 1 |

MQTT QoS 1은 메시지를 최소 한 번 전달하는 방식이므로 동일한 메시지가 중복 수신될 수 있습니다. 이를 고려해 command_id를 기준으로 중복 명령을 검사하도록 구성했습니다.

인터페이스와 메시지 구조는 다음 문서에 정리했습니다.

- [ROS2 Interface](docs/ros_interface.md)
- [MQTT Interface](docs/mqtt_interface.md)
- [System Architecture](docs/architecture.md)

## 6. Build and Run

개발 및 검증 환경은 Ubuntu 24.04 / WSL2와 ROS2 Jazzy를 기준으로 합니다.

다른 환경에서 실행할 경우 ROS2 설치 상태, 사용자 권한, PostgreSQL 연결 설정 등에 따라 추가 구성이 필요할 수 있습니다.

### 6.1 Dependencies

ROS2 Jazzy, colcon, Mosquitto 및 C++ 빌드 환경이 설치되어 있어야 합니다.

PostgreSQL과 Python 의존성은 다음과 같이 설치할 수 있습니다.

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib \
  python3-psycopg2 python3-paho-mqtt
```

MQTT 명령 송수신을 위한 클라이언트 도구가 없다면 다음 명령으로 설치합니다.

```bash
sudo apt install -y mosquitto mosquitto-clients
```

Python Gateway를 실행하는 환경에서 `paho-mqtt`와 `psycopg2` 모듈을 사용할 수 있어야 합니다.

### 6.2 PostgreSQL Setup

PostgreSQL 서비스를 시작합니다.

```bash
sudo systemctl start postgresql
```

로컬 Ubuntu 사용자 이름을 기준으로 데이터베이스 계정과 프로젝트 DB를 생성합니다.

```bash
sudo -u postgres createuser --login --no-superuser \
  --no-createdb --no-createrole "$USER"

sudo -u postgres createdb --owner="$USER" robot_gateway_db
```

이미 사용자나 데이터베이스가 존재한다면 해당 생성 명령은 생략합니다.

테이블 구조를 적용합니다.

```bash
psql -d robot_gateway_db -f db/schema.sql
```

위 설정은 로컬 PostgreSQL 환경을 기준으로 하며, 다른 환경에서는 인증 방식과 접속 설정을 조정해야 할 수 있습니다.

### 6.3 Build

프로젝트 루트 디렉터리에서 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 6.4 Start MQTT Broker

```bash
sudo systemctl start mosquitto
systemctl is-active mosquitto
```

### 6.5 Run Python Gateway

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run mqtt_gateway_py gateway_node
```

### 6.6 Run C++ Robot Controller

다른 터미널에서 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run robot_controller_cpp robot_control_node
```

### 6.7 Subscribe to MQTT Events

```bash
mosquitto_sub -h 127.0.0.1 -p 1883 \
  -t robot/events/safe_velocity -q 1 -v
```

### 6.8 Publish a Test Command

새 터미널에서 실행합니다.

```bash
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ID="cmd-test-$(date +%s%N)"

mosquitto_pub -h 127.0.0.1 -p 1883 -q 1 \
  -t robot/commands/velocity \
  -m "{\"schema_version\":\"1.0\",\"command_id\":\"$ID\",\"timestamp\":\"$TS\",\"linear_x\":2.0,\"angular_z\":0.5}"
```

입력된 `linear_x = 2.0`은 C++ 제어 노드에서 `1.0`으로 제한됩니다.

이후 새로운 명령이 들어오지 않으면 약 1초 뒤 정지 명령이 발행됩니다.

Gazebo 시뮬레이션 실행 및 연동 과정은 [Gazebo 통합 문서](docs/gazebo_integration.md)에 정리했습니다.

## 7. Validation and Testing

2026-10-15 기준으로 MQTT–ROS2 양방향 통신, 명령 검증, 안전 제어 및 연결 장애 복구 동작을 확인했습니다.

### 7.1 Integration Tests

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
| 양방향 통합 통신 | Passed |

### 7.2 Safe Velocity Control

속도 제한과 Timeout 동작을 다음과 같이 확인했습니다.

MQTT 입력 명령의 주요 속도 필드:

```json
{
  "linear_x": 2.0,
  "angular_z": 0.5
}
```

C++ 제어 노드에서 처리한 속도 명령:

```json
{
  "linear_x": 1.0,
  "angular_z": 0.5
}
```

명령 수신 중단 이후 Timeout으로 발행한 정지 명령:

```json
{
  "linear_x": 0.0,
  "angular_z": 0.0
}
```

위 JSON은 검증 과정에서 사용한 메시지의 주요 속도 필드만 발췌한 것입니다.

### 7.3 Automated Tests

다음 명령으로 자동화 테스트를 실행할 수 있습니다.

```bash
colcon test
colcon test-result --verbose
```

기록된 자동화 테스트 결과:

| Result | Count |
|---|---:|
| Passed | 27 |
| Skipped | 5 |
| Failures | 0 |
| Errors | 0 |

C++ 제어 노드의 단위 테스트와 Python Gateway의 메시지 검증 및 자동화 검사를 수행했습니다.

Skipped 5건은 통과한 테스트에 포함하지 않았습니다. 위 수치는 당시 검증 결과이며, 실행 환경이나 의존성이 달라지면 결과가 달라질 수 있습니다.

세부 검증 내용은 [테스트 결과 문서](docs/test_results.md)에 정리했습니다.

### 7.4 Gazebo Harmonic Validation

Gazebo Harmonic 시뮬레이션에서 MQTT 명령에 따른 로봇의 이동과 정지 동작을 확인했습니다.

명령 전달 이후 로봇이 움직이는지 확인하고, 새로운 명령이 중단됐을 때 안전 정지 명령이 적용되는지도 검증했습니다.

실제 로봇 하드웨어가 아닌 Gazebo 예제 로봇을 사용했으며, 시뮬레이션의 자체 속도 및 가속도 제한도 결과에 영향을 줄 수 있습니다.

관련 실행 과정은 [Gazebo 통합 문서](docs/gazebo_integration.md)에 정리했습니다.

## 8. PostgreSQL Command Logging

MQTT 명령의 수신 및 검증 결과를 PostgreSQL에 저장하도록 구성했습니다.

DB 접근 과정이 로봇 제어를 직접 지연시키지 않도록 로그를 큐에 전달하고, 별도의 작업 스레드에서 저장을 수행합니다.

### 8.1 Recorded Information

| Column | Description |
|---|---|
| `command_id` | MQTT 명령 식별자 |
| `logged_at` | 로그 저장 시각 |
| `linear_x` | 입력 선속도 |
| `angular_z` | 입력 각속도 |
| `status` | ACCEPTED / DUPLICATE / REJECTED |
| `reason` | 거부 또는 처리 사유 |

### 8.2 Query Command Logs

저장된 명령 처리 결과는 다음 SQL로 확인할 수 있습니다.

```sql
SELECT
    id,
    logged_at,
    command_id,
    linear_x,
    angular_z,
    status,
    reason
FROM command_logs
ORDER BY id DESC
LIMIT 10;
```

### 8.3 Database Fault Handling

PostgreSQL 서비스를 중단한 상태에서도 MQTT–ROS2 명령 처리 흐름이 유지되는지 확인했습니다.

DB가 중단된 동안 저장할 수 없는 로그가 발생할 수 있지만, DB 응답을 기다리느라 제어 흐름이 차단되지 않도록 구성했습니다.

이후 PostgreSQL 서비스를 복구했을 때 새로운 명령의 로그 저장이 재개되는 것도 검증했습니다.

확인한 동작은 다음과 같습니다.

- 정상 명령의 ACCEPTED 기록
- 중복 명령의 DUPLICATE 기록
- 오래된 명령의 REJECTED 기록
- DB 장애 중 MQTT–ROS2 명령 처리 유지
- DB 복구 후 새로운 로그 저장 재개

로그 큐의 최대 크기는 100개이며, DB 장애 중 발생한 로그의 완전한 보존이나 복구를 보장하지는 않습니다.

## 9. Limitations

현재 구현 및 검증 범위에는 다음과 같은 제한이 있습니다.

- 실제 로봇 하드웨어가 아닌 Gazebo 시뮬레이션 환경에서 검증했습니다.
- `/robot/safe_cmd_vel`과 MQTT safe_velocity 이벤트는 실제 측정 속도가 아닌 안전 처리된 속도 명령입니다.
- ROS2 Twist 메시지에는 MQTT command_id가 함께 전달되지 않습니다.
- 중복 명령 검사 기록은 메모리에 저장되므로 Gateway를 재시작하면 초기화됩니다.
- MQTT 이벤트 발행이나 DB 기록 성공이 실제 로봇의 명령 수행 완료를 의미하지 않습니다.
- DB 장애 중 일부 로그가 유실될 수 있으며, 로그 큐의 최대 크기는 100개입니다.
- PostgreSQL 연결과 실행 설정은 로컬 개발 환경을 기준으로 검증했습니다.
