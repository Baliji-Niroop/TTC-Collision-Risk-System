#!/usr/bin/env python
"""Test script for Wokwi bridge stdin mode"""
import subprocess
import sys
import os

# Change to the TTC directory
os.chdir(r'c:\Users\niroo\Downloads\TTC')

# Canonical packet to test
test_packet = "1000,120,30,2.40,2.20,2,0.85"

print(f"Testing Wokwi bridge with packet: {test_packet}")
print("=" * 60)

# Run the bridge with stdin mode
process = subprocess.Popen(
    [sys.executable, 'bridge/wokwi_serial_bridge.py', '--source', 'stdin', '--no-launch-stack'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send the packet to stdin
stdout, stderr = process.communicate(input=test_packet)

print("STDOUT:")
print(stdout if stdout else "(empty)")
print("\nSTDERR:")
print(stderr if stderr else "(empty)")
print(f"\nReturn code: {process.returncode}")

# Check for logs
print("\n" + "=" * 60)
print("Checking LOGS directory...")

if os.path.exists('LOGS/live_data.txt'):
    print("\nLOGS/live_data.txt exists. Contents:")
    try:
        with open('LOGS/live_data.txt', 'r') as f:
            content = f.read()
            print(content if content else "(empty file)")
    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print("LOGS/live_data.txt not found")

# List LOGS directory
if os.path.exists('LOGS'):
    print("\nFiles in LOGS directory:")
    for f in os.listdir('LOGS'):
        print(f"  - {f}")
