
# MQTT Gateway Interface Specification

## 1. Overview

Python MQTT Gateway를 통해 MQTT JSON 메시지와
ROS2 Twist 메시지를 양방향으로 변환한다.

본 문서는 현재 구현된 통신 인터페이스와 검증 규칙을 정의한다.

## 2. Communication Architecture

MQTT Broker (Mosquitto)
    ↕ JSON / QoS 1
Python MQTT Gateway (rclpy + paho-mqtt)
    ↕ ROS2 Topics
C++ Robot Control Node

Python Gateway는 MQTT 명령을 ROS2에 전달하고,
C++ 제어 노드의 안전 속도 명령을 MQTT로 다시 발행한다.

## 3. MQTT Topics

### robot/commands/velocity

- Direction: MQTT → ROS2
- ROS2 topic: /robot/cmd_vel
- ROS2 type: geometry_msgs/msg/Twist
- MQTT QoS: 1

### robot/events/safe_velocity

- Direction: ROS2 → MQTT
- ROS2 topic: /robot/safe_cmd_vel
- ROS2 type: geometry_msgs/msg/Twist
- MQTT QoS: 1
- Retain: false

## 4. Incoming JSON Schema

```json
{
  "schema_version": "1.0",
  "command_id": "cmd-001",
  "timestamp": "2026-10-15T08:56:29Z",
  "linear_x": 0.5,
  "angular_z": 0.2
}
```

Fields:

- schema_version: 지원하는 스키마 버전 ("1.0")
- command_id: 비어 있지 않은 문자열 식별자
- timestamp: UTC ISO 8601 문자열 (Z로 종료)
- linear_x: 유한한 숫자, m/s
- angular_z: 유한한 숫자, rad/s

## 5. Outgoing JSON Schema

```json
{
  "schema_version": "1.0",
  "event_type": "safe_velocity_command",
  "timestamp": "2026-10-15T08:56:29.071Z",
  "linear_x": 1.0,
  "angular_z": 0.5
}
```

출력값은 C++ 제어 노드가 계산한 안전 속도 명령이며,
실제 로봇에서 측정한 속도나 명령 실행 완료를 의미하지 않는다.

## 6. Implemented Validation

Python Gateway에서 다음 항목을 검증한다.

- JSON 형식 및 객체 구조
- schema_version
- command_id 유효성
- 필수 속도 필드 및 숫자 자료형
- NaN 및 Infinity 거부
- UTC Timestamp 형식
- 2초를 초과한 오래된 명령 거부
- 1초를 초과해 미래로 설정된 명령 거부
- 최근 command_id 중복 명령 차단

중복 명령 검사는 최근 10초 동안 허용된 명령 ID를
기준으로 수행하며, 저장 개수는 최대 1,000개로 제한한다.

검증을 통과한 명령은 ROS2 Twist로 변환하여
/robot/cmd_vel 토픽에 발행한다.

C++ 제어 노드는 별도로 다음 기능을 수행한다.

- linear.x: -1.0 ~ 1.0 m/s 제한
- angular.z: -1.5 ~ 1.5 rad/s 제한
- 비정상 속도 입력에 대한 정지 처리
- 약 1초간 명령이 없을 경우 Timeout 정지

## 7. Communication Settings

- MQTT Broker: Mosquitto
- MQTT Client: paho-mqtt
- ROS2 Client: rclpy
- MQTT QoS: 1
- Outgoing retained messages: false
- Incoming message queue maximum: 100
- MQTT queue processing interval: 100ms
- Maximum processed messages per timer callback: 10

MQTT QoS 1은 메시지 중복 전달 가능성이 있으므로
command_id를 통한 중복 차단 기능을 적용한다.

MQTT 클라이언트는 자동 재연결 기능을 사용한다.

## 8. Verified Behavior

다음 동작을 실제 통합 테스트에서 확인했다.

- MQTT 명령을 ROS2 Twist로 변환
- C++ 제어 노드의 속도 제한
- ROS2 안전 속도 명령을 MQTT JSON으로 발행
- 약 1초 Timeout 후 정지 명령 발행
- 오래된 명령 및 미래 Timestamp 차단
- 동일 command_id 중복 명령 차단
- 새로운 command_id의 정상 처리
- MQTT Broker 중단 및 복구 후 명령 수신 재개

### Integration Test Example

MQTT input:
- linear_x: 2.0
- angular_z: 0.5

MQTT safe velocity event:
- linear_x: 1.0
- angular_z: 0.5

Timeout event:
- linear_x: 0.0
- angular_z: 0.0

2026-10-15 통합 테스트에서 위 결과를 확인했다.

## 9. Limitations

- ROS2 Twist에는 command_id와 timestamp가 포함되지 않는다.
- 중복 명령 기록은 Gateway 프로세스 메모리에만 보관된다.
- Gateway 재시작 시 중복 명령 기록은 초기화된다.
- MQTT 발행 요청 성공이 최종 수신자의 처리 완료를 보장하지 않는다.
- 출력된 안전 속도 명령은 실제 로봇의 측정 상태가 아니다.
- 실제 로봇 하드웨어에서 안전성을 검증하지 않았다.
- PostgreSQL 기반 영구 로그 저장은 아직 구현하지 않았다.

## 10. Planned Extension

- PostgreSQL 기반 명령 처리 로그 저장
- 정상 및 거부 명령 이력 조회
- 데이터베이스 장애 상황에서의 동작 검증