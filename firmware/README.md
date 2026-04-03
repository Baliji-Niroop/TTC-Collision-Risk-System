# Firmware

Embedded packet-emitter implementation and TTC/risk computation for ESP32.

## Layout
- config/: protocol and thresholds
- sensors/: sensor abstraction and acquisition
- alerts/: risk-classification and display alert logic
- ml/: TTC computation engine used by local fallback logic

## Compatibility
Root header wrappers remain in place so existing includes in main.ino continue to work.
