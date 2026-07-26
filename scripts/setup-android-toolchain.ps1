[CmdletBinding()]
param(
    [string]$AndroidSdkRoot = "$env:LOCALAPPDATA\Android\Sdk",
    [string]$JavaInstallRoot = "$env:LOCALAPPDATA\Programs\Java",
    [int]$JdkMajorVersion = 17,
    [int]$PlatformApi = 35,
    [string]$BuildToolsVersion = "35.0.0",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)

    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Get-UniquePathEntries {
    param([string[]]$Entries)

    return $Entries |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { [System.IO.Path]::GetFullPath($_.Trim()) } |
        Select-Object -Unique
}

function Get-UserPathEntries {
    $rawPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ([string]::IsNullOrWhiteSpace($rawPath)) {
        return @()
    }

    return Get-UniquePathEntries -Entries ($rawPath -split ";")
}

function Set-UserPathEntries {
    param([string[]]$Entries)

    $uniqueEntries = Get-UniquePathEntries -Entries $Entries
    [Environment]::SetEnvironmentVariable("Path", ($uniqueEntries -join ";"), "User")
}

function Add-PathEntry {
    param([string]$PathEntry)

    $resolvedPath = [System.IO.Path]::GetFullPath($PathEntry)

    $userPathEntries = Get-UserPathEntries
    if ($userPathEntries -notcontains $resolvedPath) {
        Set-UserPathEntries -Entries ($userPathEntries + $resolvedPath)
    }

    $sessionPathEntries = Get-UniquePathEntries -Entries ($env:Path -split ";")
    if ($sessionPathEntries -notcontains $resolvedPath) {
        $env:Path = (($sessionPathEntries + $resolvedPath) -join ";")
    }
}

function Invoke-DownloadFile {
    param(
        [string]$Uri,
        [string]$DestinationPath
    )

    $destinationDirectory = Split-Path -Parent $DestinationPath
    if (-not (Test-Path $destinationDirectory)) {
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    }

    Invoke-WebRequest -Uri $Uri -OutFile $DestinationPath
}

function Get-LatestCommandLineToolsUri {
    Write-Step "Resolving latest Android command-line tools package"

    $repositoryXml = Invoke-WebRequest -Uri "https://dl.google.com/android/repository/repository2-1.xml" -UseBasicParsing
    $matches = [regex]::Matches($repositoryXml.Content, "commandlinetools-win-(\d+)_latest\.zip")

    if ($matches.Count -eq 0) {
        throw "Could not locate a Windows Android command-line tools package in Google's repository manifest."
    }

    $latestArchive = $matches |
        ForEach-Object {
            [PSCustomObject]@{
                Revision = [int64]$_.Groups[1].Value
                Name = $_.Value
            }
        } |
        Sort-Object Revision -Descending |
        Select-Object -First 1

    return "https://dl.google.com/android/repository/$($latestArchive.Name)"
}

function Test-JavaHomeVersion {
    param(
        [string]$JavaHome,
        [int]$RequiredMajorVersion
    )

    $releaseFile = Join-Path $JavaHome "release"
    if (-not (Test-Path $releaseFile)) {
        return $false
    }

    $javaVersionLine = Get-Content -Path $releaseFile | Where-Object { $_ -like 'JAVA_VERSION=*' } | Select-Object -First 1
    if (-not $javaVersionLine) {
        return $false
    }

    if ($javaVersionLine -match 'JAVA_VERSION="(?<version>[^\"]+)"') {
        $majorVersionText = ($Matches.version -split "\." | Select-Object -First 1)
        return ([int]$majorVersionText -ge $RequiredMajorVersion)
    }

    return $false
}

