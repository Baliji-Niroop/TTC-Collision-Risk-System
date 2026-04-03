# Abstract + Executive Summary

## Abstract
This project implements a Time-to-Collision (TTC) collision-risk monitoring system that unifies embedded telemetry generation, Python ingestion, validation tooling, and a Streamlit monitoring dashboard. The platform uses a frozen 7-field telemetry contract (`timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence`) across simulator, bridge, serial reader, replay runner, and dashboard layers. Risk classification is driven by TTC thresholds (critical <= 1.5s, warning <= 3.0s), with optional machine-learning inference and guaranteed threshold fallback when no model is available.

## Executive Summary

### What is complete
- End-to-end software telemetry pipeline is operational.
- Dashboard supports Simulator, Live Log, and ESP32 Serial modes.
- Wokwi virtual hardware path is operational (OLED/LED/buzzer signaling and canonical packets).
- Validation utilities and schema checks are present and usable.

### What is not complete
- Physical sensor integration is not implemented in firmware (`readDistanceCm`, `readSpeedKmh`, and confidence remain simulated/hardcoded).
- Real-world calibration and field validation are pending.
- Hardware performance claims (latency, false alarm rates) are not yet measured on physical hardware.

### Correct status framing
- Software system readiness: high.
- Physical hardware readiness: low.
- Overall project stage: simulation-validated integrated prototype awaiting physical integration and field verification.

### Key technical decisions
1. Freeze one canonical 7-field telemetry contract across all runtime components.
2. Keep TTC thresholds centralized and synchronized across Python and firmware configs.
3. Enforce model-optional behavior with deterministic TTC fallback.
4. Separate ingestion/validation/analytics/dashboard concerns into modular Python files.
5. Preserve reproducibility with replay and protocol validation scripts.

### Immediate priorities
1. Implement real sensor drivers in firmware.
2. Run physical serial ingestion tests into the existing Python stack.
3. Execute calibration and latency/false-alarm validation plan.
