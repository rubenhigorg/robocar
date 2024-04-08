// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice

#ifndef MESSAGES_PKG__MSG__DETAIL__ENERGY__STRUCT_HPP_
#define MESSAGES_PKG__MSG__DETAIL__ENERGY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__messages_pkg__msg__Energy __attribute__((deprecated))
#else
# define DEPRECATED__messages_pkg__msg__Energy __declspec(deprecated)
#endif

namespace messages_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Energy_
{
  using Type = Energy_<ContainerAllocator>;

  explicit Energy_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->voltage_battery_1 = 0.0;
      this->voltage_battery_2 = 0.0;
      this->voltage_battery_3 = 0.0;
      this->current = 0.0;
    }
  }

  explicit Energy_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->voltage_battery_1 = 0.0;
      this->voltage_battery_2 = 0.0;
      this->voltage_battery_3 = 0.0;
      this->current = 0.0;
    }
  }

  // field types and members
  using _voltage_battery_1_type =
    double;
  _voltage_battery_1_type voltage_battery_1;
  using _voltage_battery_2_type =
    double;
  _voltage_battery_2_type voltage_battery_2;
  using _voltage_battery_3_type =
    double;
  _voltage_battery_3_type voltage_battery_3;
  using _current_type =
    double;
  _current_type current;

  // setters for named parameter idiom
  Type & set__voltage_battery_1(
    const double & _arg)
  {
    this->voltage_battery_1 = _arg;
    return *this;
  }
  Type & set__voltage_battery_2(
    const double & _arg)
  {
    this->voltage_battery_2 = _arg;
    return *this;
  }
  Type & set__voltage_battery_3(
    const double & _arg)
  {
    this->voltage_battery_3 = _arg;
    return *this;
  }
  Type & set__current(
    const double & _arg)
  {
    this->current = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    messages_pkg::msg::Energy_<ContainerAllocator> *;
  using ConstRawPtr =
    const messages_pkg::msg::Energy_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<messages_pkg::msg::Energy_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<messages_pkg::msg::Energy_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      messages_pkg::msg::Energy_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<messages_pkg::msg::Energy_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      messages_pkg::msg::Energy_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<messages_pkg::msg::Energy_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<messages_pkg::msg::Energy_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<messages_pkg::msg::Energy_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__messages_pkg__msg__Energy
    std::shared_ptr<messages_pkg::msg::Energy_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__messages_pkg__msg__Energy
    std::shared_ptr<messages_pkg::msg::Energy_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Energy_ & other) const
  {
    if (this->voltage_battery_1 != other.voltage_battery_1) {
      return false;
    }
    if (this->voltage_battery_2 != other.voltage_battery_2) {
      return false;
    }
    if (this->voltage_battery_3 != other.voltage_battery_3) {
      return false;
    }
    if (this->current != other.current) {
      return false;
    }
    return true;
  }
  bool operator!=(const Energy_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Energy_

// alias to use template instance with default allocator
using Energy =
  messages_pkg::msg::Energy_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace messages_pkg

#endif  // MESSAGES_PKG__MSG__DETAIL__ENERGY__STRUCT_HPP_
