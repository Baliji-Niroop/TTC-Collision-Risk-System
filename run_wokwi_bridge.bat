@echo off
setlocal

set ROOT_DIR=%~dp0
set PYTHON_EXE=%ROOT_DIR%ttc_env\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python environment not found at %PYTHON_EXE%
    exit /b 1
)

if "%WOKWI_SERIAL_WS_URL%"=="" if "%WOKWI_BRIDGE_SERIAL_OUT%"=="" if "%WOKWI_READER_PORT%"=="" (
    echo WARNING: No websocket URL or COM pair configured.
    echo Configure WOKWI_SERIAL_WS_URL for websocket mode, or set both WOKWI_BRIDGE_SERIAL_OUT and WOKWI_READER_PORT for a virtual COM pair.
)

set TTC_DASHBOARD_DEFAULT_MODE=Live Log

start "TTC Wokwi Bridge" /B "%PYTHON_EXE%" "%ROOT_DIR%bridge\wokwi_serial_bridge.py" --launch-stack

endlocal