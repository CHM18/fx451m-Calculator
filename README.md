# fx451m-Calculator

A cross-platform scientific calculator built with Flet. The current app entry point is `main.py` and the same codebase runs on desktop and Android. The functionality and layout was inspired by the "CASIO Scientific Calculator fx-451M".

## Features

- Basic arithmetic
- Trigonometric and inverse trigonometric functions
- Hyperbolic and inverse hyperbolic functions
- Radian and degree modes
- Pi constant and clear functions
- Cross-platform UI with a single Python codebase

## Setup

1. Create a virtual environment:
  ```bash
  python -m venv .venv
  ```
2. Activate it:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
3. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Run on Desktop

```bash
python main.py
```

## Build Artifacts

Use the PowerShell build script to create the Windows EXE, the Android APK, or both in one run.

Build both targets:

```powershell
.\scripts\build-android-windows-exe.ps1
```

Build only the Windows EXE:

```powershell
.\scripts\build-android-windows-exe.ps1 -Targets windows
```

Build only the Android APK:

```powershell
.\scripts\build-android-windows-exe.ps1 -Targets android
```

Clean previous outputs first:

```powershell
.\scripts\build-android-windows-exe.ps1 -Clean
```

Notes:

- The script uses `fx_icon.png` as the source icon for the Windows EXE and generates `build/flutter/images/icon.ico` automatically.
- The Android toolchain bootstrap is invoked automatically from `scripts/setup-android-toolchain.ps1` when the Android target is selected.
- The Windows EXE is written to `dist/`.
- The Android APK is typically written under `build/apk/`.

## Android Toolchain and APK Build

For a predictable Windows setup, you can also provision Java and the Android SDK manually with the repo script below:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\setup-android-toolchain.ps1
```

This script installs a user-scoped JDK 17 and Android SDK, sets `JAVA_HOME`, `ANDROID_HOME`, and `ANDROID_SDK_ROOT`, updates the user `Path`, installs the required Android SDK components, and accepts SDK licenses.

If you prefer the direct Flet build flow for Android, run:

```bash
pip install flet
flet build apk
```

To regenerate the app icon artwork before building:

```bash
python scripts/generate_icon.py
```

The APK will appear in `build/apk/`. The first build downloads the Flutter SDK automatically (about 1 GB), so the initial run may take longer.

### Android install notes

1. Enable "Unknown sources" on the device.
2. Copy the APK to the phone via USB or file sharing.
3. Open the file and confirm the installation prompt.

### Troubleshooting

- First build is slow because the Flutter SDK is downloaded once.
- If the build fails, rerun with `flet build apk --no-rich-output` for fuller diagnostics.
- Make sure Python 3.9+ is installed and enough disk space is available for the toolchain and build artifacts.

## Requirements

- Python 3.9+
- Dependencies from `requirements.txt`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## To Do:
- write more unit tests
- add financial and statistical functions (extra switch)
- modern design system (e.g. metal borders, shadows...)