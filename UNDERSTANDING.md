# Understanding the Project

The TTC Collision Risk Monitoring System is fundamentally a time-based safety warning system for drivers.

At a high level, the logic is based on measuring two things:
1. Current speed
2. Distance to obstacles

These variables are evaluated to compute the Time-to-Collision (TTC). The result answers a straightforward question: "At the current speed, how much time remains until we hit something?"

## The Logic Flow

1. **Telemetry**: Distance and speed metrics are generated. Currently, this data originates from a software simulator (`serial_simulator.py`) acting as a proxy. Future iterations will interface with real telemetry hardware (ESP32 via `serial_reader.py`). The measurements are continuously written to a log file (`LOGS/live_data.txt`). The dashboard watches this file for rapid changes.
2. **Validation Checks**: To ensure software safety and reliability, data is evaluated to make sure sensors aren't failing and values are mathematically and physically reasonable.
3. **Risk Verification**: Based on the validated data, the system classifies safety states. If the TTC drops below 1.5 seconds, it returns a critical alert. Between 1.5 seconds and 3 seconds, it is marked as a warning. Everything above 3 seconds is considered safe.
4. **Dashboard**: The user interface (`dashboard.py`) processes these computations approximately every 0.6 seconds. It paints the corresponding alert state, trendlines of the previous minutes, and total warning occurrences.

## Modifying Configurations

Advanced parameters such as update rates, specific threshold limits, and simulator speeds are housed exclusively in `config.py`. Modifying these settings will dynamically alter the warning triggers and behavior.

It is normal for log files in `LOGS` to grow progressively large over session time. These files act as simple records and debug repositories. Should visual data clear, old logs can be deleted safely at your discretion.
