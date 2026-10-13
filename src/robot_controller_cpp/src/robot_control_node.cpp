#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "robot_controller_cpp/robot_controller.hpp"

namespace robot_controller_cpp
{

class RobotControlNode : public rclcpp::Node
{
public:
  RobotControlNode()
  : Node("robot_control_node")
  {
        // Publisher: 검증된 이동 명령 발행
    safe_publisher_ =
      this->create_publisher<geometry_msgs::msg::Twist>(
                "/robot/safe_cmd_vel", 10);

        // Subscriber: 외부 이동 명령 수신
    command_subscriber_ =
      this->create_subscription<geometry_msgs::msg::Twist>(
                "/robot/cmd_vel",
                10,
      [this](geometry_msgs::msg::Twist::SharedPtr msg)
      {
        handleCommand(msg);
                });

    RCLCPP_INFO(
            this->get_logger(),
            "Robot Control Node started.");
  }

private:
    // 1. 이동 명령 수신 및 검증
  void handleCommand(
    const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    const bool accepted = controller_.setCommand(
            msg->linear.x,
            msg->angular.z);

    const auto command = controller_.getCommand();

        // 2. 검증된 명령 발행
    publishSafeCommand(command);

        // 3. 처리 결과 기록
    if (!accepted) {
      RCLCPP_WARN(
                this->get_logger(),
                "Invalid command received. Robot stopped.");
      return;
    }

    RCLCPP_INFO(
            this->get_logger(),
            "Command: linear=%.2f, angular=%.2f",
            command.linear_x,
            command.angular_z);
  }

    // 검증된 이동 명령을 ROS2 메시지로 변환 및 발행
  void publishSafeCommand(const VelocityCommand & command)
  {
    geometry_msgs::msg::Twist safe_msg;

    safe_msg.linear.x = command.linear_x;
    safe_msg.angular.z = command.angular_z;

    safe_publisher_->publish(safe_msg);
  }

    // 로봇 제어 객체
  RobotController controller_;

    // ROS2 Publisher
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr
    safe_publisher_;

    // ROS2 Subscriber
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr
    command_subscriber_;
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
