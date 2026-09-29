@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0DEPLOY_AND_VERIFY.ps1"
echo.
echo Result copied to clipboard. Window will remain open.
pause
