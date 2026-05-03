@echo off
TITLE S.T.A.R.S. MATRIX Server
echo ===================================================
echo     STARTING S.T.A.R.S. MATRIX SYSTEM
echo ===================================================
echo.
echo 1. Ensure your phone and computer are on the SAME Wi-Fi.
echo 2. Wait for the message "S.T.A.R.S. MATRIX is running!" below.
echo 3. Open your browser to the Instructor Link shown.
echo.
echo Closing this window will stop the server.
echo.

cd /d "%~dp0"
echo Cleaning up old processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM cloudflared.exe /F >nul 2>&1
python start_server.py
pause
