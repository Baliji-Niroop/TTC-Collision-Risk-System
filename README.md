# TTC - Time-To-Collision Risk Prediction System

A clean, easy-to-understand collision risk prediction system that ingests sensor data, calculates time-to-collision (TTC), and displays real-time alerts on a dashboard.

## What This Does

- **Reads sensor data**: Distance, speed, and timing information from hardware or simulation
- **Calculates risk**: Determines time-to-collision and classifies danger level (safe, warning, critical)
- **Shows live dashboard**: Real-time visualization of vehicle status and alerts
- **Validates everything**: Built-in tests ensure data quality and system reliability

## Quick Start (5 minutes)

### Step 1: Set up Python environment

**On Windows (Command Prompt or PowerShell):**
```bat
python -m venv ttc_env
ttc_env\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r config/requirements.txt
```

**On Linux/Mac (Terminal):**
```bash
python -m venv ttc_env
source ttc_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r config/requirements.txt
```

### Step 2: Run the dashboard
```bash
run_dashboard.bat    # Windows
./run_dashboard.sh   # Linux/Mac (if script exists)
```

The dashboard will start with simulated vehicle data. You should see real-time metrics on your terminal or web interface.

## How It Works (Simple Overview)

```
Sensor Input → Validate Data → Calculate TTC → Classify Risk → Show Alert → Log Data
```

1. **Sensor Input**: Data comes from the vehicle (firmware), a simulator, or the Wokwi bridge
2. **Validate Data**: Ensures all 7 required fields are present and correct
3. **Calculate TTC**: Determines seconds until potential collision (distance ÷ speed)
4. **Classify Risk**: 
   - **CRITICAL**: TTC ≤ 1.5 seconds (stop immediately!)
   - **WARNING**: TTC ≤ 3.0 seconds (reduce speed)
   - **SAFE**: TTC > 3.0 seconds (normal operation)
5. **Show Alert**: Display on dashboard, LED, or other output
6. **Log Data**: Save for later review and analysis

## Data Format (Telemetry Contract)

The system always uses this 7-field format. Nothing more, nothing less:

```
timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence
```

- **timestamp_ms**: When the reading was taken (milliseconds)
- **distance_cm**: Distance to object ahead (centimeters)
- **speed_kmh**: Vehicle speed (kilometers per hour)
- **ttc_basic**: Basic time-to-collision calculation (seconds)
- **ttc_ext**: Extended TTC with sensor adjustments (seconds)
- **risk_class**: 0=safe, 1=warning, 2=critical
- **confidence**: How sure the system is (0.0 to 1.0)

Example valid data:
```
1700000000,150,50,10.8,10.2,0,0.95
1700000100,140,52,9.6,9.1,0,0.94
1700000200,100,60,6.0,5.5,1,0.92
```

## Testing & Validation

Run these checks to make sure everything works:

```bash
# Test the core protocol validation
python validation/protocol_contract_test.py

# Evaluate system with synthetic (fake) data
python validation/evaluate_synthetic.py

# Test the data bridge with manual input
echo "1000,120,30,2.40,2.20,2,0.85" | python bridge/wokwi_serial_bridge.py --source stdin --no-launch-stack
```

If all tests pass, the system is healthy.

## Project Structure (What Goes Where)

```
TTC/
├── src/                          # Main Python code
│   ├── dashboard.py              # Live display
│   ├── alerts.py                 # Alert system
│   ├── analytics.py              # Data analysis
│   ├── config.py                 # Settings (centralized)
│   ├── serial_reader.py          # USB communication
│   ├── serial_simulator.py       # Fake data for testing
│   ├── telemetry_schema.py       # Data format
│   └── validators.py             # Data validation
│
├── firmware/                     # Arduino/hardware code
│   ├── main.ino                  # Main program
│   ├── config/                   # Settings
│   ├── sensors/                  # Sensor drivers
│   ├── ml/                       # ML engine
│   └── alerts/                   # Alert outputs
│
├── bridge/                       # Wokwi simulator bridge
│   └── wokwi_serial_bridge.py
│
├── config/                       # System configuration
│   ├── requirements.txt          # Python packages
│   └── requirements-dev.txt      # Dev packages
│
├── docs/                         # Documentation
│   ├── README.md                 # Docs index
│   ├── serial_protocol.md        # Protocol spec
│   ├── wokwi_bridge_smoke_test.md # Simulator setup
│   ├── api/                      # API reference
│   └── guides/                   # How-to guides
│
├── validation/                   # Testing scripts
│   ├── protocol_contract_test.py # Verify data format
│   └── evaluate_synthetic.py     # Test with fake scenarios
│
├── tests/                        # Unit tests
├── LOGS/                         # Session recordings
├── MODELS/                       # Optional ML model
├── dataset/                      # Sample data
│
├── README.md                     # Main documentation
└── run_dashboard.bat             # Quick start
```

