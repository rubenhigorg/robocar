// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice

#ifndef MESSAGES_PKG__MSG__DETAIL__ENERGY__BUILDER_HPP_
#define MESSAGES_PKG__MSG__DETAIL__ENERGY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "messages_pkg/msg/detail/energy__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace messages_pkg
{

namespace msg
{

namespace builder
{

class Init_Energy_current
{
public:
  explicit Init_Energy_current(::messages_pkg::msg::Energy & msg)
  : msg_(msg)
  {}
  ::messages_pkg::msg::Energy current(::messages_pkg::msg::Energy::_current_type arg)
  {
    msg_.current = std::move(arg);
    return std::move(msg_);
  }

private:
  ::messages_pkg::msg::Energy msg_;
};

class Init_Energy_voltage_battery_3
{
public:
  explicit Init_Energy_voltage_battery_3(::messages_pkg::msg::Energy & msg)
  : msg_(msg)
  {}
  Init_Energy_current voltage_battery_3(::messages_pkg::msg::Energy::_voltage_battery_3_type arg)
  {
    msg_.voltage_battery_3 = std::move(arg);
    return Init_Energy_current(msg_);
  }

private:
  ::messages_pkg::msg::Energy msg_;
};

class Init_Energy_voltage_battery_2
{
public:
  explicit Init_Energy_voltage_battery_2(::messages_pkg::msg::Energy & msg)
  : msg_(msg)
  {}
  Init_Energy_voltage_battery_3 voltage_battery_2(::messages_pkg::msg::Energy::_voltage_battery_2_type arg)
  {
    msg_.voltage_battery_2 = std::move(arg);
    return Init_Energy_voltage_battery_3(msg_);
  }

private:
  ::messages_pkg::msg::Energy msg_;
};

class Init_Energy_voltage_battery_1
{
public:
  Init_Energy_voltage_battery_1()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Energy_voltage_battery_2 voltage_battery_1(::messages_pkg::msg::Energy::_voltage_battery_1_type arg)
  {
    msg_.voltage_battery_1 = std::move(arg);
    return Init_Energy_voltage_battery_2(msg_);
  }

private:
  ::messages_pkg::msg::Energy msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::messages_pkg::msg::Energy>()
{
  return messages_pkg::msg::builder::Init_Energy_voltage_battery_1();
}

}  // namespace messages_pkg

#endif  // MESSAGES_PKG__MSG__DETAIL__ENERGY__BUILDER_HPP_
