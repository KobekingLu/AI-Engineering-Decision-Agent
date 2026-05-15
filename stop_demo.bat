@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_demo.ps1" %*
if errorlevel 1 (
  echo.
  echo Demo stop failed.
  pause
  exit /b %errorlevel%
)