## Contributing

Want to make this better? Here's how:

### Setup for development
```bash
python -m venv ttc_env
source ttc_env/bin/activate      # or: ttc_env\Scripts\activate on Windows
pip install -r config/requirements-dev.txt
```

### Before submitting changes
1. Create a new branch from `main`
2. Keep your changes focused and small
3. Run validation tests:
   ```bash
   python validation/protocol_contract_test.py
   python validation/evaluate_synthetic.py
   ```
4. If you changed code behavior, add or update tests in `tests/`
5. Write a clear description of what you changed and why

### Key rules for contributors
- **Don't change the 7-field telemetry format** - other systems depend on it
- **Keep TTC thresholds in sync** between `src/config.py` and `firmware/config.h`
- **Don't hardcode thresholds** in feature code - read from config instead
- **Use shared validation** (`validators.py`, `telemetry_schema.py`) instead of custom parsing
- **Run all validation checks** before opening a pull request

## Troubleshooting

### "Protocol validation failed"
Run: `python validation/protocol_contract_test.py`
Check that your data has exactly 7 comma-separated fields in the right order.

### "ML model not found - using TTC thresholds"
This is normal! The system falls back to basic TTC calculation if `MODELS/ml_model.pkl` doesn't exist.

### "Wokwi connection failed"
On Windows with virtual COM ports: Make sure the bridge write port and reader port are different (e.g., COM5 and COM6).

### "Dashboard won't start"
1. Check Python version: `python --version` (need 3.10+)
2. Verify environment: `pip list | grep -E "rich|requests"` (should show installed packages)
3. Try manually: `python src/dashboard.py`

## Security & Community

- **Report security issues privately** - see [SECURITY.md](SECURITY.md) for details
- **Be respectful and inclusive** - see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## System Requirements

- **Python**: 3.10 or newer (3.11 recommended)
- **OS**: Windows, Linux, or macOS
- **RAM**: 512 MB minimum (1 GB recommended)
- **Disk**: ~50 MB for code and logs

## Architecture Details (For Deep Dives)

The system has five main stages:

1. **Data Source**
   - Firmware (real hardware)
   - Serial simulator (testing on PC)
   - Wokwi bridge (cloud simulation)

2. **Data Validation**
   - Check 7-field format
   - Verify ranges (speed ≥ 0, distance > 0)
   - Calculate checksums if needed

3. **Processing**
   - Ingest serial/log data
   - Calculate TTC and extended metrics
   - Apply sensor fusion

4. **Analysis & Alerts**
   - Trend detection
   - Risk escalation
   - Alert triggering

5. **Offline Validation**
   - Protocol compliance tests
   - Synthetic scenario evaluation
   - Session replay and analysis

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/config.py` | All system settings (thresholds, timeouts, etc) |
| `src/dashboard.py` | What you see on screen |
| `src/alerts.py` | When and how alerts trigger |
| `firmware/main.ino` | What runs on the vehicle |
| `firmware/config.h` | Hardware settings |
| `docs/serial_protocol.md` | Detailed protocol specification |

## Common Tasks

### See logs from last session
```bash
ls LOGS/
cat LOGS/session_*.csv | head -20
```

### Run only the simulator (no dashboard)
```bash
python src/serial_simulator.py
```

### Test with custom data
```bash
echo "1000,100,30,12,11.5,0,0.90" | python bridge/wokwi_serial_bridge.py --source stdin --no-launch-stack
```

### Check system health
```bash
python validation/protocol_contract_test.py && echo "✓ Protocol OK"
python validation/evaluate_synthetic.py && echo "✓ Synthetic test OK"
```

## Next Steps

1. **First time?** Run `run_dashboard.bat` to see it working
2. **Want to understand more?** Read `docs/README.md`
3. **Building something custom?** Check this README for system design
4. **Have ideas?** Open an issue or start contributing!

## Version Info

- **Current version**: 1.0
- **Last updated**: 2026
- **Status**: Active development

---

Questions? Found a bug? Have an idea? The best way is to:
- Check the docs in `/docs`
- Look at existing test cases in `tests/`
- Run validation scripts to check your environment
- Open an issue with clear steps to reproduce
