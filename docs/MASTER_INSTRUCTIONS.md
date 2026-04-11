# TTC System — Professional Maintenance Master Instructions

**Date:** April 11, 2026  
**Audience:** VS Code Copilot & Development Team  
**Standard:** Professional "10/10" Grade  
**Compliance:** ISO 15623 (Safety), PEP 8 (Python), MISRA-C (Firmware)

---

## 1. Project Context (Elite Level)

### Goal
Professional-grade Time-To-Collision (TTC) risk prediction system suitable for automotive safety applications.

### Standards & Compliance
- **Safety:** ISO 15623 (Road Vehicles — Collision Risk Mitigation Systems)
- **Python Code:** PEP 8 style guide + type hints on all functions
- **Firmware:** MISRA-C guidelines + static analysis
- **Architecture:** Layered design with clear separation: ESP32 Firmware (sensor fusion) | Python Dashboard (analytics & UI)

### Design Principles
1. **Single Source of Truth**: `firmware/pinmap.h` for pins, `firmware/config/config.h` for thresholds
2. **Graceful Degradation**: System works without optional components (ML, LIDAR)
3. **Canonical Telemetry**: 7-field CSV format immutable (timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence)
4. **Real-Time Analytics**: Dashboard updates at 5 Hz minimum
5. **Testability**: All core functions unit-tested, integration tests for critical paths

---

## 2. Professional Maintenance Tasks (Priority Order)

### Task 1: Code Quality Audit & Type Hints (HIGH PRIORITY)

**Objective:** Achieve 100% PEP 8 compliance and add type annotations to all Python functions.

**Scope:**
- All files in `src/` (dashboard.py, serial_reader.py, analytics.py, etc.)
- All files in `validation/` (protocol_contract_test.py, evaluate_synthetic.py, etc.)
- All files in `bridge/` (wokwi_serial_bridge.py)

**Acceptance Criteria:**
- [ ] `pylint` score ≥ 9.5/10 across entire codebase
- [ ] All function signatures include type hints (args + return type)
- [ ] No `# type: ignore` comments without justification
- [ ] Docstrings follow NumPy style (not Google style)
- [ ] Example:
  ```python
  def validate_csv_line(line: str) -> Optional[Dict[str, float]]:
      """Parse and validate a CSV telemetry line.
      
      Parameters
      ----------
      line : str
          CSV line with 7 comma-separated fields.
          
      Returns
      -------
      Optional[Dict[str, float]]
          Parsed packet dict if valid, None if invalid.
      """
  ```

**Reference:** `src/validators.py`, `src/config.py`  
**Timeline:** 4–6 hours

---

### Task 2: Firmware Optimization — Extended Kalman Filter (HIGH PRIORITY)

**Objective:** Replace simple Kalman filter with EKF for non-linear sensor fusion.

**Current State:**
- `firmware/config/kalman_filter.h`: Basic 1D Kalman filter
- Works well but assumes linear dynamics

**Enhancement:**
- Implement EKF with non-linear measurement model
- Account for sensor noise characteristics (HC-SR04 vs LIDAR)
- Adaptive process noise based on speed/acceleration

**Acceptance Criteria:**
- [ ] EKF implementation in `firmware/config/extended_kalman_filter.h`
- [ ] Distance noise reduced by 15%+ in real-world testing
- [ ] Firmware size increase < 5KB
- [ ] No degradation in 100ms update rate
- [ ] Existing validation tests still pass

**Reference:** `firmware/config/kalman_filter.h`, `firmware/sensors/sensor_fusion.h`  
**Timeline:** 6–8 hours

---

### Task 3: Advanced Analytics — Collision Probability (HIGH PRIORITY)

**Objective:** Calculate real-time collision probability and generate session summary reports.

**New Functions (in `src/analytics.py`):**
```python
def calculate_collision_probability(
    ttc_sec: float,
    closing_velocity_kmh: float,
    confidence: float,
    reaction_time_sec: float = 0.75
) -> float:
    """
    Bayesian calculation of collision probability.
    Returns: Probability [0.0, 1.0]
    """

def generate_session_summary_json(
    session_csv_path: Path,
    output_dir: Path
) -> Dict:
    """
    Generate comprehensive session analysis JSON.
    Includes: statistics, risk timeline, key events, recommendations.
    """
```

