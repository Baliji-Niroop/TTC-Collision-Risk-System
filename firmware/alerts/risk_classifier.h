#pragma once

#include "../config/config.h"

inline int classifyRisk(float ttcSeconds) {
  if (ttcSeconds <= TTC_CRITICAL_S) {
    return 2;
  }
  if (ttcSeconds <= TTC_WARNING_S) {
    return 1;
  }
  return 0;
}
