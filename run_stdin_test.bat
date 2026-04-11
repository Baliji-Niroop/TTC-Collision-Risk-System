@echo off
cd /d "c:\Users\niroo\Downloads\TTC"
echo Running Wokwi bridge test with canonical packet...
echo.
(echo 1000,120,30,2.40,2.20,2,0.85) | python bridge/wokwi_serial_bridge.py --source stdin --no-launch-stack
echo.
echo.
echo Checking LOGS directory...
if exist LOGS\live_data.txt (
    echo.
    echo LOGS/live_data.txt contents:
    type LOGS\live_data.txt
) else (
    echo LOGS/live_data.txt not found
)
echo.
echo Test completed.
