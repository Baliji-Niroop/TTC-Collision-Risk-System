@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 goto setup_failed

echo.
echo ================================================================
echo   TTC Collision Risk Dashboard Launcher
echo ================================================================
echo.

set "VENV_DIR=%~dp0ttc_env"
set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -c "import pip._internal" >nul 2>nul
    if not errorlevel 1 (
        set "VENV_DIR=%~dp0.venv"
        set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"
    )
)

if not exist "%PYTHON_CMD%" (
    echo [1/4] Creating the project virtual environment ...
    where py >nul 2>nul
    if errorlevel 1 (
        where python >nul 2>nul
        if errorlevel 1 goto python_not_found
        python -m venv "%VENV_DIR%"
    ) else (
        py -3.12 -m venv "%VENV_DIR%"
        if errorlevel 1 py -3 -m venv "%VENV_DIR%"
    )
    if errorlevel 1 goto setup_failed
)

if not exist "%PYTHON_CMD%" goto setup_failed

"%PYTHON_CMD%" -c "import pip._internal" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] The existing virtual environment is incomplete.
    echo         Repair it or remove it, then run this launcher again.
    goto failed
)

"%PYTHON_CMD%" -c "import pip._internal, serial, websocket, pandas, numpy, streamlit.web.cli, streamlit_autorefresh, plotly, sklearn, joblib, matplotlib" >nul 2>nul
if errorlevel 1 (
    echo [2/4] Installing dashboard dependencies ...
    "%PYTHON_CMD%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 goto setup_failed
)

echo [2/4] Python environment is ready.
echo.

set "DASHBOARD_PORT="
for /f %%P in ('powershell -NoProfile -Command "$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LocalPort); foreach($port in 8501..8510){ if($listeners -notcontains $port){ Write-Output $port; exit 0 } }; exit 1"') do set "DASHBOARD_PORT=%%P"
if not defined DASHBOARD_PORT goto port_error

echo [3/4] Starting telemetry simulator ...
start "TTC Simulator" /D "%~dp0" "%PYTHON_CMD%" "%~dp0src\serial_simulator.py"
if errorlevel 1 goto launch_failed

echo       Simulator running in a separate window.
echo.
echo       Starting Streamlit dashboard ...
start "TTC Dashboard" /D "%~dp0" "%PYTHON_CMD%" -m streamlit run "%~dp0src\dashboard.py" --server.headless true --server.address 127.0.0.1 --server.port %DASHBOARD_PORT%
if errorlevel 1 goto launch_failed

echo       Waiting for the dashboard to become ready ...
set "WAIT_COUNT=0"

:wait_for_dashboard
powershell -NoProfile -Command "try { $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:%DASHBOARD_PORT%/_stcore/health' -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } } catch { }; exit 1" >nul 2>nul
if not errorlevel 1 goto dashboard_ready
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GEQ 30 goto dashboard_timeout
timeout /t 1 /nobreak >nul
goto wait_for_dashboard

:dashboard_ready
echo [4/4] Dashboard is ready at http://127.0.0.1:%DASHBOARD_PORT%
start "" "http://127.0.0.1:%DASHBOARD_PORT%"
echo.
echo   Dashboard : http://127.0.0.1:%DASHBOARD_PORT%
echo   Simulator : see the "TTC Simulator" terminal window
echo.
echo   Close the simulator and dashboard windows to stop the system.
echo ================================================================
echo.
if /i "%~1"=="--no-pause" exit /b 0
pause
exit /b 0

:dashboard_timeout
echo [ERROR] Dashboard did not become ready within 30 seconds.
echo         Check the "TTC Dashboard" terminal window for the error.
goto failed

:python_not_found
echo [ERROR] Python 3 was not found.
echo         Install Python 3 and ensure the Python Launcher or python.exe is on PATH.
goto failed

:launch_failed
echo [ERROR] Could not start the simulator or dashboard.
echo         Check the Python environment and try again.
goto failed

:port_error
echo [ERROR] Could not find an available dashboard port (8501-8510).
echo         Close another application using those ports and retry.
goto failed

:setup_failed
echo [ERROR] Could not create or prepare the Python environment.
echo         Check your Python installation and internet connection, then try again.

:failed
if /i "%~1"=="--no-pause" exit /b 1
echo.
pause
exit /b 1
