@echo off
echo Building fx451m-Calculator Android APK...
echo.

REM Check if buildozer is installed
buildozer version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: buildozer is not installed.
    echo Please install it with: pip install buildozer
    pause
    exit /b 1
)

echo Starting APK build process...
echo This may take several minutes on first run (downloading Android SDK/NDK)...
echo.

buildozer android debug

if %errorlevel% equ 0 (
    echo.
    echo Build completed successfully!
    echo APK location: bin\fx451mcalculator-1.0.0-debug.apk
    echo.
    echo To install on Android device:
    echo 1. Enable "Unknown Sources" in Settings ^> Security
    echo 2. Transfer the APK to your device
    echo 3. Open the APK file and install
) else (
    echo.
    echo Build failed. Check the output above for errors.
    echo Common solutions:
    echo - Delete .buildozer directory and try again
    echo - Ensure you have JDK 8+ installed
    echo - Check available disk space (need ~5GB)
)

pause