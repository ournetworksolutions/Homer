@echo off
setlocal

echo Removing scheduled task...
schtasks /end /tn "Homer"
schtasks /delete /tn "Homer" /f

if %errorlevel%==0 (
    echo.
    echo SUCCESS: Task removed.
) else (
    echo.
    echo FAILED to remove task.
)

schtasks /end /tn "OpenHardwareMonitor"
schtasks /delete /tn "OpenHardwareMonitor" /f

if %errorlevel%==0 (
    echo.
    echo SUCCESS: Task removed.
) else (
    echo.
    echo FAILED to remove task.
)

pause