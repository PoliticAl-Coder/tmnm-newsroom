@echo off
setlocal
title TMNM Acquisition
cd /d "%~dp0"
echo TMNM Batch D source acquisition
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ACQUIRE_1_1_SOURCE.ps1"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo STATUS=PASS
) else (
  echo STATUS=FAIL
  echo EXIT_CODE=%RC%
  (echo STATUS=FAIL&echo EXIT_CODE=%RC%) | clip
)
echo.
echo Result copied to clipboard on PASS.
echo This window will remain open so you can read the result.
echo.
pause
exit /b %RC%
