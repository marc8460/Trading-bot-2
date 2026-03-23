@echo off
REM ================================================
REM PropOS — Windows Startup Script
REM ================================================
REM Place this file in the project root.
REM Double-click to start PropOS, or use Task Scheduler.
REM ================================================

echo ================================================
echo   PropOS — Multi-Account Prop Trading OS
echo ================================================
echo.

cd /d "%~dp0"

REM Activate virtualenv
call venv\Scripts\activate.bat

REM Set Python path
set PYTHONPATH=.

REM Create data directory if missing
if not exist "data" mkdir data

echo Starting PropOS backend...
echo.

python -m backend.main

REM If the server exits, pause to show errors
echo.
echo PropOS has stopped. Press any key to exit.
pause
