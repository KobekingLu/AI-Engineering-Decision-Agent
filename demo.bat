@echo off
setlocal
set "GEMMA_HOST=172.17.14.34"
if defined NO_PROXY (
  set "NO_PROXY=%NO_PROXY%,%GEMMA_HOST%"
) else (
  set "NO_PROXY=%GEMMA_HOST%"
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_demo.ps1" %*
if errorlevel 1 (
  echo.
  echo Demo launcher failed.
  pause
  exit /b %errorlevel%
)
