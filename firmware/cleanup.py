#!/usr/bin/env python
"""Delete wrapper header files and verify remaining files."""
import os
import sys

# Change to firmware directory
os.chdir(r'c:\Users\niroo\Downloads\TTC\firmware')

# Files to delete from firmware root
root_files = [
    'config.h',
    'serial_protocol.h',
    'sensors.h',
    'oled_display.h',
    'risk_classifier.h',
    'ttc_engine.h'
]

print("=== DELETING WRAPPER FILES ===\n")

# Delete root files
for f in root_files:
    if os.path.exists(f):
        os.remove(f)
        print(f"✓ Deleted: {f}")
    else:
        print(f"✗ Not found: {f}")

# Delete kalman_filter.h from sensors
kalman_path = r'sensors\kalman_filter.h'
if os.path.exists(kalman_path):
    os.remove(kalman_path)
    print(f"✓ Deleted: {kalman_path}")
else:
    print(f"✗ Not found: {kalman_path}")

print("\n=== VERIFYING REMAINING .h FILES ===\n")

# Directories to check
dirs_to_check = {
    'firmware/ root': '.',
    'firmware/config/': 'config',
    'firmware/sensors/': 'sensors',
    'firmware/alerts/': 'alerts',
    'firmware/ml/': 'ml'
}

for label, dir_path in dirs_to_check.items():
    if os.path.isdir(dir_path):
        h_files = sorted([f for f in os.listdir(dir_path) if f.endswith('.h')])
        if h_files:
            print(f"{label}")
            for f in h_files:
                print(f"  - {f}")
        else:
            print(f"{label}")
            print(f"  (no .h files)")
        print()
    else:
        print(f"{label}: DIRECTORY NOT FOUND\n")
