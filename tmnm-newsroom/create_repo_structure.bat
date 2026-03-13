@echo off
REM TMNM Newsroom Repo Folder Scaffolding Script
REM Creates the canonical folder structure for the TMNM newsroom project

setlocal
set "ROOT=tmnm-newsroom"

REM Create main repo folder
mkdir "%ROOT%"

REM Create subfolders
mkdir "%ROOT%\characters"
mkdir "%ROOT%\prompts"
mkdir "%ROOT%\branding"
mkdir "%ROOT%\automation"
mkdir "%ROOT%\obs"
mkdir "%ROOT%\workflows"

echo TMNM newsroom folder structure created successfully.
endlocal
pause
