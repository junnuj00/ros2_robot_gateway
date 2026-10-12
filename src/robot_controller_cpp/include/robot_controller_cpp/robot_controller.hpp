#pragma once

namespace robot_controller_cpp
{

struct VelocityCommand
{
    double linear_x{0.0};
    double angular_z{0.0};
};

class RobotController
{
public:
    bool setCommand(double linear_x, double angular_z);

    void stop();

    VelocityCommand getCommand() const;

private:
    static constexpr double kMaxLinearSpeed{1.0};
    static constexpr double kMaxAngularSpeed{1.5};

    VelocityCommand command_{};
};

}  // namespace robot_controller_cpp