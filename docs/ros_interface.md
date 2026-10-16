
# ROS2 Robot Gateway — Interface Specification

## 1. Overview

ROS2 C++ Robot Control Node와 Python MQTT Gateway 사이의
메시지 구조 및 데이터 처리 규칙을 정의한다.

현재 ROS2–MQTT 양방향 통신과 기본 안전 제어 기능이 구현되어 있다.

## 2. ROS2 Topics

### /robot/cmd_vel

- Type: geometry_msgs/msg/Twist
- Publisher: Python MQTT Gateway
- Subscriber: C++ Robot Control Node
- Purpose: MQTT에서 수신한 로봇 이동 명령 전달

### /robot/safe_cmd_vel

- Type: geometry_msgs/msg/Twist
- Publisher: C++ Robot Control Node
- Subscriber: Python MQTT Gateway
- Purpose: 속도 제한과 안전 처리가 적용된 명령 전달

Python Gateway는 /robot/safe_cmd_vel 메시지를
MQTT의 robot/events/safe_velocity 토픽으로 발행한다.

## 3. Command Fields

| Field | Type | Unit | Description |
|---|---|---|---|
| linear.x | float64 | m/s | 전진 및 후진 속도 |
| angular.z | float64 | rad/s | 회전 속도 |

현재 제어 노드는 위 두 필드를 사용한다.
출력되는 Twist 메시지의 나머지 축은 0으로 설정된다.

## 4. C++ Safety Validation

C++ Robot Control Node는 다음 기능을 수행한다.

- linear.x: -1.0 ~ 1.0 m/s 제한
- angular.z: -1.5 ~ 1.5 rad/s 제한
- NaN 및 Infinity 입력 시 정지 명령 발행
- 허용 범위를 초과하는 속도는 제한값으로 조정
- 명령 수신 Timeout 처리

### Example

Input:
- linear.x: 2.0
- angular.z: 0.5

Output:
- linear.x: 1.0
- angular.z: 0.5

## 5. Command Timeout

이동 명령을 수신한 뒤 일정 시간 동안
새로운 명령이 없으면 정지 명령을 발행한다.

### Implementation

- Node: robot_control_node
- Language: C++17
- Timer interval: 100ms
- Command timeout: 1 second
- Time measurement: std::chrono::steady_clock
- Output topic: /robot/safe_cmd_vel

### Behavior

- 명령 수신 시 마지막 수신 시각 갱신
- 활성 이동 명령 이후 약 1초 동안 명령이 없으면 정지
- 정지 명령은 linear.x = 0, angular.z = 0
- 이미 정지한 상태에서는 Timeout 경고 반복 방지

## 6. Python Gateway Responsibilities

Python MQTT Gateway는 다음 기능을 수행한다.

- MQTT JSON 메시지 수신
- JSON 구조 및 필수 필드 검증
- UTC Timestamp 유효성 검사
- command_id 기반 중복 명령 차단
- 유효한 명령을 ROS2 Twist로 변환
- /robot/cmd_vel 토픽 발행
- /robot/safe_cmd_vel 토픽 구독
- 안전 속도 명령을 MQTT JSON으로 변환 및 발행

속도 제한 및 Timeout 처리는 C++ 제어 노드에서 수행한다.

MQTT 메시지 검증 규칙의 상세 내용은
docs/mqtt_interface.md를 참조한다.

## 7. Integration Verification

2026-10-15 전체 통합 테스트에서 다음 경로를 검증했다.

MQTT Broker
→ Python Gateway
→ /robot/cmd_vel
→ C++ Robot Control Node
→ /robot/safe_cmd_vel
→ Python Gateway
→ MQTT Broker

### Test Results

- MQTT 입력 속도: 2.0 / 0.5
- C++ 제한 후 출력: 1.0 / 0.5
- 약 1초 후 Timeout 출력: 0.0 / 0.0
- 두 결과 모두 MQTT 응답 토픽에서 수신 확인

C++ 제어 노드의 단위 테스트와
Python Gateway의 자동화 테스트도 실행했다.

## 8. Current Limitations

- ROS2 Twist에는 command_id와 timestamp가 포함되지 않는다.
- /robot/safe_cmd_vel은 안전 처리된 제어 명령이지 실제 측정 속도가 아니다.
- 실제 로봇 하드웨어에 대한 연결 및 안전성 검증은 수행하지 않았다.
- 실제 로봇 상태 피드백은 구현하지 않았다.
- PostgreSQL 기반 명령 기록 저장은 아직 구현하지 않았다.