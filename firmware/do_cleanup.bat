@echo off
cd /d c:\Users\niroo\Downloads\TTC\firmware

echo === DELETING WRAPPER FILES ===
echo.

if exist config.h (
    del config.h
    echo Deleted: config.h
) else (
    echo Not found: config.h
)

if exist serial_protocol.h (
    del serial_protocol.h
    echo Deleted: serial_protocol.h
) else (
    echo Not found: serial_protocol.h
)

if exist sensors.h (
    del sensors.h
    echo Deleted: sensors.h
) else (
    echo Not found: sensors.h
)

if exist oled_display.h (
    del oled_display.h
    echo Deleted: oled_display.h
) else (
    echo Not found: oled_display.h
)

if exist risk_classifier.h (
    del risk_classifier.h
    echo Deleted: risk_classifier.h
) else (
    echo Not found: risk_classifier.h
)

if exist ttc_engine.h (
    del ttc_engine.h
    echo Deleted: ttc_engine.h
) else (
    echo Not found: ttc_engine.h
)

if exist sensors\kalman_filter.h (
    del sensors\kalman_filter.h
    echo Deleted: sensors\kalman_filter.h
) else (
    echo Not found: sensors\kalman_filter.h
)

echo.
echo === VERIFYING REMAINING .h FILES ===
echo.

echo firmware/ root:
dir /b *.h 2>nul || echo   (no .h files)
echo.

echo firmware/config/:
cd config
dir /b *.h 2>nul || echo   (no .h files)
cd ..
echo.

echo firmware/sensors/:
cd sensors
dir /b *.h 2>nul || echo   (no .h files)
cd ..
echo.

echo firmware/alerts/:
cd alerts
dir /b *.h 2>nul || echo   (no .h files)
cd ..
echo.

echo firmware/ml/:
cd ml
dir /b *.h 2>nul || echo   (no .h files)
cd ..
