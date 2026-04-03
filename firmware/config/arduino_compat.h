#pragma once

#if defined(__has_include)
#if __has_include(<Arduino.h>)
#include <Arduino.h>
#else
#include <stdint.h>

class __SerialStub {
 public:
  template <typename T>
  void begin(T) {}

  template <typename T>
  void print(const T&) {}

  template <typename T>
  void print(const T&, int) {}

  template <typename T>
  void println(const T&) {}

  template <typename T>
  void println(const T&, int) {}
};

static __SerialStub Serial;

static inline unsigned long millis() { return 0UL; }
static inline void delay(unsigned long) {}
#endif
#else
#include <Arduino.h>
#endif
