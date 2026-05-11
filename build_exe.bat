@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0build_exe.ps1"
if errorlevel 1 (
    echo.
    echo Build failed.
    pause
    exit /b %errorlevel%
)

echo.
echo Build completed.
pause