**Acceptance Criteria:**
- [ ] Collision probability formula validated against ISO 15623 examples
- [ ] Session summary JSON includes: min/max/mean TTC, risk events, driver score
- [ ] Can process 1000-row session in < 1 second
- [ ] JSON schema documented

**Reference:** `src/analytics.py`  
**Timeline:** 4–5 hours

---

### Task 4: Dashboard UI/UX Enhancement (MEDIUM PRIORITY)

**Objective:** Add professional safety monitoring widgets.

**New Components:**
1. **Risk Gauge** — Radial gauge showing live risk level (SAFE→WARNING→CRITICAL)
2. **Safety Score** — Running metric of driver performance (0–100)
3. **Collision Probability Timeline** — Plot of risk over time
4. **Alert History** — Scrollable log of critical/warning events

**Acceptance Criteria:**
- [ ] Risk Gauge updates smoothly at 5Hz
- [ ] Safety Score calculated per session (weighted formula)
- [ ] Dashboard loads in < 2 seconds
- [ ] Mobile-responsive layout (works on phone browser)
- [ ] Color-blind friendly palette

**Reference:** `src/dashboard.py`  
**Example:**
```python
# Add to dashboard.py
with st.columns([1, 2, 1]):
    st.markdown("### Risk Gauge")
    risk_gauge = st.empty()
    risk_gauge.metric("Current Risk", current_risk_class, delta=risk_trend)
```

**Timeline:** 5–6 hours

---

### Task 5: Automated Report Generation (MEDIUM PRIORITY)

**Objective:** Generate professional PDF safety audits from session CSVs.

**New Script:** `src/report_generator.py`

**Output:** PDF with:
- Executive Summary (key statistics, risk events)
- Charts: TTC timeline, distance vs speed, risk heatmap
- Risk Analysis: Critical moments with recommendations
- Safety Compliance: ISO 15623 checklist
- Recommendations for driver improvement

**Acceptance Criteria:**
- [ ] PDF generation < 5 seconds per session
- [ ] Charts are publication-quality (matplotlib tight layout)
- [ ] Handles sessions with 100–10,000 rows
- [ ] All text readable at 96 DPI
- [ ] Example:
  ```bash
  python src/report_generator.py --input LOGS/session_20260411_161234.csv --output reports/
  ```

**Reference:** New file `src/report_generator.py`  
**Timeline:** 5–7 hours

---

### Task 6: Expanded Test Suite & Coverage (MEDIUM PRIORITY)

**Objective:** Achieve 90%+ code coverage with integration tests.

**New Tests (in `tests/`):**
- `test_session_analytics.py` — Full lifecycle of SessionAnalytics class
- `test_dashboard_metrics.py` — Dashboard calculation validation
- `test_bridge_integration.py` — End-to-end packet flow
- `test_serial_reader.py` — Mock serial port reading

**Acceptance Criteria:**
- [ ] Coverage report: `pytest --cov=src --cov-report=html`
- [ ] Overall coverage ≥ 90%
- [ ] All critical paths (TTC calculation, risk classification) at 100% coverage
- [ ] Tests run in < 10 seconds
- [ ] CI/CD integration: tests auto-run on push

**Reference:** `tests/`, `validation/`  
**Timeline:** 6–8 hours

---

### Task 7: CI/CD Enhancement (MEDIUM PRIORITY)

**Objective:** Automated quality gates on every commit.

**Update `.github/workflows/main.yml`:**
1. Python linting: `pylint src/ validation/`
2. Type checking: `mypy src/ --strict`
3. Unit tests: `pytest tests/`
4. Code coverage: `pytest --cov=src`
5. Arduino compilation: `arduino-cli compile --fqbn esp32:esp32:esp32doit-devkit-v1 firmware/main.ino`
6. Documentation: Auto-generate via MkDocs or Sphinx

