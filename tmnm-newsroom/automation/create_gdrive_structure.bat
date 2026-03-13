@echo off
REM TMNM Google Drive Local Mirror Folder Scaffolding Script
REM Creates a local mirror of the Google Drive folder structure for TMNM

setlocal
set "ROOT=TMNM"

REM Create main Google Drive folder
mkdir "%ROOT%"

REM Create subfolders
mkdir "%ROOT%\Avatars"
mkdir "%ROOT%\Studios"
mkdir "%ROOT%\Graphics"
mkdir "%ROOT%\Daily Output"
mkdir "%ROOT%\Ready To Post"

echo TMNM Google Drive local folder structure created successfully.
endlocal
pause