function Install-TemurinJdk {
    param(
        [string]$InstallRoot,
        [int]$RequiredMajorVersion,
        [bool]$Reinstall
    )

    $targetJavaHome = Join-Path $InstallRoot "jdk-$RequiredMajorVersion"
    if ((-not $Reinstall) -and (Test-JavaHomeVersion -JavaHome $targetJavaHome -RequiredMajorVersion $RequiredMajorVersion)) {
        Write-Step "Using existing JDK at $targetJavaHome"
        return $targetJavaHome
    }

    if (Test-Path $targetJavaHome) {
        Remove-Item -Path $targetJavaHome -Recurse -Force
    }

    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null

    $temporaryRoot = Join-Path $env:TEMP ("fx451m-java-" + [guid]::NewGuid().ToString())
    $archivePath = Join-Path $temporaryRoot "jdk.zip"

    try {
        New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null

        Write-Step "Downloading Temurin JDK $RequiredMajorVersion"
        $jdkUri = "https://api.adoptium.net/v3/binary/latest/$RequiredMajorVersion/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk&image_type=jdk&package_type=zip"
        Invoke-DownloadFile -Uri $jdkUri -DestinationPath $archivePath

        Write-Step "Extracting JDK"
        Expand-Archive -Path $archivePath -DestinationPath $temporaryRoot -Force

        $extractedDirectory = Get-ChildItem -Path $temporaryRoot -Directory |
            Where-Object { $_.Name -like 'jdk*' } |
            Select-Object -First 1

        if (-not $extractedDirectory) {
            throw "The downloaded JDK archive did not contain a JDK directory."
        }

        Move-Item -Path $extractedDirectory.FullName -Destination $targetJavaHome
        return $targetJavaHome
    }
    finally {
        if (Test-Path $temporaryRoot) {
            Remove-Item -Path $temporaryRoot -Recurse -Force
        }
    }
}

function Install-AndroidCommandLineTools {
    param(
        [string]$SdkRoot,
        [bool]$Reinstall
    )

    $sdkManagerPath = Join-Path $SdkRoot "cmdline-tools\latest\bin\sdkmanager.bat"
    if ((-not $Reinstall) -and (Test-Path $sdkManagerPath)) {
        Write-Step "Using existing Android command-line tools"
        return $sdkManagerPath
    }

    $temporaryRoot = Join-Path $env:TEMP ("fx451m-android-sdk-" + [guid]::NewGuid().ToString())
    $archivePath = Join-Path $temporaryRoot "commandlinetools.zip"
    $toolsTargetRoot = Join-Path $SdkRoot "cmdline-tools"
    $toolsTargetPath = Join-Path $toolsTargetRoot "latest"

    try {
        New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
        New-Item -ItemType Directory -Path $SdkRoot -Force | Out-Null

        $commandLineToolsUri = Get-LatestCommandLineToolsUri
        Write-Step "Downloading Android command-line tools"
        Invoke-DownloadFile -Uri $commandLineToolsUri -DestinationPath $archivePath

        Write-Step "Extracting Android command-line tools"
        Expand-Archive -Path $archivePath -DestinationPath $temporaryRoot -Force

        $extractedToolsPath = Join-Path $temporaryRoot "cmdline-tools"
        if (-not (Test-Path $extractedToolsPath)) {
            throw "The Android command-line tools archive did not contain the expected cmdline-tools directory."
        }

        New-Item -ItemType Directory -Path $toolsTargetRoot -Force | Out-Null
        
        # Clean up any existing cmdline-tools versions (latest, latest-1, latest-2, etc.)
        # to avoid SDK inconsistency warnings
        Get-ChildItem -Path $toolsTargetRoot -Directory -ErrorAction SilentlyContinue | 
            Where-Object { $_.Name -like "latest*" } |
            ForEach-Object { Remove-Item -Path $_.FullName -Recurse -Force }

        Move-Item -Path $extractedToolsPath -Destination $toolsTargetPath
        return (Join-Path $toolsTargetPath "bin\sdkmanager.bat")
    }
    finally {
        if (Test-Path $temporaryRoot) {
            Remove-Item -Path $temporaryRoot -Recurse -Force
        }
    }
}

function Set-UserEnvironmentVariable {
    param(
        [string]$Name,
        [string]$Value
    )

    [Environment]::SetEnvironmentVariable($Name, $Value, "User")
    Set-Item -Path "Env:$Name" -Value $Value
}

function Get-RequiredAndroidSdkPaths {
    param(
        [string]$SdkRoot,
        [string]$JavaHome,
        [int]$PlatformApi,
        [string]$BuildToolsVersion
    )

    return @(
        (Join-Path $SdkRoot "platform-tools"),
        (Join-Path $SdkRoot "platforms\android-$PlatformApi"),
        (Join-Path $SdkRoot "build-tools\$BuildToolsVersion"),
        (Join-Path $JavaHome "bin\java.exe")
    )
}

function Get-MissingPaths {
    param([string[]]$Paths)

    return @($Paths | Where-Object { -not (Test-Path $_) })
}

function Test-SdkManagerRemoteFailure {
    param([string]$ErrorText)

    return $ErrorText -match "ProductDetails\$CpuArchitecture"
}

