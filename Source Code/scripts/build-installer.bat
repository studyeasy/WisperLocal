@echo off
cd /d "%~dp0.."

if not exist "dist\WisperLocal\WisperLocal.exe" (
  echo App not built yet. Run scripts\build.bat first.
  pause
  exit /b 1
)

set "ISCC="
where iscc >nul 2>nul && set "ISCC=iscc"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC (
  echo Inno Setup compiler ^(ISCC^) not found.
  echo Install it with:   winget install JRSoftware.InnoSetup
  pause
  exit /b 1
)

"%ISCC%" installer\WisperLocal.iss
if errorlevel 1 (
  echo Installer build failed.
  pause
  exit /b 1
)

echo.
echo Signing installer (skipped if no code-signing cert is present)...
for %%f in ("installer_output\WisperLocal-Setup-*.exe") do (
  powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\sign.ps1" "%%~ff"
)

echo.
echo Installer created in:  installer_output\
pause
