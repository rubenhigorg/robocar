// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice

#ifndef MESSAGES_PKG__MSG__DETAIL__ENERGY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define MESSAGES_PKG__MSG__DETAIL__ENERGY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "messages_pkg/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "messages_pkg/msg/detail/energy__struct.hpp"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

#include "fastcdr/Cdr.h"

namespace messages_pkg
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
cdr_serialize(
  const messages_pkg::msg::Energy & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  messages_pkg::msg::Energy & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
get_serialized_size(
  const messages_pkg::msg::Energy & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
max_serialized_size_Energy(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace messages_pkg

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, messages_pkg, msg, Energy)();

#ifdef __cplusplus
}
#endif

#endif  // MESSAGES_PKG__MSG__DETAIL__ENERGY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
