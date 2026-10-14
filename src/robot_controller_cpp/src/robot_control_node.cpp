#include <chrono>
#include <memory>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"
#include "robot_controller_cpp/robot_controller.hpp"

namespace robot_controller_cpp
{

class RobotControlNode : public rclcpp::Node
{
public:
  RobotControlNode()
  : Node("robot_control_node")
  {
    // 검증된 이동 명령 발행
    safe_publisher_ =
      this->create_publisher<geometry_msgs::msg::Twist>(
      "/robot/safe_cmd_vel", 10);

    // 외부 이동 명령 수신
    command_subscriber_ =
      this->create_subscription<geometry_msgs::msg::Twist>(
      "/robot/cmd_vel",
      10,
      [this](geometry_msgs::msg::Twist::SharedPtr msg) {
        handleCommand(msg);
      });

    // 100ms 간격으로 명령 수신 타임아웃 확인
    timeout_timer_ = this->create_wall_timer(
      std::chrono::milliseconds(100),
      [this]() {
        checkCommandTimeout();
      });

    RCLCPP_INFO(
      this->get_logger(),
      "Robot Control Node started. Timeout: 1.0 second.");
  }

private:
  // 이동 명령 수신 및 검증
  void handleCommand(
    const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    const bool accepted = controller_.setCommand(
      msg->linear.x,
      msg->angular.z);

    const auto command = controller_.getCommand();

    // NaN 또는 Infinity 입력 시 즉시 정지
    if (!accepted) {
      has_active_command_ = false;
      publishSafeCommand(command);

      RCLCPP_WARN(
        this->get_logger(),
        "Invalid command received. Robot stopped.");
      return;
    }

    // 정상 명령의 마지막 수신 시각 기록
    last_command_time_ = std::chrono::steady_clock::now();

    // 속도가 0이면 이미 정지 상태
    has_active_command_ =
      (command.linear_x != 0.0 || command.angular_z != 0.0);

    publishSafeCommand(command);

    RCLCPP_INFO(
      this->get_logger(),
      "Command: linear=%.2f, angular=%.2f",
      command.linear_x,
      command.angular_z);
  }

  // 처리된 명령을 ROS2 토픽으로 발행
  void publishSafeCommand(const VelocityCommand & command)
  {
    geometry_msgs::msg::Twist safe_msg;

    safe_msg.linear.x = command.linear_x;
    safe_msg.angular.z = command.angular_z;

    safe_publisher_->publish(safe_msg);
  }

  // 명령 수신이 중단됐는지 검사
  void checkCommandTimeout()
  {
    if (!has_active_command_) {
      return;
    }

    const auto now = std::chrono::steady_clock::now();
    const auto elapsed = now - last_command_time_;

    if (elapsed < std::chrono::seconds(1)) {
      return;
    }

    // 타임아웃 발생: 정지 명령 발행
    controller_.stop();
    has_active_command_ = false;

    publishSafeCommand(controller_.getCommand());

    RCLCPP_WARN(
      this->get_logger(),
      "Command timeout. Robot stopped.");
  }

  RobotController controller_;

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr
    safe_publisher_;

  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr
    command_subscriber_;

  rclcpp::TimerBase::SharedPtr timeout_timer_;

  std::chrono::steady_clock::time_point last_command_time_{};

  bool has_active_command_{false};
};

}  // namespace robot_controller_cpp

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node =
    std::make_shared<robot_controller_cpp::RobotControlNode>();

  rclcpp::spin(node);

  rclcpp::shutdown();

  return 0;
}
