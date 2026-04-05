#pragma once

#include "../config/config.h"

inline int classifyRiskPhysics(float ttcSeconds, int roadCondition) {
  // Road multipliers: 0=Dry(1.0x), 1=Wet(1.4x), 2=Gravel(1.6x), 3=Ice(2.0x)
  float multiplier = 1.0f;
  if (roadCondition == 1) multiplier = 1.4f;
  else if (roadCondition == 2) multiplier = 1.6f;
  else if (roadCondition == 3) multiplier = 2.0f;

  if (ttcSeconds <= TTC_CRITICAL_S * multiplier) {
    return 2;
  }
  if (ttcSeconds <= TTC_WARNING_S * multiplier) {
    return 1;
  }
  return 0;
}

// Applies ML override with safety constraint: ML cannot downgrade a physics CRITICAL.
inline int classifyRiskFinal(float ttcSeconds, int roadCondition, int mlRisk) {
    int physicsRisk = classifyRiskPhysics(ttcSeconds, roadCondition);
    
    // Safety constraint: physics CRITICAL cannot be downgraded
    if (physicsRisk == 2) {
        return 2;
    }
    
    // Otherwise trust ML
    return mlRisk > physicsRisk ? mlRisk : physicsRisk;
}
