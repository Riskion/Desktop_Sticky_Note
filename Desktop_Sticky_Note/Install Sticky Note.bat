```bat
@echo off
setlocal
title Desktop Sticky Note - Installer
cd /d "%~dp0"

echo.
echo ============================================
echo       DESKTOP STICKY NOTE INSTALLER
echo ============================================
echo.

REM Check required application files
for %%F in ("note.py" "wolf.png" "Start Sticky Note.vbs" "start_sticky_note.bat") do (
    if not exist "%%~F" (
        echo ERROR: Missing file %%~F
        goto error
    )
)

echo [1/5] Checking Python...

where py >nul 2>&1
if errorlevel 1 (
    echo Python was not found.

    where winget >nul 2>&1
    if errorlevel 1 (
        echo Please install Python 3 from:
        echo https://www.python.org/downloads/
        goto error
    )

    echo Installing Python 3.14...
    winget install --id Python.Python.3.14 --exact --scope user --accept-package-agreements --accept-source-agreements

    if errorlevel 1 (
        echo Python installation failed.
        goto error
    )
)

where py >nul 2>&1
if errorlevel 1 (
    echo Python was installed but is not available yet.
    echo Restart this installer after opening a new window.
    goto error
)

echo.
echo [2/5] Installing Pillow...

py -3 -m pip install --user --upgrade Pillow
if errorlevel 1 (
    echo Pillow installation failed.
    goto error
)

echo.
echo [3/5] Preparing note data...

if not exist "note_data.json" (
    echo {}>"note_data.json"
)

echo.
echo [4/5] Creating desktop shortcut...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$folder=$env:USERPROFILE; $desktop=[Environment]::GetFolderPath('Desktop'); $shell=New-Object -ComObject WScript.Shell; $s=$shell.CreateShortcut((Join-Path $desktop 'Desktop Sticky Note.lnk')); $s.TargetPath=Join-Path '%~dp0' 'Start Sticky Note.vbs'; $s.WorkingDirectory='%~dp0'; $s.Description='Desktop Sticky Note'; $s.Save()"

if errorlevel 1 (
    echo Could not create the desktop shortcut.
    goto error
)

echo.
echo [5/5] Enabling startup with Windows...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$startup=[Environment]::GetFolderPath('Startup'); $shell=New-Object -ComObject WScript.Shell; $s=$shell.CreateShortcut((Join-Path $startup 'Desktop Sticky Note.lnk')); $s.TargetPath=Join-Path '%~dp0' 'Start Sticky Note.vbs'; $s.WorkingDirectory='%~dp0'; $s.Description='Start Desktop Sticky Note with Windows'; $s.Save()"

if errorlevel 1 (
    echo Could not enable automatic startup.
    goto error
)

echo.
echo ============================================
echo       INSTALLATION COMPLETED!
echo ============================================
echo.
echo Desktop shortcut created.
echo Automatic startup with Windows enabled.
echo.
echo Keep all application files together.
echo You can now open Desktop Sticky Note.
echo.
pause
exit /b 0

:error
echo.
echo INSTALLATION FAILED.
echo Correct the problem shown above and try again.
echo.
pause
exit /b 1
```