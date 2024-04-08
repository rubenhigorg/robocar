// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from messages_pkg:msg/Energy.idl
// generated code does not contain a copyright notice
#include "messages_pkg/msg/detail/energy__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
messages_pkg__msg__Energy__init(messages_pkg__msg__Energy * msg)
{
  if (!msg) {
    return false;
  }
  // voltage_battery_1
  // voltage_battery_2
  // voltage_battery_3
  // current
  return true;
}

void
messages_pkg__msg__Energy__fini(messages_pkg__msg__Energy * msg)
{
  if (!msg) {
    return;
  }
  // voltage_battery_1
  // voltage_battery_2
  // voltage_battery_3
  // current
}

bool
messages_pkg__msg__Energy__are_equal(const messages_pkg__msg__Energy * lhs, const messages_pkg__msg__Energy * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // voltage_battery_1
  if (lhs->voltage_battery_1 != rhs->voltage_battery_1) {
    return false;
  }
  // voltage_battery_2
  if (lhs->voltage_battery_2 != rhs->voltage_battery_2) {
    return false;
  }
  // voltage_battery_3
  if (lhs->voltage_battery_3 != rhs->voltage_battery_3) {
    return false;
  }
  // current
  if (lhs->current != rhs->current) {
    return false;
  }
  return true;
}

bool
messages_pkg__msg__Energy__copy(
  const messages_pkg__msg__Energy * input,
  messages_pkg__msg__Energy * output)
{
  if (!input || !output) {
    return false;
  }
  // voltage_battery_1
  output->voltage_battery_1 = input->voltage_battery_1;
  // voltage_battery_2
  output->voltage_battery_2 = input->voltage_battery_2;
  // voltage_battery_3
  output->voltage_battery_3 = input->voltage_battery_3;
  // current
  output->current = input->current;
  return true;
}

messages_pkg__msg__Energy *
messages_pkg__msg__Energy__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  messages_pkg__msg__Energy * msg = (messages_pkg__msg__Energy *)allocator.allocate(sizeof(messages_pkg__msg__Energy), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(messages_pkg__msg__Energy));
  bool success = messages_pkg__msg__Energy__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
messages_pkg__msg__Energy__destroy(messages_pkg__msg__Energy * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    messages_pkg__msg__Energy__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
messages_pkg__msg__Energy__Sequence__init(messages_pkg__msg__Energy__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  messages_pkg__msg__Energy * data = NULL;

  if (size) {
    data = (messages_pkg__msg__Energy *)allocator.zero_allocate(size, sizeof(messages_pkg__msg__Energy), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = messages_pkg__msg__Energy__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        messages_pkg__msg__Energy__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
messages_pkg__msg__Energy__Sequence__fini(messages_pkg__msg__Energy__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      messages_pkg__msg__Energy__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

messages_pkg__msg__Energy__Sequence *
messages_pkg__msg__Energy__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  messages_pkg__msg__Energy__Sequence * array = (messages_pkg__msg__Energy__Sequence *)allocator.allocate(sizeof(messages_pkg__msg__Energy__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = messages_pkg__msg__Energy__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
messages_pkg__msg__Energy__Sequence__destroy(messages_pkg__msg__Energy__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    messages_pkg__msg__Energy__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
messages_pkg__msg__Energy__Sequence__are_equal(const messages_pkg__msg__Energy__Sequence * lhs, const messages_pkg__msg__Energy__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!messages_pkg__msg__Energy__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
messages_pkg__msg__Energy__Sequence__copy(
  const messages_pkg__msg__Energy__Sequence * input,
  messages_pkg__msg__Energy__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(messages_pkg__msg__Energy);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    messages_pkg__msg__Energy * data =
      (messages_pkg__msg__Energy *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!messages_pkg__msg__Energy__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          messages_pkg__msg__Energy__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!messages_pkg__msg__Energy__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
