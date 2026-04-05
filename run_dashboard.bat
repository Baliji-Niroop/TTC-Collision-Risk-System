@echo off
REM ================================================================
REM  TTC Collision Risk Dashboard — One-Click Launcher
REM  Starts the simulator + Streamlit dashboard + opens browser.
REM  Just double-click this file — it auto-navigates to the
REM  project root using its own location.
REM ================================================================

REM --- Navigate to the folder where this .bat file lives ----------
cd /d "%~dp0"

echo.
echo ================================================================
echo   TTC Collision Risk Dashboard Launcher
echo ================================================================
echo.

REM --- Pre-flight check: virtual environment ----------------------
if not exist "ttc_env\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo         Expected at: ttc_env\Scripts\activate.bat
    echo         Create it first:  python -m venv ttc_env
    echo.
    pause
    exit /b 1
)

REM --- Step 1: Activate the virtual environment -------------------
echo [1/4] Activating virtual environment ...
call ttc_env\Scripts\activate.bat
echo       Done.
echo.

REM --- Step 2: Launch the telemetry simulator in its own window ---
echo [2/4] Starting telemetry simulator ...
start "TTC Simulator" cmd /k "cd /d ""%~dp0"" && call ttc_env\Scripts\activate.bat && python src\serial_simulator.py"
echo       Simulator running in a separate window.
echo.

REM --- Step 3: Launch the Streamlit dashboard in its own window ---
echo [3/4] Launching Streamlit dashboard ...
start "TTC Dashboard" cmd /k "cd /d ""%~dp0"" && call ttc_env\Scripts\activate.bat && python -m streamlit run src\dashboard.py --server.headless true"
echo       Dashboard starting in a separate window.
echo.

REM --- Step 4: Wait, then open the browser ------------------------
echo      Waiting 3 seconds for the dashboard to initialise ...
timeout /t 3 /nobreak >nul

echo [4/4] Opening browser at http://localhost:8501 ...
start "" "http://localhost:8501"
echo.

echo ================================================================
echo   All systems running!
echo.
echo   Simulator  :  see the "TTC Simulator" terminal window
echo   Dashboard  :  see the "TTC Dashboard" terminal window
echo   Browser    :  http://localhost:8501
echo.
echo   To stop everything, close both terminal windows or
echo   press Ctrl+C inside each one.
echo ================================================================
echo.
pause
