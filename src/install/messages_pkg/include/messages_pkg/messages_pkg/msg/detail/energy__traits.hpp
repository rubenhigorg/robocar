// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice

#ifndef MESSAGES_PKG__MSG__DETAIL__ENERGY__TRAITS_HPP_
#define MESSAGES_PKG__MSG__DETAIL__ENERGY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "messages_pkg/msg/detail/energy__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace messages_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const Energy & msg,
  std::ostream & out)
{
  out << "{";
  // member: voltage_battery_1
  {
    out << "voltage_battery_1: ";
    rosidl_generator_traits::value_to_yaml(msg.voltage_battery_1, out);
    out << ", ";
  }

  // member: voltage_battery_2
  {
    out << "voltage_battery_2: ";
    rosidl_generator_traits::value_to_yaml(msg.voltage_battery_2, out);
    out << ", ";
  }

  // member: voltage_battery_3
  {
    out << "voltage_battery_3: ";
    rosidl_generator_traits::value_to_yaml(msg.voltage_battery_3, out);
    out << ", ";
  }

  // member: current
  {
    out << "current: ";
    rosidl_generator_traits::value_to_yaml(msg.current, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Energy & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: voltage_battery_1
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "voltage_battery_1: ";
    rosidl_generator_traits::value_to_yaml(msg.voltage_battery_1, out);
    out << "\n";
  }

  // member: voltage_battery_2
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "voltage_battery_2: ";
    rosidl_generator_traits::value_to_yaml(msg.voltage_battery_2, out);
    out << "\n";
  }

  // member: voltage_battery_3
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "voltage_battery_3: ";
    rosidl_generator_traits::value_to_yaml(msg.voltage_battery_3, out);
    out << "\n";
  }

  // member: current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "current: ";
    rosidl_generator_traits::value_to_yaml(msg.current, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Energy & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace messages_pkg

namespace rosidl_generator_traits
{

[[deprecated("use messages_pkg::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const messages_pkg::msg::Energy & msg,
  std::ostream & out, size_t indentation = 0)
{
  messages_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use messages_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const messages_pkg::msg::Energy & msg)
{
  return messages_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<messages_pkg::msg::Energy>()
{
  return "messages_pkg::msg::Energy";
}

template<>
inline const char * name<messages_pkg::msg::Energy>()
{
  return "messages_pkg/msg/Energy";
}

template<>
struct has_fixed_size<messages_pkg::msg::Energy>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<messages_pkg::msg::Energy>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<messages_pkg::msg::Energy>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MESSAGES_PKG__MSG__DETAIL__ENERGY__TRAITS_HPP_
