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
echo   Process Finished. Check your 'Final Video' folder!
echo ========================================================
echo.
echo ********************************************************
echo   Enjoying typo Videos? Support the Creator:
echo   - Ko-fi : https://ko-fi.com/U4B028M2CY
echo   - GitHub: https://github.com/witrfaruk/TypoGraphy
echo ********************************************************
echo.
pause
