@echo off
setlocal
cd /d "%~dp0.."

echo ============================================
echo  WisperLocal setup
echo ============================================
echo.

echo Creating virtual environment (.venv)...
py -3.12 -m venv .venv
if errorlevel 1 (
  echo   Python 3.12 launcher not found, trying default python...
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create the virtual environment. Is Python installed?
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing dependencies (this downloads the Whisper engine, may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo.
echo ============================================
echo  Setup complete.
echo  Start the app with:  scripts\run.bat
echo  (or double-click scripts\run-hidden.vbs for no console window)
echo ============================================
pause
