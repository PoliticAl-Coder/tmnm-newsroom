@echo off
setlocal
title TMNM Source Transport
cd /d "%~dp0"
echo TMNM existing source-result transport
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0TRANSPORT_EXISTING_RESULT.ps1"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo STATUS=PASS) else (echo STATUS=FAIL&echo EXIT_CODE=%RC%&(echo STATUS=FAIL&echo EXIT_CODE=%RC%)|clip)
echo.
echo This window will remain open so you can read the result.
pause
exit /b %RC%
