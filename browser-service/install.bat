@echo off
echo Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: pip install failed. Make sure Python is installed and in PATH.
    echo Download from https://www.python.org/downloads/ and check "Add to PATH".
    pause
    exit /b 1
)
echo.
echo Installing Chromium browser...
python -m playwright install chromium
echo.
echo Done! Now run login_weibo.bat or login_xhs.bat to log in.
pause
