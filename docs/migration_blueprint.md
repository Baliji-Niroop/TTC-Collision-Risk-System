# Phase-2 Runtime-Safe Migration Blueprint

## Objective
Upgrade the repository from architecture anchors to industry-style runtime layout without breaking current launch paths.

## Current runtime truth
- Active Python runtime modules are in `src/`.
- Launch scripts and bridge stack currently invoke `src/dashboard.py`, `src/serial_reader.py`, and `src/serial_simulator.py`.
- Internal imports are mostly flat (`from config import ...`, `from logger import ...`).

This means direct bulk moves will break imports and script entrypoints unless staged.

## Migration strategy
Use a three-pass approach with backward-compatibility shims.

---

## Pass A: Move ML and shared helpers first

### A1. Create package scaffolding
- Add `python/__init__.py`.
- Add `ml/__init__.py`.

### A2. Move modules
- Move `src/ml_inference.py` -> `ml/inference.py`.
- Move low-risk shared modules to `python/`:
  - `src/analytics.py` -> `python/analytics.py`
  - `src/utils.py` -> `python/utils.py`

### A3. Add compatibility wrappers (critical)
Keep these files in `src/` as wrappers so old imports/scripts still work:
- `src/ml_inference.py`
- `src/analytics.py`
- `src/utils.py`

Wrapper pattern:
- `from ml.inference import *`
- `from python.analytics import *`
- `from python.utils import *`

### A4. Import rewrite scope
Update only modules that already consume moved files, for example:
- Anywhere importing `ml_inference` should eventually move to `from ml import inference` or `from ml.inference import ...`.
- Keep wrappers until all references are migrated and tests pass.

### A5. Verification gates
- `python validation/protocol_contract_test.py`
- Start simulator + dashboard
- Start bridge stack
- Confirm no import errors in startup logs

---

## Pass B: Move dashboard entrypoint safely

### B1. Move dashboard app
- Move `src/dashboard.py` -> `dashboard/dashboard.py`.

### B2. Keep `src/dashboard.py` wrapper
- Create `src/dashboard.py` as a tiny forwarding module that imports and runs dashboard app logic from `dashboard/dashboard.py`.

### B3. Streamlit launch compatibility
Keep old command working first:
- `streamlit run src/dashboard.py --server.headless true`

Then validate new command in parallel:
- `streamlit run dashboard/dashboard.py --server.headless true`

### B4. Verification gates
- Run both old and new commands.
- Validate Simulator, Live Log, and Serial modes.
- Verify bridge-launched dashboard path still works.

---

## Pass C: Move ingestion/runtime modules and switch scripts

### C1. Move ingestion modules
- `src/serial_reader.py` -> `python/serial_reader.py`
- `src/serial_simulator.py` -> `simulation/serial_simulator.py` (or `python/serial_simulator.py` if preferred)

### C2. Keep wrappers in `src/`
- `src/serial_reader.py` forwards to `python.serial_reader`
- `src/serial_simulator.py` forwards to new location

### C3. Update launchers and bridge
- Update `run_dashboard.bat` commands to new target paths.
- Update `run_wokwi_bridge.bat` if it invokes old entrypoints.
- Update `bridge/wokwi_serial_bridge.py` launch commands:
  - reader command path
  - dashboard command path

### C4. Deprecation window
Keep wrappers for one release cycle (or one milestone sprint) before deleting `src/` wrappers.

### C5. Verification gates
- One-click launcher works.
- Wokwi bridge stack works end-to-end.
- Serial reader writes session CSV and live log.
- Dashboard renders all modes without import/path errors.

---

## Exact move map (recommended)

### Pass A map
- `src/ml_inference.py` -> `ml/inference.py`
- `src/analytics.py` -> `python/analytics.py`
- `src/utils.py` -> `python/utils.py`

### Pass B map
- `src/dashboard.py` -> `dashboard/dashboard.py`

### Pass C map
- `src/serial_reader.py` -> `python/serial_reader.py`
- `src/serial_simulator.py` -> `simulation/serial_simulator.py`

---

## Script update matrix

### Scripts and modules to update in Pass C
- `run_dashboard.bat`
- `run_wokwi_bridge.bat`
- `bridge/wokwi_serial_bridge.py`

### Why these are critical
They currently reference `src/` paths directly, so this is the primary runtime-break risk.

---

## Rollback plan
If any pass fails:
1. Revert only that pass commit.
2. Keep previous wrappers and scripts untouched.
3. Re-run protocol and launch smoke tests.

Do not combine two passes in one commit.

---

## Commit plan
Use one commit per pass:
- Commit 1: Pass A move + wrappers + verification
- Commit 2: Pass B move + wrapper + verification
- Commit 3: Pass C move + script updates + verification

This preserves bisectability and simplifies emergency rollback.

---

## Exit criteria (migration complete)
- All launch scripts point to new package locations.
- No runtime imports depend on `src/` wrappers.
- Wrapper files removed from `src/`.
- Validation and launch smoke tests pass in final layout.
