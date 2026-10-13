#include "robot_controller_cpp/robot_controller.hpp"

#include <algorithm>
#include <cmath>

namespace robot_controller_cpp
{

bool RobotController::setCommand(double linear_x, double angular_z)
{
  if (!std::isfinite(linear_x) || !std::isfinite(angular_z)) {
    stop();
    return false;
  }

  command_.linear_x = std::clamp(
        linear_x,
        -kMaxLinearSpeed,
        kMaxLinearSpeed
  );

  command_.angular_z = std::clamp(
        angular_z,
        -kMaxAngularSpeed,
        kMaxAngularSpeed
  );

  return true;
}

void RobotController::stop()
{
  command_.linear_x = 0.0;
  command_.angular_z = 0.0;
}

VelocityCommand RobotController::getCommand() const
{
  return command_;
}

}  // namespace robot_controller_cpp
