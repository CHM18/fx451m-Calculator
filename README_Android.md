# fx451m-Calculator Android App

This is the Android version of the fx451m-Calculator, built with **Flet** (Python).
It also runs on desktop (Windows/Mac/Linux) — the same `main.py` is used everywhere.

## Features

- **Basic Arithmetic:** Addition, subtraction, multiplication, division
- **Trigonometric Functions:** sin, cos, tan, cot and their inverses
- **Hyperbolic Functions:** sinh, cosh, tanh, coth and their inverses
- **Constants:** Pi (π) button
- **Modes:** Switch between Radians and Degrees
- **Cross-Platform:** Same code runs on desktop and Android

## Prerequisites

- **Python 3.9+**
- **Git**

Flet can bootstrap some Android build dependencies automatically, but for a predictable Windows setup you can provision Java and the Android SDK yourself with the repo script below.

## Windows Toolchain Setup

Run the setup script from the repo root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\setup-android-toolchain.ps1
```

The script installs a user-scoped JDK 17 and Android SDK, sets `JAVA_HOME`, `ANDROID_HOME`, and `ANDROID_SDK_ROOT`, updates the user `Path`, installs `platform-tools`, `platforms;android-35`, `build-tools;35.0.0`, and accepts SDK licenses.

## Run on Desktop

```bash
pip install flet
python main.py
```

## Build Android APK

```bash
pip install flet
flet build apk
```

If you want to rebuild the local toolchain from scratch, rerun the PowerShell script with `-Force`.

The APK will appear in the `build/apk/` folder.

The first build downloads the Flutter SDK automatically (~1 GB, one time only).

### Build Options

```bash
# Custom name and org
flet build apk --project "fx451m Calculator" --org org.fx451m

# Release build
flet build apk --no-rich-output
```

## Installing on Android

1. **Enable Unknown Sources:**
   - Go to Settings > Security > Unknown Sources (enable)

2. **Transfer the APK:**
   - Copy the APK file to your Android device via USB or file sharing

3. **Install:**
   - Open the APK file on your device and follow the prompts

## Usage

- **Basic Calculations:** Tap numbers and operators, then "=" to calculate
- **Functions:** Enter a number, then tap a function button (sin, cos, etc.)
- **Mode Toggle:** Use the Deg switch to toggle between radians and degrees
- **Clear:** "C" clears everything, "CE" clears current entry
- **Pi:** "π" inserts the value of π

## Troubleshooting

- **First build is slow:** Flutter SDK (~1 GB) is downloaded once. Subsequent builds are faster.
- **Build fails:** Run `flet build apk --no-rich-output` for full error output.
- **Python version:** Ensure Python 3.9+ is installed.
- **Disk space:** Need ~3 GB free for the Flutter SDK and build artifacts.

## Project Structure

```
fx451m-Calculator/
├── main.py                 # Flet app (desktop + Android)
├── requirements.txt        # Dependencies (flet only)
├── fx-451m-Calculator.py   # Original tkinter desktop version
├── README_Android.md       # This file
└── README.md
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.