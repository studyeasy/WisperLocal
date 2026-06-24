@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\activate.bat" (
  echo Run scripts\setup.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"

echo Generating icon...
python tools\gen_icon.py

echo Building WisperLocal (this can take a few minutes)...
pyinstaller --noconfirm WisperLocal.spec
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo.
echo Done. App is in:  dist\WisperLocal\WisperLocal.exe
pause
