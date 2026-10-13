
cmake_minimum_required(VERSION 3.8)
project(robot_controller_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ROS2 dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# RobotController library
add_library(robot_controller
  src/robot_controller.cpp
)

target_compile_features(robot_controller PUBLIC cxx_std_17)

target_include_directories(robot_controller PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# RobotControlNode executable
add_executable(robot_control_node
  src/robot_control_node.cpp
)

target_link_libraries(robot_control_node
  robot_controller
)

ament_target_dependencies(robot_control_node
  rclcpp
  geometry_msgs
)

# Install library
install(
  TARGETS robot_controller
  EXPORT export_robot_controller
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Install executable
install(
  TARGETS robot_control_node
  DESTINATION lib/${PROJECT_NAME}
)

# Install header files
install(
  DIRECTORY include/
  DESTINATION include
)

ament_export_targets(export_robot_controller HAS_LIBRARY_TARGET)

# Automated tests
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_robot_controller
    test/test_robot_controller.cpp
  )

  if(TARGET test_robot_controller)
    target_link_libraries(test_robot_controller
      robot_controller
    )
  endif()

  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
