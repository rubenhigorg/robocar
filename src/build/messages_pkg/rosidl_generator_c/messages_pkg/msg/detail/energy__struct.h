// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice

#ifndef MESSAGES_PKG__MSG__DETAIL__ENERGY__STRUCT_H_
#define MESSAGES_PKG__MSG__DETAIL__ENERGY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Struct defined in msg/Energy in the package messages_pkg.
typedef struct messages_pkg__msg__Energy
{
  double voltage_battery_1;
  double voltage_battery_2;
  double voltage_battery_3;
  double current;
} messages_pkg__msg__Energy;

// Struct for a sequence of messages_pkg__msg__Energy.
typedef struct messages_pkg__msg__Energy__Sequence
{
  messages_pkg__msg__Energy * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} messages_pkg__msg__Energy__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MESSAGES_PKG__MSG__DETAIL__ENERGY__STRUCT_H_
