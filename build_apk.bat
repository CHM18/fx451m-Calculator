@echo off
setlocal

echo Setting up Android toolchain for fx451m-Calculator...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-android-toolchain.ps1"
if errorlevel 1 (
    echo.
    echo Android toolchain setup failed.
    pause
    exit /b 1
)

echo.
echo Building Android APK with Flet...
echo.

set "FLET_CMD=flet"
if exist "%~dp0.venv\Scripts\flet.exe" (
    set "FLET_CMD=%~dp0.venv\Scripts\flet.exe"
)

call "%FLET_CMD%" build apk
if errorlevel 1 (
    echo.
    echo APK build failed. Review the output above for the failing tool or package.
    echo If needed, rerun scripts\setup-android-toolchain.ps1 -Force and try again.
    pause
    exit /b 1
)

echo.
echo Build completed successfully.
echo APK output: build\apk\
pause