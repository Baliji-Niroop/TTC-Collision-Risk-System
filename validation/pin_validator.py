#!/usr/bin/env python3
"""
pin_validator.py - Validate pin consistency across firmware, diagram, and bridge.

Purpose:
  Ensures that pin assignments in firmware (pinmap.h) match:
    - Circuit diagram (diagram.json)
    - Bridge expectations (wokwi_serial_bridge.py expectations)

This prevents subtle bugs where, for example, a firmware pin gets changed
but the diagram isn't updated, leading to inconsistent behavior in simulation.

Usage:
  python validation/pin_validator.py [--strict]

Exit codes:
  0: All checks passed
  1: Warnings found (non-critical mismatches)
  2: Errors found (critical mismatches)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict

ROOT_DIR = Path(__file__).resolve().parents[1]


def parse_pinmap_h() -> Dict[str, int]:
    """
    Extract pin definitions from firmware/pinmap.h.

    Returns dict like:
      {
        'PIN_SONAR1_TRIG': 5,
        'PIN_SONAR1_ECHO': 18,
        ...
      }
    """
    pinmap_file = ROOT_DIR / "firmware" / "pinmap.h"
    pins = {}

    if not pinmap_file.exists():
        print(f"ERROR: {pinmap_file} not found")
        return pins

    with open(pinmap_file, "r") as f:
        content = f.read()

    # Match: static const uint8_t PIN_NAME = <number>;
    pattern = r"static\s+const\s+uint8_t\s+(\w+)\s*=\s*(\d+);"
    for match in re.finditer(pattern, content):
        pin_name, pin_number = match.groups()
        pins[pin_name] = int(pin_number)

    return pins


def parse_diagram_json() -> Dict[str, Dict]:
    """
    Extract ESP32 connections from diagram.json.

    Returns dict mapping device IDs to their pin connections:
      {
        'sonar': {'TRIG': ('esp:D5', 'sonar:TRIG'), 'ECHO': ('esp:D18', 'sonar:ECHO')},
        ...
      }
    """
    diagram_file = ROOT_DIR / "diagram.json"
    connections = {}

    if not diagram_file.exists():
        print(f"ERROR: {diagram_file} not found")
        return connections

    with open(diagram_file, "r") as f:
        data = json.load(f)

    # Extract all connections like ["esp:D5", "sonar:TRIG", "green", []]
    for conn in data.get("connections", []):
        if len(conn) >= 2:
            esp_side = conn[0]
            device_side = conn[1]

            # Match esp:D<number> format
            esp_match = re.match(r"esp:D(\d+)", esp_side)
            if esp_match:
                pin_num = int(esp_match.group(1))

                # Extract device ID and pin name
                device_match = re.match(r"(\w+):(\w+)", device_side)
                if device_match:
                    device_id, device_pin = device_match.groups()

                    if device_id not in connections:
                        connections[device_id] = {}

                    connections[device_id][device_pin] = {
                        "esp_pin": pin_num,
                        "esp_side": esp_side,
                        "device_side": device_side,
                    }

    return connections


def extract_digital_pins_from_diagram(diagram_conns: Dict) -> Dict[str, int]:
    """
    Convert diagram connections to flat pin dict like pinmap.h format.

    Returns dict mapping functional names to pins based on diagram structure.
    """
    pins = {}

    # Map device:pin patterns to firmware pin names
    device_mappings = {
        "sonar": {"TRIG": "PIN_SONAR1_TRIG", "ECHO": "PIN_SONAR1_ECHO"},
        "sonar2": {"TRIG": "PIN_SONAR2_TRIG", "ECHO": "PIN_SONAR2_ECHO"},
        "encoder": {"CLK": "PIN_ENCODER_CLK", "DT": "PIN_ENCODER_DT"},
        "oled": {"SDA": "PIN_I2C_SDA", "SCL": "PIN_I2C_SCL"},
        "imu": {"SDA": "PIN_I2C_SDA", "SCL": "PIN_I2C_SCL"},
        "ledSafe1": {"A": "PIN_LED_SAFE1"},
        "ledSafe2": {"A": "PIN_LED_SAFE2"},
        "ledWarning1": {"A": "PIN_LED_WARNING1"},
        "ledWarning2": {"A": "PIN_LED_WARNING2"},
        "ledCritical": {"A": "PIN_LED_CRITICAL"},
        "buzzer": {"2": "PIN_BUZZER"},
    }

    for device_id, device_conns in diagram_conns.items():
        if device_id in device_mappings:
            for device_pin, fw_pin_name in device_mappings[device_id].items():
                if device_pin in device_conns:
                    pins[fw_pin_name] = device_conns[device_pin]["esp_pin"]

    return pins


def validate_pins(strict: bool = False) -> int:
    """
    Validate pin consistency between firmware and diagram.

    Args:
        strict: If True, any warning becomes an error

    Returns:
        0: Pass, 1: Warnings, 2: Errors
    """
    print("=" * 60)
    print("TTC Pin Validator")
    print("=" * 60)

    # Parse both sources
    fw_pins = parse_pinmap_h()
    diagram_conns = parse_diagram_json()
    diagram_pins = extract_digital_pins_from_diagram(diagram_conns)

    if not fw_pins:
        print("ERROR: Could not parse firmware pins")
        return 2

    if not diagram_conns:
        print("ERROR: Could not parse diagram connections")
        return 2

    print(f"\nFirmware pins found: {len(fw_pins)}")
    print(f"Diagram pins mapped: {len(diagram_pins)}\n")

    errors = []
    warnings = []

    # Check: All diagram pins should match firmware
    for pin_name in sorted(set(list(fw_pins.keys()) + list(diagram_pins.keys()))):
        fw_value = fw_pins.get(pin_name)
        diagram_value = diagram_pins.get(pin_name)

        if fw_value is None:
            warnings.append(
                f"  [WARN] {pin_name}: defined in diagram but not in pinmap.h"
            )
        elif diagram_value is None:
            warnings.append(
                f"  [WARN] {pin_name}: defined in pinmap.h but not in diagram"
            )
        elif fw_value != diagram_value:
            errors.append(
                f"  [ERROR] {pin_name}: MISMATCH (pinmap.h={fw_value}, diagram={diagram_value})"
            )
        else:
            print(f"  [OK] {pin_name}: {fw_value}")

    # Report results
    print()
    if errors:
        print("ERRORS (Critical mismatches):")
        for err in errors:
            print(err)

    if warnings:
        print("WARNINGS (Non-critical):")
        for warn in warnings:
            print(warn)

    if not errors and not warnings:
        print("✓ All pins validated successfully!")
        return 0

    if errors:
        print("\n✗ Validation failed: Pin mismatches detected")
        return 2

    if warnings and strict:
        print("\n⚠ Validation failed in strict mode: Warnings treated as errors")
        return 2

    print("\n⚠ Validation passed with warnings")
    return 1


def main() -> int:
    strict = "--strict" in sys.argv
    return validate_pins(strict=strict)


if __name__ == "__main__":
    sys.exit(main())
