@echo off
REM ================================================================
REM  TTC Project Cleanup & Organization Script
REM  Removes build artifacts, cache, and temp files
REM  Leaves source code, tests, docs, and config intact
REM ================================================================

cd /d "%~dp0"

echo.
echo ================================================================
echo   TTC Project Cleanup & Compaction
echo ================================================================
echo.

echo [1/6] Removing Python cache directories (__pycache__)...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    echo   Removing: %%d
    rd /s /q "%%d" 2>nul
)
echo       Done.
echo.

echo [2/6] Removing .pytest_cache directories...
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" (
    echo   Removing: %%d
    rd /s /q "%%d" 2>nul
)
echo       Done.
echo.

echo [3/6] Removing Arduino build artifacts...
if exist "build\" (
    echo   Removing: build\
    rd /s /q "build" 2>nul
)
echo       Done.
echo.

echo [4/6] Removing old cleanup scripts...
if exist "firmware\cleanup.py" del /q firmware\cleanup.py && echo   Removed: firmware\cleanup.py
if exist "firmware\cleanup.bat" del /q firmware\cleanup.bat && echo   Removed: firmware\cleanup.bat
if exist "firmware\do_cleanup.bat" del /q firmware\do_cleanup.bat && echo   Removed: firmware\do_cleanup.bat
echo       Done.
echo.

echo [5/6] Cleaning validation output artifacts...
if exist "validation\outputs" (
    for %%f in (validation\outputs\*) do (
        if "%%~xf"==".png" del /q "%%f" && echo   Removed: %%f
        if "%%~xf"==".json" del /q "%%f" && echo   Removed: %%f
        if "%%~xf"==".csv" del /q "%%f" && echo   Removed: %%f
    )
)
echo       Done.
echo.

echo [6/6] Verifying directory structure...
echo.
echo   Core directories:
if exist src echo   ✓ src/
if exist firmware echo   ✓ firmware/
if exist tests echo   ✓ tests/
if exist validation echo   ✓ validation/
if exist bridge echo   ✓ bridge/
if exist config echo   ✓ config/
if exist docs echo   ✓ docs/
if exist ml echo   ✓ ml/ (optional ML code)
echo.
echo   Runtime directories:
if exist LOGS echo   ✓ LOGS/
if exist MODELS echo   ✓ MODELS/
if exist dataset echo   ✓ dataset/
echo.
echo   System directories:
if exist .git echo   ✓ .git/
if exist .github echo   ✓ .github/
if exist .vscode echo   ✓ .vscode/
echo.

echo ================================================================
echo   Cleanup Complete!
echo ================================================================
echo.
echo   Project Size Reduction:
echo   - Removed: build artifacts, Python cache, cleanup scripts
echo   - Kept: All source code, tests, docs, configuration
echo   - Result: Project is now COMPACT and ready for distribution
echo.
echo   To optimize further:
echo   - Delete .venv\ and recreate with: python -m venv .venv
echo   - Then: .venv\Scripts\activate && pip install -r config\requirements.txt
echo.
pause
