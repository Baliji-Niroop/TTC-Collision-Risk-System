#pragma once

#if defined(ARDUINO) && !defined(__INTELLISENSE__)
#include <Arduino.h>
#include <Wire.h>
#else
#include <stdint.h>
#include <cstddef>

#ifndef IRAM_ATTR
#define IRAM_ATTR
#endif

#ifndef HIGH
#define HIGH 0x1
#endif

#ifndef LOW
#define LOW 0x0
#endif

#ifndef OUTPUT
#define OUTPUT 0x1
#endif

#ifndef INPUT
#define INPUT 0x0
#endif

#ifndef INPUT_PULLUP
#define INPUT_PULLUP 0x2
#endif

#ifndef RISING
#define RISING 0x03
#endif

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
static inline void delayMicroseconds(unsigned int) {}
static inline void pinMode(uint8_t, uint8_t) {}
static inline void digitalWrite(uint8_t, uint8_t) {}
static inline unsigned long pulseIn(uint8_t, uint8_t, unsigned long = 1000000UL) { return 0UL; }
static inline int digitalPinToInterrupt(uint8_t pin) { return static_cast<int>(pin); }
static inline void attachInterrupt(int, void (*)(), int) {}
static inline void noInterrupts() {}
static inline void interrupts() {}

class __WireStub {
 public:
  void begin(int = -1, int = -1) {}
  void setClock(uint32_t) {}
};

static __WireStub Wire;
#endif
