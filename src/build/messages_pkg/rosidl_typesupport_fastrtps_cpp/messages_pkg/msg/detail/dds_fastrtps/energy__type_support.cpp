// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice
#include "messages_pkg/msg/detail/energy__rosidl_typesupport_fastrtps_cpp.hpp"
#include "messages_pkg/msg/detail/energy__functions.h"
#include "messages_pkg/msg/detail/energy__struct.hpp"

#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions

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
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: voltage_battery_1
  cdr << ros_message.voltage_battery_1;
  // Member: voltage_battery_2
  cdr << ros_message.voltage_battery_2;
  // Member: voltage_battery_3
  cdr << ros_message.voltage_battery_3;
  // Member: current
  cdr << ros_message.current;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  messages_pkg::msg::Energy & ros_message)
{
  // Member: voltage_battery_1
  cdr >> ros_message.voltage_battery_1;

  // Member: voltage_battery_2
  cdr >> ros_message.voltage_battery_2;

  // Member: voltage_battery_3
  cdr >> ros_message.voltage_battery_3;

  // Member: current
  cdr >> ros_message.current;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
get_serialized_size(
  const messages_pkg::msg::Energy & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: voltage_battery_1
  {
    size_t item_size = sizeof(ros_message.voltage_battery_1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: voltage_battery_2
  {
    size_t item_size = sizeof(ros_message.voltage_battery_2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: voltage_battery_3
  {
    size_t item_size = sizeof(ros_message.voltage_battery_3);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: current
  {
    size_t item_size = sizeof(ros_message.current);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_messages_pkg
max_serialized_size_Energy(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;


  // Member: voltage_battery_1
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: voltage_battery_2
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: voltage_battery_3
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: current
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = messages_pkg::msg::Energy;
    is_plain =
      (
      offsetof(DataType, current) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static bool _Energy__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const messages_pkg::msg::Energy *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _Energy__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<messages_pkg::msg::Energy *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _Energy__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const messages_pkg::msg::Energy *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _Energy__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_Energy(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _Energy__callbacks = {
  "messages_pkg::msg",
  "Energy",
  _Energy__cdr_serialize,
  _Energy__cdr_deserialize,
  _Energy__get_serialized_size,
  _Energy__max_serialized_size
};

static rosidl_message_type_support_t _Energy__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_Energy__callbacks,
  get_message_typesupport_handle_function,
  &messages_pkg__msg__Energy__get_type_hash,
  &messages_pkg__msg__Energy__get_type_description,
  &messages_pkg__msg__Energy__get_type_description_sources,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace messages_pkg

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_messages_pkg
const rosidl_message_type_support_t *
get_message_type_support_handle<messages_pkg::msg::Energy>()
{
  return &messages_pkg::msg::typesupport_fastrtps_cpp::_Energy__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, messages_pkg, msg, Energy)() {
  return &messages_pkg::msg::typesupport_fastrtps_cpp::_Energy__handle;
}

#ifdef __cplusplus
}
#endif
