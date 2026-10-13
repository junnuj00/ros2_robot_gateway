#include <gtest/gtest.h>

#include <limits>

#include "robot_controller_cpp/robot_controller.hpp"

using robot_controller_cpp::RobotController;

// 1. 초기 상태 확인
TEST(RobotControllerTest, InitialCommandIsZero)
{
    RobotController controller;

    const auto command = controller.getCommand();

    EXPECT_DOUBLE_EQ(command.linear_x, 0.0);
    EXPECT_DOUBLE_EQ(command.angular_z, 0.0);
}

// 2. 정상적인 이동 명령
TEST(RobotControllerTest, AcceptsValidCommand)
{
    RobotController controller;

    EXPECT_TRUE(controller.setCommand(0.8, 0.4));

    const auto command = controller.getCommand();

    EXPECT_DOUBLE_EQ(command.linear_x, 0.8);
    EXPECT_DOUBLE_EQ(command.angular_z, 0.4);
}

// 3. 최대 속도 제한
TEST(RobotControllerTest, ClampsExcessiveSpeed)
{
    RobotController controller;

    EXPECT_TRUE(controller.setCommand(3.0, 2.0));

    const auto command = controller.getCommand();

    EXPECT_DOUBLE_EQ(command.linear_x, 1.0);
    EXPECT_DOUBLE_EQ(command.angular_z, 1.5);
}

// 4. 음수 방향 속도 제한
TEST(RobotControllerTest, ClampsNegativeSpeed)
{
    RobotController controller;

    EXPECT_TRUE(controller.setCommand(-3.0, -2.0));

    const auto command = controller.getCommand();

    EXPECT_DOUBLE_EQ(command.linear_x, -1.0);
    EXPECT_DOUBLE_EQ(command.angular_z, -1.5);
}

// 5. NaN 입력 거부
TEST(RobotControllerTest, RejectsNaN)
{
    RobotController controller;

    controller.setCommand(0.5, 0.3);

    const double nan =
    std::numeric_limits<double>::quiet_NaN();

    EXPECT_FALSE(controller.setCommand(nan, 0.5));

    const auto command = controller.getCommand();

    EXPECT_DOUBLE_EQ(command.linear_x, 0.0);
    EXPECT_DOUBLE_EQ(command.angular_z, 0.0);
}

// 6. 무한대 입력 거부
TEST(RobotControllerTest, RejectsInfinity)
{
    RobotController controller;

    const double infinity =
    std::numeric_limits<double>::infinity();

    EXPECT_FALSE(controller.setCommand(infinity, 0.5));

    const auto command = controller.getCommand();

    EXPECT_DOUBLE_EQ(command.linear_x, 0.0);
    EXPECT_DOUBLE_EQ(command.angular_z, 0.0);
}

// 7. 정지 명령
TEST(RobotControllerTest, StopResetsCommand)
{
    RobotController controller;

    controller.setCommand(0.8, 0.4);
    controller.stop();

    const auto command = controller.getCommand();

    EXPECT_DOUBLE_EQ(command.linear_x, 0.0);
    EXPECT_DOUBLE_EQ(command.angular_z, 0.0);
}
