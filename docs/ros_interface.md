
# ROS2 Robot Gateway — Interface Specification

## 1. Overview

ROS2 C++ 로봇 제어 노드와 향후 Python MQTT Gateway 사이의
메시지 구조 및 데이터 처리 규칙을 정의한다.

## 2. ROS2 Topics

### /robot/cmd_vel
- Type: geometry_msgs/msg/Twist
- Direction: Gateway → RobotControlNode
- Purpose: 로봇 이동 명령 전달

### /robot/safe_cmd_vel
- Type: geometry_msgs/msg/Twist
- Direction: RobotControlNode → Robot/Simulator
- Purpose: 검증 및 속도 제한이 적용된 이동 명령 전달

## 3. Command Fields

| Field | Type | Unit | Description |
|---|---|---|---|
| linear.x | float64 | m/s | 전진 및 후진 속도 |
| angular.z | float64 | rad/s | 회전 속도 |

현재 제어 노드는 위 두 필드를 사용한다.
Twist의 나머지 축은 현재 출력에서 0으로 설정된다.

## 4. Current Validation Rules

- NaN 및 Infinity 입력 거부
- 유효하지 않은 입력 수신 시 속도 0 명령 발행
- linear.x: -1.0 ~ 1.0 m/s
- angular.z: -1.5 ~ 1.5 rad/s
- 최대 속도 초과 시 제한값으로 조정

## 5. Planned MQTT JSON Command

아래 JSON은 향후 구현할 인터페이스 초안이다.

```json
{
  "schema_version": "1.0",
  "command_id": "cmd-001",
  "timestamp": "2026-10-14T05:00:00Z",
  "linear_x": 0.5,
  "angular_z": 0.2
}
```

- schema_version: 데이터 형식 버전
- command_id: 명령 식별자
- timestamp: UTC 기준 명령 생성 시각
- linear_x: 직선 속도 (m/s)
- angular_z: 회전 속도 (rad/s)

## 6. Planned Gateway Responsibilities

- JSON 메시지 파싱 및 필드 타입 검증
- 필수 필드 누락 확인
- 단위와 허용 범위 검증
- command_id 기반 중복 명령 처리
- Timestamp 검사
- JSON 데이터를 ROS2 Twist로 변환
- ROS2 명령 처리 결과를 외부 시스템에 전달


## 7. Current Limitations

- MQTT Gateway 미구현
- 실제 로봇 상태 피드백 미구현
- safe_cmd_vel은 실제 로봇 속도가 아닌 제어 명령
- 메시지 ID와 timestamp는 현재 Twist 메시지에 포함되지 않음
- 실제 하드웨어에서의 비상 정지 기능은 검증하지 않음

## 8. Implemented Command Timeout

ROS2 C++ 제어 노드에 명령 수신 타임아웃 기능을 구현했다.

### Behavior

- 정상 명령 수신 시 마지막 수신 시각 갱신
- ROS2 Wall Timer로 100ms마다 타임아웃 검사
- 활성 이동 명령 이후 1초 이상 새 명령이 없으면 정지
- 타임아웃 발생 시 linear.x와 angular.z를 0으로 설정하여 발행
- NaN 또는 Infinity 입력 시 즉시 정지 명령 발행
- 정지 상태에서는 타임아웃 경고를 반복 발생시키지 않음

### Implementation

- Node: robot_control_node
- Language: C++17
- Timer interval: 100ms
- Command timeout: 1 second
- Time measurement: std::chrono::steady_clock
- Output topic: /robot/safe_cmd_vel

### Verification

- ROS2 명령 수신 및 출력 토픽 확인
- 단일 이동 명령 발행 후 약 1초 뒤 정지 명령 출력 확인
- 속도 제한 및 비정상 입력 처리 회귀 테스트 실행
- colcon build 및 colcon test 정상 완료

