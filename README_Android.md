# fx451m-Calculator Android App

This is the Android version of the fx451m-Calculator, built with Kivy for mobile devices.

## Features

- **Basic Arithmetic:** Addition, subtraction, multiplication, division
- **Trigonometric Functions:** sin, cos, tan, cot and their inverses
- **Hyperbolic Functions:** sinh, cosh, tanh, coth and their inverses
- **Constants:** Pi (π) button
- **Modes:** Switch between Radians and Degrees
- **Mobile-Optimized UI:** Touch-friendly interface designed for mobile devices

## Building the APK

### Prerequisites

1. **Python 3.8+** installed
2. **Java JDK 8+** installed
3. **Android SDK and NDK** (Buildozer will download these automatically)
4. **Git** for cloning repositories

### Linux/Mac Setup (Recommended)

For the best experience, use Linux or macOS to build the APK. On Windows, you may encounter issues with the Android build tools.

### Build Instructions

1. **Install buildozer:**
   ```bash
   pip install buildozer
   ```

2. **Navigate to the project directory:**
   ```bash
   cd fx451m-Calculator
   ```

3. **Build the APK (debug version):**
   ```bash
   buildozer android debug
   ```

   This will:
   - Download Android SDK/NDK (first time only)
   - Compile Python dependencies
   - Create the APK file

4. **Find the APK:**
   The APK will be located at: `bin/fx451mcalculator-1.0.0-debug.apk`

### Alternative: Use Docker (Cross-Platform)

If you're on Windows or having issues, you can use Docker:

```bash
# Build the Docker image
docker build -t kivy-buildozer .

# Run the build
docker run -v $(pwd):/home/user/app kivy-buildozer buildozer android debug
```

## Installing on Android

1. **Enable Unknown Sources:**
   - Go to Settings > Security > Unknown Sources (enable)

2. **Transfer the APK:**
   - Copy the APK file to your Android device
   - Use a file manager or connect via USB

3. **Install:**
   - Open the APK file on your device
   - Follow the installation prompts

## Usage

- **Basic Calculations:** Tap numbers and operators, then "=" to calculate
- **Functions:** Enter a number, then tap a function button (sin, cos, etc.)
- **Mode Toggle:** Use the Rad/Deg buttons to switch between radians and degrees
- **Clear:** "C" clears everything, "CE" clears current entry
- **Pi:** "π" inserts the value of π (clears any existing number)

## Troubleshooting

### Common Issues

1. **Build fails with SDK/NDK errors:**
   - Delete the `.buildozer` directory and try again
   - Ensure you have sufficient disk space (at least 5GB free)

2. **Java version issues:**
   - Ensure JDK 8 or 11 is installed and JAVA_HOME is set correctly

3. **Permission denied errors:**
   - On Linux/Mac, you might need to run with sudo for some operations

### Buildozer Commands

```bash
# Clean build
buildozer android clean

# Update buildozer
buildozer update

# Get buildozer version
buildozer version
```

## Project Structure

```
fx451m-Calculator/
├── android_calculator.py    # Main Kivy app
├── buildozer.spec          # Build configuration
├── README_Android.md       # This file
└── ...other files
```

## Requirements

- Kivy
- Buildozer
- Android SDK/NDK (downloaded automatically)

## License

This project is licensed under the MIT License - see the LICENSE file for details.