@echo off
REM Run the FLIR Video Extensometer using the correct virtual environment interpreter
REM This avoids execution policy issues with PowerShell script activation.
echo Starting FLIR Video Extensometer...
".\pyspin_env\Scripts\python.exe" main.py %*
