@echo off
title Kinetic Typography Auto-Folder Watcher
echo ========================================================
echo   KINETIC TYPOGRAPHY AUTO-FOLDER WATCHER
echo ========================================================
echo Watching Audio/ folder for new voice files...
echo.

set PYTHONPATH=%~dp0;%PYTHONPATH%
python "%~dp0run_pipeline.py" --watch

pause
