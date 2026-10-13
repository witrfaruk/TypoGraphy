@echo off
title Kinetic Typography Video Generator
echo ========================================================
echo   KINETIC TYPOGRAPHY VIDEO GENERATOR
echo ========================================================
echo Scanning Audio/ folder for voice recordings...
echo.

set PYTHONPATH=%~dp0code;%PYTHONPATH%
python "%~dp0code\run_pipeline.py" %*

echo.
echo ========================================================
echo Process Finished. Check your 'Final Video' folder!
echo ========================================================
pause
