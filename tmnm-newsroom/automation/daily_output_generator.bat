@echo off
REM TMNM Daily Output Folder Generator
REM Usage: daily_output_generator.bat YYYY-MM-DD DeskName

if "%~1"=="" (
    echo Usage: %0 YYYY-MM-DD DeskName
    exit /b 1
)
if "%~2"=="" (
    echo Usage: %0 YYYY-MM-DD DeskName
    exit /b 1
)

set "ROOT=TMNM\Daily Output"
set "DATE=%~1"
set "DESK=%~2"

set "TARGET=%ROOT%\%DATE%\%DESK%"

mkdir "%TARGET%"
echo Created: %TARGET%
pause
