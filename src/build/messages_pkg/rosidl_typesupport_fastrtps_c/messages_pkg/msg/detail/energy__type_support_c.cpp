// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice
#include "messages_pkg/msg/detail/energy__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "messages_pkg/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "messages_pkg/msg/detail/energy__struct.h"
#include "messages_pkg/msg/detail/energy__functions.h"
#include "fastcdr/Cdr.h"

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

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif


// forward declare type support functions


using _Energy__ros_msg_type = messages_pkg__msg__Energy;

static bool _Energy__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _Energy__ros_msg_type * ros_message = static_cast<const _Energy__ros_msg_type *>(untyped_ros_message);
  // Field name: voltage_battery_1
  {
    cdr << ros_message->voltage_battery_1;
  }

  // Field name: voltage_battery_2
  {
    cdr << ros_message->voltage_battery_2;
  }

  // Field name: voltage_battery_3
  {
    cdr << ros_message->voltage_battery_3;
  }

  // Field name: current
  {
    cdr << ros_message->current;
  }

  return true;
}

static bool _Energy__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _Energy__ros_msg_type * ros_message = static_cast<_Energy__ros_msg_type *>(untyped_ros_message);
  // Field name: voltage_battery_1
  {
    cdr >> ros_message->voltage_battery_1;
  }

  // Field name: voltage_battery_2
  {
    cdr >> ros_message->voltage_battery_2;
  }

  // Field name: voltage_battery_3
  {
    cdr >> ros_message->voltage_battery_3;
  }

  // Field name: current
  {
    cdr >> ros_message->current;
  }

  return true;
}  // NOLINT(readability/fn_size)

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_messages_pkg
size_t get_serialized_size_messages_pkg__msg__Energy(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _Energy__ros_msg_type * ros_message = static_cast<const _Energy__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name voltage_battery_1
  {
    size_t item_size = sizeof(ros_message->voltage_battery_1);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name voltage_battery_2
  {
    size_t item_size = sizeof(ros_message->voltage_battery_2);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name voltage_battery_3
  {
    size_t item_size = sizeof(ros_message->voltage_battery_3);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name current
  {
    size_t item_size = sizeof(ros_message->current);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _Energy__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_messages_pkg__msg__Energy(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_messages_pkg
size_t max_serialized_size_messages_pkg__msg__Energy(
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

  // member: voltage_battery_1
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }
  // member: voltage_battery_2
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }
  // member: voltage_battery_3
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }
  // member: current
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
    using DataType = messages_pkg__msg__Energy;
    is_plain =
      (
      offsetof(DataType, current) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static size_t _Energy__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_messages_pkg__msg__Energy(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_Energy = {
  "messages_pkg::msg",
  "Energy",
  _Energy__cdr_serialize,
  _Energy__cdr_deserialize,
  _Energy__get_serialized_size,
  _Energy__max_serialized_size
};

static rosidl_message_type_support_t _Energy__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_Energy,
  get_message_typesupport_handle_function,
  &messages_pkg__msg__Energy__get_type_hash,
  &messages_pkg__msg__Energy__get_type_description,
  &messages_pkg__msg__Energy__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, messages_pkg, msg, Energy)() {
  return &_Energy__type_support;
}

#if defined(__cplusplus)
}
#endif