**Acceptance Criteria:**
- [ ] Workflow completes in < 5 minutes
- [ ] Blocking gates: linting ≥9.5, tests 100% pass, coverage ≥90%
- [ ] Non-blocking gates: documentation generation, firmware size tracking
- [ ] Slack/email notifications on failure
- [ ] Badge in README showing build status

**Reference:** `.github/workflows/`  
**Timeline:** 3–4 hours

---

### Task 8: Safety Audit & Compliance Documentation (HIGH PRIORITY)

**Objective:** Document all safety thresholds and validate against ISO 15623.

**New File:** `docs/SAFETY_CASE.md`

**Contents:**
- TTC thresholds: Why 1.5s (critical) and 3.0s (warning)?
- Sensor reliability: Specifications for HC-SR04, MPU6050
- Failure modes: What happens if distance sensor fails?
- Risk acceptance: Who approved these thresholds?
- Traceability matrix: ISO 15623 requirements → firmware config

**Acceptance Criteria:**
- [ ] Every threshold in `firmware/config/config.h` has documented justification
- [ ] Cross-reference: `firmware/config/config.h` ↔ `src/config.py` ↔ `docs/SAFETY_CASE.md`
- [ ] All sensor specs match datasheet claims
- [ ] Failure handling documented (graceful degradation paths)
- [ ] Signature/approval placeholder for safety engineer

**Timeline:** 3–4 hours

---

### Task 9: Protocol Verification (ONGOING)

**Objective:** Enforce immutable 7-field telemetry contract.

**Process:**
- After ANY change to telemetry format, run:
  ```bash
  python validation/protocol_contract_test.py
  ```
- If modification needed, update in this order:
  1. `firmware/main.ino` (emitTelemetryPacket function)
  2. `src/config.py` (TELEMETRY_FIELDS)
  3. `docs/serial_protocol.md` (documentation)
  4. Add test case to protocol_contract_test.py
- Rule: **7-field format is immutable. Period.**

**Acceptance Criteria:**
- [ ] Protocol tests always pass
- [ ] No legacy packet formats supported (no backward compatibility hacks)
- [ ] Any breaking change requires major version bump + release notes

**Timeline:** Ongoing check (< 5 min per change)

---

## 3. Professional Assembly & Deployment Checklist

### Hardware Prerequisites
```
✅ ESP32 DevKit-V1 (30-pin)
✅ 2x HC-SR04 Ultrasonic Sensors (5V)
✅ MPU6050 Accelerometer (I2C)
✅ SSD1306 OLED Display (I2C, 0.96")
✅ KY-040 Rotary Encoder
✅ 5x LEDs (2x green, 2x yellow, 1x red) + 220Ω resistors
✅ 1x Active Buzzer (5V)
✅ Breadboard (830-point+)
✅ Jumper wires (50+ pack)
✅ USB Micro-B cable
✅ 5V power adapter (2A)
```

### Firmware Deployment
```
1. Arduino IDE → Tools → Board → ESP32 Dev Module
2. Verify: Sketch → Compile (Ctrl+R) → 0 errors
3. Upload: Sketch → Upload (Ctrl+U)
4. Monitor: Tools → Serial Monitor (115200 baud)
5. Expected: CSV lines like "1000,245.30,0.00,99.00,99.00,0,0.90"
```

### Software Deployment
```
1. Python: .venv\Scripts\activate
2. Dashboard: streamlit run src/dashboard.py
3. Serial Reader: python src/serial_reader.py --port COMx
4. Verify: Live metrics update every 200ms
```

### Validation Gates
```
✅ python validation/protocol_contract_test.py    (must pass: 6/6)
✅ python validation/evaluate_synthetic.py        (must pass: 100%)
✅ python validation/pin_validator.py             (must pass: 14/14)
✅ pytest tests/                                   (must pass: all)
✅ pylint src/ validation/                         (must pass: ≥9.5)
```

---

## 4. Standards & Guidelines

