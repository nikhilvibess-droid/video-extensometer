@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  Video Extensometer - Release Build
echo  Publisher: Shaktikrupa Automation
echo ============================================================

cd /d "%~dp0\.."

if not exist ".\pyspin_env\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found: .\pyspin_env
    exit /b 1
)

if not exist ".\installer\redist\vc_redist.x64.exe" (
    echo [ERROR] Missing Visual C++ runtime package:
    echo         installer\redist\vc_redist.x64.exe
    echo.
    echo Download from:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    exit /b 1
)

echo.
echo [1/3] Installing build dependencies...
".\pyspin_env\Scripts\pip.exe" install --upgrade pyinstaller >nul
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    exit /b 1
)

echo [2/3] Building application with PyInstaller...
".\pyspin_env\Scripts\pyinstaller.exe" "installer\VideoExtensometer.spec" --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

set "ISCC="
for %%I in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) do (
    if exist %%~I set "ISCC=%%~I"
)

if "%ISCC%"=="" (
    echo.
    echo [WARN] Inno Setup Compiler was not found.
    echo        Open installer\VideoExtensometer.iss manually in Inno Setup.
    exit /b 0
)

echo [3/3] Compiling installer...
"%ISCC%" "installer\VideoExtensometer.iss"
if errorlevel 1 (
    echo [ERROR] Installer compilation failed.
    exit /b 1
)

echo.
echo Build complete:
echo   installer\output\VideoExtensometer_Setup.exe
exit /b 0
