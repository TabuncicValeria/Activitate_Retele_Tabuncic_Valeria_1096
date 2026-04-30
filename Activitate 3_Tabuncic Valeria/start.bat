@echo off
title FTP Exercise - Start
cls

echo.
echo ======================================================
echo  FTP Exercise Starter
echo ======================================================
echo.
echo Starting server and client...
echo.

REM Start server in new window
echo [1/2] Starting FTP Server...
start "FTP Server" cmd /k python server.py

REM Wait a moment for server to start
timeout /t 2 /nobreak

REM Start client in new window
echo [2/2] Starting FTP Client...
start "FTP Client" cmd /k python client.py

echo.
echo ======================================================
echo  SUCCESS!
echo ======================================================
echo.
echo Server window:  "FTP Server"
echo Client window:  "FTP Client"
echo.
echo To stop: Run stop.bat
echo.
exit /b
