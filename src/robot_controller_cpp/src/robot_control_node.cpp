
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
        safe_publisher_ =
            this->create_publisher<geometry_msgs::msg::Twist>(
                "/robot/safe_cmd_vel", 10);

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
    void handleCommand(
        const geometry_msgs::msg::Twist::SharedPtr msg)
    {
        bool accepted = controller_.setCommand(
            msg->linear.x,
            msg->angular.z);

        VelocityCommand command = controller_.getCommand();

        geometry_msgs::msg::Twist safe_msg;
        safe_msg.linear.x = command.linear_x;
        safe_msg.angular.z = command.angular_z;

        safe_publisher_->publish(safe_msg);

        if (!accepted)
        {
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

    RobotController controller_;

    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr
        safe_publisher_;

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
