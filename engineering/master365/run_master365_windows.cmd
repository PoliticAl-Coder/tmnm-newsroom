@echo off
setlocal EnableExtensions
set "RC=2"
set "BASE=%TEMP%\TMNM Master365 Results With Spaces"
if not exist "%BASE%" mkdir "%BASE%"
for /f %%G in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')"') do set "RUNID=%%G"
set "TMNM_RESULT_PATH=%BASE%\MASTER365_RESULT_%RUNID%.json"
set "TMNM_WIN_TEST_ROOT=%TEMP%\TMNM Master365 Work With Spaces\%RUNID%"
if exist "%TMNM_RESULT_PATH%" (
  echo STATUS=FAIL>"%TMNM_RESULT_PATH%"
  echo ERROR=STALE_RESULT_COLLISION>>"%TMNM_RESULT_PATH%"
  goto :finish
)
python "%~dp0windows_validate.py"
set "RC=%ERRORLEVEL%"
:finish
if not exist "%TMNM_RESULT_PATH%" (
  >"%TMNM_RESULT_PATH%" echo {"STATUS":"FAIL","ERROR":"RESULT_NOT_CREATED"}
  set "RC=2"
)
type "%TMNM_RESULT_PATH%"
powershell -NoProfile -Command "$p=$env:TMNM_RESULT_PATH; $x=Get-Content -LiteralPath $p -Raw; if($x -match 'TOPSECRET|SECONDSECRET|Bearer [A-Za-z0-9]'){exit 9}; Set-Clipboard -Value $x; $y=Get-Clipboard -Raw; if($y -ne $x){exit 8}"
if errorlevel 1 (
  echo CLIPBOARD=FAIL
  set "RC=2"
) else (
  echo CLIPBOARD=PASS
)
echo RESULT_FILE=%TMNM_RESULT_PATH%
echo Window will remain open for inspection.
pause
exit /b %RC%
