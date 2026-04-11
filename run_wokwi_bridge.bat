@echo off
REM ================================================================
REM  TTC Wokwi Bridge Launcher
REM  Starts bridge + optional stack using either .venv or ttc_env.
REM ================================================================

cd /d "%~dp0"

echo.
echo ================================================================
echo   TTC Wokwi Bridge Launcher
echo ================================================================
echo.

set "VENV_ACTIVATE="
set "PYTHON_CMD="

if exist ".venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=.venv\Scripts\activate.bat"
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else if exist "ttc_env\Scripts\activate.bat" (
    set "VENV_ACTIVATE=ttc_env\Scripts\activate.bat"
    set "PYTHON_CMD=ttc_env\Scripts\python.exe"
) else (
    echo [ERROR] Virtual environment not found.
    echo         Checked: .venv\Scripts\activate.bat and ttc_env\Scripts\activate.bat
    echo         Create one first:  python -m venv .venv
    echo.
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment ...
call "%VENV_ACTIVATE%"
echo       Done.
echo.

if "%WOKWI_SERIAL_WS_URL%"=="" (
    echo [INFO] WOKWI_SERIAL_WS_URL is not set. Bridge will use stdin source.
)
if "%WOKWI_BRIDGE_SERIAL_OUT%"=="" (
    echo [INFO] WOKWI_BRIDGE_SERIAL_OUT is not set. COM forwarding disabled.
)
if "%WOKWI_READER_PORT%"=="" (
    echo [INFO] WOKWI_READER_PORT is not set. serial_reader launch may be skipped.
)
echo.

echo [2/3] Setting dashboard default mode to Live Log ...
set "TTC_DASHBOARD_DEFAULT_MODE=Live Log"
echo       Done.
echo.

echo [3/3] Starting bridge ...
"%PYTHON_CMD%" bridge\wokwi_serial_bridge.py --launch-stack
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] Bridge exited with code %EXIT_CODE%
) else (
    echo [OK] Bridge exited successfully.
)
pause
exit /b %EXIT_CODE%
