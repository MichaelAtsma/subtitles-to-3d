param(
    [switch]$SkipTests,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Virtual environment Python not found at $pythonExe"
}

Write-Host "Using Python:" $pythonExe

& $pythonExe -m pip install pyinstaller | Out-Host

if (-not $SkipTests) {
    & $pythonExe -m pytest -q tests | Out-Host
}

& $pythonExe -m PyInstaller --noconfirm subtitle_to_3d.spec | Out-Host

if ($SkipInstaller) {
    Write-Host "Installer build skipped."
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

& $isccExe (Join-Path $projectRoot "builds\installer\SubtitleTo3DAss.iss") | Out-Host
