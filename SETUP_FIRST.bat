@echo off
setlocal
cd /d "%~dp0"
echo ===== PuyoReview: First-time setup =====
echo.
where py >nul 2>&1
if errorlevel 1 goto no_python
py -3 -c "import sys; sys.exit(0 if (sys.version_info >= (3,12) and sys.maxsize > 2**32) else 1)" >nul 2>&1
if errorlevel 1 goto unsupported
for /f "delims=" %%V in ('py -3 -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'.'+str(sys.version_info.micro))"') do set "PYTHON_VERSION=%%V"
echo Python version: %PYTHON_VERSION%
py -3 -c "import sys; sys.exit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] Python %PYTHON_VERSION% is newer than Python 3.12.
    echo This version has not been fully verified with all dependencies.
    echo Setup will continue, but some libraries may fail to install or run.
    echo.
)
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,12) and sys.maxsize > 2**32 else 1)" >nul 2>&1
    if errorlevel 1 goto old_venv
) else (
    echo [1/3] Preparing a private Python environment...
    py -3 -m venv .venv
    if errorlevel 1 goto failed
)
echo [2/3] Installing libraries (Internet required)...
".venv\Scripts\python.exe" -m pip install -r requirements-windows.txt
if errorlevel 1 goto failed
echo [3/3] Checking libraries...
".venv\Scripts\python.exe" -c "import PIL, cv2, webview, clr; print('Libraries OK')"
if errorlevel 1 goto failed
echo.
echo Setup complete. Now open START_Analysis.bat.
pause
exit /b 0
:no_python
echo Python Launcher ('py') was not found.
echo Install 64-bit Python 3.12 or newer from https://www.python.org/downloads/
pause
exit /b 1
:unsupported
echo Python 3.11 or older, or a 32-bit Python, is not supported.
echo Please install Python 3.12 (64-bit) or newer.
echo Check installed versions with: py -0p
pause
exit /b 1
:old_venv
echo The existing .venv environment is incompatible.
echo Close the app, delete ONLY the .venv folder, and run SETUP_FIRST.bat again.
pause
exit /b 1
:failed
echo Installation failed. Check Internet and disk space, then try again.
echo If it still fails, send the displayed error to @istnpypy on X.
pause
exit /b 1
