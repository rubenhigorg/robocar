// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice

#include "messages_pkg/msg/detail/energy__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_messages_pkg
const rosidl_type_hash_t *
messages_pkg__msg__Energy__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x9f, 0x0a, 0x49, 0x80, 0x57, 0x6d, 0x21, 0x82,
      0x44, 0x43, 0x8e, 0x0b, 0x88, 0x5e, 0xdb, 0xc7,
      0xed, 0xb2, 0xd5, 0x58, 0x8d, 0xc7, 0x68, 0x38,
      0x14, 0x4d, 0x7e, 0x1d, 0xc5, 0x3e, 0xf3, 0x80,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char messages_pkg__msg__Energy__TYPE_NAME[] = "messages_pkg/msg/Energy";

// Define type names, field names, and default values
static char messages_pkg__msg__Energy__FIELD_NAME__voltage_battery_1[] = "voltage_battery_1";
static char messages_pkg__msg__Energy__FIELD_NAME__voltage_battery_2[] = "voltage_battery_2";
static char messages_pkg__msg__Energy__FIELD_NAME__voltage_battery_3[] = "voltage_battery_3";
static char messages_pkg__msg__Energy__FIELD_NAME__current[] = "current";

static rosidl_runtime_c__type_description__Field messages_pkg__msg__Energy__FIELDS[] = {
  {
    {messages_pkg__msg__Energy__FIELD_NAME__voltage_battery_1, 17, 17},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_DOUBLE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {messages_pkg__msg__Energy__FIELD_NAME__voltage_battery_2, 17, 17},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_DOUBLE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {messages_pkg__msg__Energy__FIELD_NAME__voltage_battery_3, 17, 17},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_DOUBLE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {messages_pkg__msg__Energy__FIELD_NAME__current, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_DOUBLE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
messages_pkg__msg__Energy__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {messages_pkg__msg__Energy__TYPE_NAME, 23, 23},
      {messages_pkg__msg__Energy__FIELDS, 4, 4},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "float64 voltage_battery_1\n"
  "float64 voltage_battery_2\n"
  "float64 voltage_battery_3\n"
  "float64 current";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
messages_pkg__msg__Energy__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {messages_pkg__msg__Energy__TYPE_NAME, 23, 23},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 93, 93},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
messages_pkg__msg__Energy__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *messages_pkg__msg__Energy__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
