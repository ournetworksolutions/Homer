@echo off
schtasks /create /tn "Homer" /tr "wscript.exe \"C:\Homer\homer.vbs\"" /sc onlogon /ru "%USERNAME%" /rl HIGHEST
schtasks /run /tn "Homer"
schtasks /create /tn "OpenHardwareMonitor" /tr "wscript.exe \"C:\Homer\OpenHardwareMonitor\OpenHardwareMonitor.vbs\"" /sc onlogon /ru "%USERNAME%" /rl HIGHEST
schtasks /run /tn "OpenHardwareMonitor"
echo Task installed
pause
