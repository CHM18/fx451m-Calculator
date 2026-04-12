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
\.\scripts\build-windows-exe.ps1
```

Build only the Windows EXE:

```powershell
.\scripts\build-windows-exe.ps1 -Targets windows
```

Build only the Android APK:

```powershell
.\scripts\build-windows-exe.ps1 -Targets android
```

Clean previous outputs first:

```powershell
.\scripts\build-windows-exe.ps1 -Clean
```

Notes:

- The script uses `fx_icon.png` as the source icon for the Windows EXE and generates `build/flutter/images/icon.ico` automatically.
- The Android toolchain bootstrap is invoked automatically from `scripts/setup-android-toolchain.ps1` when the Android target is selected.
- The Windows EXE is written to `dist/`.
- The Android APK is typically written under `build/apk/`.

See [README_Android.md](README_Android.md) for additional Android-specific background.

## Requirements

- Python 3.9+
- Dependencies from `requirements.txt`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## To Do:
- write unit tests
- add financial and statistical functions (extra switch)
- add log, ln, e^x and x!