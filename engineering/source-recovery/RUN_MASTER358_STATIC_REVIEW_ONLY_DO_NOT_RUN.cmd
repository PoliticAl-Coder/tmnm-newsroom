@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "RC=2"
for /f %%I in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')"') do set "RID=%%I"
set "RESULT=%TEMP%\TMNM_MASTER358_RESULT_%RID%.txt"
set "PY=%LOCALAPPDATA%\TMNM\LocalWorker\.venv\Scripts\python.exe"

if not exist "%PY%" (
  >"%RESULT%" echo STATUS=FAIL
  >>"%RESULT%" echo PRIMARY_ERROR=INSTALLED_LOCALWORKER_PYTHON_NOT_FOUND
  set "RC=2"
  goto FINAL
)

"%PY%" "%~dp0acquire_and_transfer.py" "%RESULT%"
set "RC=%ERRORLEVEL%"

:FINAL
echo.
echo ================= TMNM FINAL RESULT =================
if exist "%RESULT%" (
  type "%RESULT%"
) else (
  echo STATUS=FAIL
  echo PRIMARY_ERROR=RESULT_FILE_UNAVAILABLE
  set "RC=4"
)
echo =====================================================

set "TMNM_RESULT_PATH=%RESULT%"
powershell -NoProfile -Command "$p=$env:TMNM_RESULT_PATH; try { if(-not $p){throw 'missing result path'}; Get-Content -LiteralPath $p -Raw | Set-Clipboard; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo CLIPBOARD=FAILED
) else (
  echo CLIPBOARD=PASS
)

echo RESULT_FILE=%RESULT%
echo Window will remain open for inspection.
pause
exit /b %RC%
