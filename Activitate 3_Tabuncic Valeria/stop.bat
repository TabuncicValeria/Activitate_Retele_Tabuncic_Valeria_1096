@echo off
echo Se opresc procesele Python...
taskkill /f /im python.exe >nul 2>&1
echo Se inchid terminalele...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='cmd.exe' AND commandline LIKE '%%server.py%%'\" | Invoke-CimMethod -MethodName Terminate | Out-Null"
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='cmd.exe' AND commandline LIKE '%%client.py%%'\" | Invoke-CimMethod -MethodName Terminate | Out-Null"
echo Gata. Toate procesele au fost oprite.
exit /b
