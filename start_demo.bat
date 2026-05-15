@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_demo.ps1" %*
if errorlevel 1 (
  echo.
  echo Demo launcher failed.
  pause
  exit /b %errorlevel%
)