function Invoke-SdkManagerWithYInput {
    param(
        [string]$SdkManager,
        [string]$SdkRoot,
        [string[]]$Arguments
    )

    $output = (1..200 | ForEach-Object { "y" }) | & $SdkManager "--sdk_root=$SdkRoot" @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    return [PSCustomObject]@{
        Output = @($output)
        ExitCode = $exitCode
    }
}

Write-Step "Installing Java"
$javaHome = Install-TemurinJdk -InstallRoot $JavaInstallRoot -RequiredMajorVersion $JdkMajorVersion -Reinstall:$Force.IsPresent

Write-Step "Installing Android SDK command-line tools"
$sdkManager = Install-AndroidCommandLineTools -SdkRoot $AndroidSdkRoot -Reinstall:$Force.IsPresent

Write-Step "Persisting environment variables"
Set-UserEnvironmentVariable -Name "JAVA_HOME" -Value $javaHome
Set-UserEnvironmentVariable -Name "ANDROID_HOME" -Value $AndroidSdkRoot
Set-UserEnvironmentVariable -Name "ANDROID_SDK_ROOT" -Value $AndroidSdkRoot

Add-PathEntry -PathEntry (Join-Path $javaHome "bin")
Add-PathEntry -PathEntry (Join-Path $AndroidSdkRoot "cmdline-tools\latest\bin")
Add-PathEntry -PathEntry (Join-Path $AndroidSdkRoot "platform-tools")

$packages = @(
    "cmdline-tools;latest",
    "platform-tools",
    "platforms;android-$PlatformApi",
    "build-tools;$BuildToolsVersion"
)

$expectedPaths = Get-RequiredAndroidSdkPaths -SdkRoot $AndroidSdkRoot -JavaHome $javaHome -PlatformApi $PlatformApi -BuildToolsVersion $BuildToolsVersion
$missingPaths = @(Get-MissingPaths -Paths $expectedPaths)

if ($missingPaths.Count -eq 0) {
    Write-Step "Required Android SDK packages already installed; skipping remote sdkmanager operations"
}
else {
    Write-Step "Accepting Android SDK licenses"
    $licenseResult = Invoke-SdkManagerWithYInput -SdkManager $sdkManager -SdkRoot $AndroidSdkRoot -Arguments @("--licenses")
    if ($licenseResult.ExitCode -ne 0) {
        $licenseErrorText = ($licenseResult.Output -join [Environment]::NewLine)
        if (Test-SdkManagerRemoteFailure -ErrorText $licenseErrorText) {
            throw (
                "Android cmdline-tools remote operations are currently broken on this machine: sdkmanager failed with " +
                "ProductDetails`$CpuArchitecture while loading the remote repository. " +
                "The required SDK packages are also missing:`n$($missingPaths -join "`n")`n`n" +
                "Workaround: install the missing SDK components via Android Studio's SDK Manager or another working sdkmanager, then rerun this script."
            )
        }

        throw "Failed while accepting Android SDK licenses.`n$licenseErrorText"
    }

    Write-Step "Installing Android SDK packages"
    $installResult = Invoke-SdkManagerWithYInput -SdkManager $sdkManager -SdkRoot $AndroidSdkRoot -Arguments $packages
    if ($installResult.ExitCode -ne 0) {
        $installErrorText = ($installResult.Output -join [Environment]::NewLine)
        if (Test-SdkManagerRemoteFailure -ErrorText $installErrorText) {
            throw (
                "Android cmdline-tools remote operations are currently broken on this machine: sdkmanager failed with " +
                "ProductDetails`$CpuArchitecture while loading the remote repository. " +
                "The required SDK packages are still missing:`n$($missingPaths -join "`n")`n`n" +
                "Workaround: install the missing SDK components via Android Studio's SDK Manager or another working sdkmanager, then rerun this script."
            )
        }

        throw "Failed while installing Android SDK packages.`n$installErrorText"
    }
}
$missingPaths = @(Get-MissingPaths -Paths $expectedPaths)
if ($missingPaths.Count -gt 0) {
    throw "Android setup completed with missing expected paths:`n$($missingPaths -join "`n")"
}

Write-Host "`nAndroid toolchain setup completed successfully." -ForegroundColor Green
Write-Host "JAVA_HOME        = $javaHome"
Write-Host "ANDROID_SDK_ROOT = $AndroidSdkRoot"
Write-Host "Installed API    = android-$PlatformApi"
Write-Host "Build tools      = $BuildToolsVersion"
Write-Host "`nOpen a new PowerShell window for persistent PATH updates, or continue in this session."
Write-Host "Next build command: flet build apk"