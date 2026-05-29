[CmdletBinding()]
param(
    [string[]]$Targets = @("windows", "android"),
    [string]$AppName = "fx451m-Calculator",
    [string]$EntryPoint = "main.py",
    [string]$IconPng = "fx_icon.png",
    [string]$IconIco = "build/flutter/images/icon.ico",
    [switch]$NoIcon,
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$validTargets = @("windows", "android")
$targetSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($target in $Targets) {
    if ($validTargets -notcontains $target) {
        throw "Unsupported target '$target'. Supported values: windows, android"
    }
    $null = $targetSet.Add($target)
}

$buildWindows = $targetSet.Contains("windows")
$buildAndroid = $targetSet.Contains("android")
if (-not $buildWindows -and -not $buildAndroid) {
    throw "No build targets were selected."
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Get-PythonCommand {
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    throw "Python was not found. Create .venv or install Python and ensure it is in PATH."
}

function Get-FletCommand {
    $venvFlet = Join-Path $repoRoot ".venv\Scripts\flet.exe"
    if (Test-Path $venvFlet) {
        return $venvFlet
    }

    $fletCmd = Get-Command flet -ErrorAction SilentlyContinue
    if ($fletCmd) {
        return $fletCmd.Source
    }

    throw "Flet CLI was not found. Install dependencies in the active environment so the 'flet' command is available."
}

$pythonExe = Get-PythonCommand
$fletExe = Get-FletCommand

if (-not (Test-Path $EntryPoint)) {
    throw "Entry point not found: $EntryPoint"
}

if ($Clean) {
    Write-Step "Removing previous build outputs"
    foreach ($path in @("build", "dist")) {
        if (Test-Path $path) {
            Remove-Item -Path $path -Recurse -Force
        }
    }
}

if ($buildWindows) {
    Write-Step "Ensuring PyInstaller is installed"
    & $pythonExe -m pip install --upgrade pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install or upgrade PyInstaller."
    }

    $iconArg = $null
    if (-not $NoIcon) {
        if (-not (Test-Path $IconPng)) {
            throw "PNG icon not found: $IconPng"
        }

        Write-Step "Generating ICO from PNG"
        $iconScript = @"
from PIL import Image
from pathlib import Path

src = Path(r\"$IconPng\")
dst = Path(r\"$IconIco\")
dst.parent.mkdir(parents=True, exist_ok=True)
img = Image.open(src)
img.save(dst, sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
print(f\"Wrote {dst}\")
"@

        & $pythonExe -c $iconScript
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create ICO from PNG icon."
        }

        $iconArg = (Resolve-Path $IconIco).Path
    }

    Write-Step "Building standalone EXE with PyInstaller"
    $pyInstallerArgs = @(
        "--onefile",
        "--windowed",
        "--name", $AppName
    )

    if ($iconArg) {
        $pyInstallerArgs += @("--icon", $iconArg)
        # Include the ICO file as bundled data so the running app can access it (onefile/_MEIPASS)
        # Use PyInstaller data syntax: <SRC>;<DEST> (Windows uses ';' separator)
        $addDataArg = "$iconArg;." 
        $pyInstallerArgs += @("--add-data", $addDataArg)
    }

        # Create a Windows version resource file so Task Manager shows a proper File Description
        $versionDir = Join-Path $repoRoot "build"
        if (-not (Test-Path $versionDir)) { New-Item -Path $versionDir -ItemType Directory | Out-Null }
        $versionFile = Join-Path $versionDir "version.txt"
        $versionContent = @"
# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(0,1,0,0),
        prodvers=(0,1,0,0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0,0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                '040904b0',
                [
                    StringStruct('CompanyName', ''),
                    StringStruct('FileDescription', 'fx451m Calculator'),
                    StringStruct('FileVersion', '0.1.0'),
                    StringStruct('InternalName', "$AppName"),
                    StringStruct('OriginalFilename', "$AppName.exe"),
                    StringStruct('ProductName', 'fx451m Calculator'),
                    StringStruct('ProductVersion', '0.1.0')
                ]
            )
        ]),
        VarFileInfo([VarStruct('Translation', [0x0409, 1200])])
    ]
)
"@
        Set-Content -Path $versionFile -Value $versionContent -Encoding UTF8
        $pyInstallerArgs += @("--version-file", $versionFile)

    $pyInstallerArgs += $EntryPoint

    & $pythonExe -m PyInstaller @pyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }

    $exePath = Join-Path $repoRoot "dist\$AppName.exe"
    if (Test-Path $exePath) {
        Write-Host "EXE: $exePath" -ForegroundColor Green
    } else {
        throw "Build finished but EXE was not found at $exePath"
    }
}

if ($buildAndroid) {
    $androidSetupScript = Join-Path $repoRoot "scripts\setup-android-toolchain.ps1"
    if (-not (Test-Path $androidSetupScript)) {
        throw "Android setup script not found: $androidSetupScript"
    }

    Write-Step "Preparing Android toolchain"
    & $androidSetupScript
    if ($LASTEXITCODE -ne 0) {
        throw "Android toolchain setup failed."
    }

    Write-Step "Refreshing custom icon assets"
    & $pythonExe scripts/generate_icon.py
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to regenerate custom icon assets."
    }

    Write-Step "Building Android APK with Flet"
    & $fletExe build apk
    if ($LASTEXITCODE -ne 0) {
        throw "Android APK build failed. Check the Flet output above for the concrete Flutter/Android error."
    }

    # Kill Gradle daemon and any lingering Java/SDK processes that might hang
    Write-Step "Cleaning up Android build processes"
    Get-Process -Name "java" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "sdkmanager" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "gradle*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    $apkCandidates = @()
    if (Test-Path "build\apk") {
        $apkCandidates += Get-ChildItem -Path "build\apk" -Filter "*.apk" -Recurse -File
    }

    if ($apkCandidates.Count -eq 0 -and (Test-Path "build\flutter\build")) {
        $apkCandidates += Get-ChildItem -Path "build\flutter\build" -Filter "*.apk" -Recurse -File
    }

    if ($apkCandidates.Count -gt 0) {
        foreach ($apk in ($apkCandidates | Select-Object -Unique FullName)) {
            Write-Host "APK: $($apk.FullName)" -ForegroundColor Green
        }
    } else {
        Write-Host "APK build completed, but no .apk file was found in expected output folders." -ForegroundColor Yellow
    }
}

Write-Step "Build completed"
