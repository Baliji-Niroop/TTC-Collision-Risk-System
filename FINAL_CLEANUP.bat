@echo off
REM ================================================================
REM  TTC PROJECT FINAL COMPREHENSIVE CLEANUP
REM ================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ================================================================
echo   TTC PROJECT CLEANUP - COMPREHENSIVE REORGANIZATION
echo ================================================================
echo.

REM ===== PHASE 1: DELETE PYTHON CACHE =====
echo [PHASE 1] Deleting Python cache directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    echo   - Removing: %%d
    rd /s /q "%%d" 2>nul
)
echo   ^ü Done
echo.

REM ===== PHASE 2: DELETE PYTEST CACHE =====
echo [PHASE 2] Deleting pytest cache...
if exist ".pytest_cache\" (
    echo   - Removing: .pytest_cache\
    rd /s /q ".pytest_cache" 2>nul
)
echo   ^ü Done
echo.

REM ===== PHASE 3: DELETE BUILD ARTIFACTS =====
echo [PHASE 3] Deleting Arduino build artifacts...
if exist "build\" (
    echo   - Removing: build\
    rd /s /q "build" 2>nul
)
echo   ^ü Done
echo.

REM ===== PHASE 4: DELETE RUNTIME LOGS =====
echo [PHASE 4] Deleting runtime logs...
if exist "LOGS\live_data.txt" (
    echo   - Deleting: LOGS\live_data.txt
    del /q "LOGS\live_data.txt" 2>nul
)
if exist "LOGS\ttc_system.log" (
    echo   - Deleting: LOGS\ttc_system.log
    del /q "LOGS\ttc_system.log" 2>nul
)
echo   ^ü Done
echo.

REM ===== PHASE 5: DELETE TEST ARTIFACTS =====
echo [PHASE 5] Cleaning validation test artifacts...
if exist "validation\outputs\classification_report.txt" (
    del /q "validation\outputs\classification_report.txt" 2>nul
    echo   - Deleted: classification_report.txt
)
if exist "validation\outputs\confusion_matrix.png" (
    del /q "validation\outputs\confusion_matrix.png" 2>nul
    echo   - Deleted: confusion_matrix.png
)
if exist "validation\outputs\scenario_summary.png" (
    del /q "validation\outputs\scenario_summary.png" 2>nul
    echo   - Deleted: scenario_summary.png
)
if exist "validation\outputs\summary.json" (
    del /q "validation\outputs\summary.json" 2>nul
    echo   - Deleted: summary.json
)
if exist "validation\outputs\synthetic_predictions.csv" (
    del /q "validation\outputs\synthetic_predictions.csv" 2>nul
    echo   - Deleted: synthetic_predictions.csv
)
if exist "validation\outputs\timeline_summary.png" (
    del /q "validation\outputs\timeline_summary.png" 2>nul
    echo   - Deleted: timeline_summary.png
)
for /d /r validation\outputs %%d in (demo_evidence) do @if exist "%%d" (
    echo   - Removing: %%d
    rd /s /q "%%d" 2>nul
)
echo   ^ü Done
echo.

REM ===== PHASE 6: DELETE OLD CLEANUP SCRIPTS =====
echo [PHASE 6] Removing old cleanup scripts...
if exist "firmware\cleanup.bat" (
    echo   - Deleting: firmware\cleanup.bat
    del /q "firmware\cleanup.bat" 2>nul
)
if exist "firmware\cleanup.py" (
    echo   - Deleting: firmware\cleanup.py
    del /q "firmware\cleanup.py" 2>nul
)
if exist "firmware\do_cleanup.bat" (
    echo   - Deleting: firmware\do_cleanup.bat
    del /q "firmware\do_cleanup.bat" 2>nul
)
echo   ^ü Done
echo.

REM ===== PHASE 7: MOVE PROJECT_STRUCTURE.md =====
echo [PHASE 7] Moving PROJECT_STRUCTURE.md to docs/...
if exist "PROJECT_STRUCTURE.md" (
    if exist "docs\PROJECT_STRUCTURE.md" (
        echo   - File already in docs/, removing root copy
        del /q "PROJECT_STRUCTURE.md" 2>nul
    ) else (
        echo   - Moving PROJECT_STRUCTURE.md to docs/
        move "PROJECT_STRUCTURE.md" "docs\PROJECT_STRUCTURE.md" >nul 2>&1
    )
)
echo   ^ü Done
echo.

REM ===== PHASE 8: MOVE cleanup_project.bat to archive =====
echo [PHASE 8] Archiving cleanup_project.bat...
if exist "cleanup_project.bat" (
    if not exist "docs\archive" mkdir docs\archive
    echo   - Moving cleanup_project.bat to docs/archive/
    move "cleanup_project.bat" "docs\archive\cleanup_project.bat" >nul 2>&1
)
echo   ^ü Done
echo.

echo ================================================================
echo   CLEANUP COMPLETE!
echo ================================================================
echo.
echo Project is now cleaner and well-organized:
echo   - All Python caches removed
echo   - Build artifacts cleaned
echo   - Test outputs archived/deleted
echo   - Old cleanup scripts removed
echo   - Documentation centralized
echo.
echo Current directory structure is now production-ready.
echo.
pause
