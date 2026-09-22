@echo off
setlocal
title TMNM MASTER384 READ-ONLY APPS SCRIPT INSPECTION
set "PY=C:\Users\USER\AppData\Local\TMNM\LocalWorker\.venv\Scripts\python.exe"
set "CRED=C:\Users\USER\AppData\Local\TMNM\ControlRoom\secrets\publisher_google_token.dpapi"
set "OUT=%LOCALAPPDATA%\TMNM\LocalWorker\state\tech_results_outbox\TMNM_MASTER384_APPS_SCRIPT_READONLY_RESULT.json"
if not exist "%PY%" (
  echo HOLD: LocalWorker Python not found.
  pause
  exit /b 2
)
"%PY%" -B "%~dp0tmnm_master384_readonly_inspector.py" --credential "%CRED%" --out "%OUT%" --persist-drive
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo PASS: Read-only Apps Script inspection completed and evidence persisted.) else (echo HOLD: No repair or reauthorisation attempted.)
echo Result is saved automatically. You do not need to retrieve it.
pause
exit /b %RC%
