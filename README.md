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

## Build Android APK

See [README_Android.md](README_Android.md) for Android-specific instructions.

On Windows, you can provision Java and the Android SDK with:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\setup-android-toolchain.ps1
```

Then build the APK with:

```bash
flet build apk
```

The generated APK is written to `build/apk/`.

## Requirements

- Python 3.9+
- Dependencies from `requirements.txt`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.