### Code Style
- **Python:** PEP 8 + Black formatter (line length 100)
- **Firmware:** MISRA-C + astyle formatter
- **Docstrings:** NumPy style (not Google)
- **Type Hints:** Mandatory for all function signatures

### Testing
- **Unit Tests:** pytest for Python; no C++ unit tests (Arduino limitation)
- **Integration Tests:** End-to-end CSV → dashboard flow
- **Coverage Goal:** 90%+ (critical paths 100%)
- **Performance:** No function should take >1 second

### Documentation
- **Inline Comments:** Only for "why", not "what"
- **Docstrings:** One-liner + detailed params/returns
- **README:** Keep up-to-date with current features
- **Safety Case:** Document all thresholds and justifications

### Version Control
- **Conventional Commits:** `type(scope): message`
  - Example: `feat(dashboard): Add collision probability gauge`
  - Types: feat, fix, docs, refactor, test, ci
- **Branches:** `feature/`, `bugfix/`, `hotfix/` prefixes
- **Co-authored-by:** Always include for paired work

---

## 5. Rapid Response Fixes

### If Validation Fails
```
1. Run: python validation/protocol_contract_test.py
2. If fails: Check emitTelemetryPacket() in firmware/main.ino
3. If fails: Check TELEMETRY_FIELDS in src/config.py
4. Fix: Update both files + docs/serial_protocol.md
5. Verify: Re-run validation suite (must pass 31/31 tests)
```

### If Dashboard Won't Start
```
1. Check: .venv is activated
2. Check: All imports in src/dashboard.py (pip install --upgrade streamlit pandas)
3. Check: LOGS/live_data.txt exists and has valid CSV
4. Run: python src/serial_reader.py --port COMx first
5. Then: streamlit run src/dashboard.py
```

### If Hardware Telemetry Stops
```
1. Check: Serial Monitor (115200 baud) shows data
2. Check: ESP32 LED is blinking
3. Check: All sensor connections per pinmap.h
4. Reboot: Unplug USB, wait 2s, reconnect
5. Reupload: Ctrl+U in Arduino IDE
```

---

## 6. Professional Checklist Before Release

- [ ] All 9 tasks completed (or deferred with justification)
- [ ] Validation: 31/31 tests pass
- [ ] Coverage: pytest --cov reports ≥90%
- [ ] Linting: pylint score ≥9.5
- [ ] Type Checking: mypy --strict passes
- [ ] Documentation: README, SAFETY_CASE.md, docs/ all current
- [ ] Git: Clean history, all commits conventional format
- [ ] Arduino: Compiles with 0 warnings
- [ ] Dashboard: 5Hz update rate, no lag
- [ ] Hardware: All sensors respond, no dead zones

---

## 7. Emergency Contacts & Escalation

| Issue | Check | Contact |
|-------|-------|---------|
| Firmware won't compile | Verify Arduino IDE board + libraries | Copilot: `validate-firmware-compile` task |
| Protocol contract broken | Run `protocol_contract_test.py` | Revert last telemetry format change |
| Critical safety threshold question | See `docs/SAFETY_CASE.md` | Safety engineer review required |
| Performance degradation | Profile with `time` module | Optimize bottleneck or allocate more resources |

---

## 8. Professional Handoff Template

When passing this system to another team/developer:

1. **Read:** `docs/PROJECT_ORGANIZATION.md` + `README.md`
2. **Run:** All validation tests (should pass 31/31)
3. **Explore:** `firmware/pinmap.h` (pin assignments), `src/config.py` (thresholds)
4. **Ask:** Any deviations from this master guide?
5. **Update:** This file if new standards are adopted

---

## Appendix: Master Instructions Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-11 | Initial master instructions for 10/10 professional standard |

---

**Status:** 🟢 **ACTIVE GUIDANCE DOCUMENT**

This document is the authoritative reference for maintaining TTC at a professional "10/10" grade. Treat it as law for quality gates and acceptance criteria.

**Last Reviewed:** April 11, 2026  
**Next Review:** After completion of 3 or more tasks
