param(
    [switch]$SkipTests,
    [switch]$SkipInstaller,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $false)]
        [string[]]$Arguments = @()
    )

    & $Command @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvCandidates = @(
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path (Split-Path -Parent $projectRoot) ".venv\Scripts\python.exe")
)

$pythonExe = $venvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $pythonExe) {
    throw "Virtual environment Python not found. Checked: $($venvCandidates -join ', ')"
}

Write-Host "Using Python:" $pythonExe

Invoke-CheckedCommand -Command $pythonExe -Arguments @("-m", "pip", "install", "-r", "requirements.txt")
Invoke-CheckedCommand -Command $pythonExe -Arguments @("-m", "pip", "install", "pyinstaller")
Invoke-CheckedCommand -Command $pythonExe -Arguments @("-c", "import PyQt6, pysubs2, cv2, PyInstaller; print('Build environment OK: all required modules are importable.')")

if (-not $SkipTests) {
    Invoke-CheckedCommand -Command $pythonExe -Arguments @("-m", "pytest", "-q", "tests")
}

if ($OneFile) {
    Write-Host "Building one-file executable (non-spec mode)..."
    Invoke-CheckedCommand -Command $pythonExe -Arguments @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "SubtitleTo3D-0.1.0",
        "--icon", "src/gui/assets/app_icon.ico",
        "--add-data", "src/gui/assets/app_icon.png;src/gui/assets",
        "--add-data", "src/gui/assets/app_icon.ico;src/gui/assets",
        "--add-data", "src/gui/assets/splash.png;src/gui/assets",
        "main.py"
    )
} else {
    Invoke-CheckedCommand -Command $pythonExe -Arguments @("-m", "PyInstaller", "--noconfirm", "subtitle_to_3d.spec")
}

if ($SkipInstaller) {
    Write-Host "Installer build skipped."
    exit 0
}

if ($OneFile) {
    Write-Host "Installer build skipped for one-file mode."
    Write-Host "The current Inno Setup script expects the folder build output."
    exit 0
}

$isccCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$isccExe = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $isccExe) {
    Write-Host "Inno Setup was not found. EXE build is complete, but installer was not created."
    Write-Host "Install Inno Setup 6 and run build_exe.ps1 again to generate the installer."
    exit 0
}

Invoke-CheckedCommand -Command $isccExe -Arguments @((Join-Path $projectRoot "builds\installer\SubtitleTo3DAss.iss"))
