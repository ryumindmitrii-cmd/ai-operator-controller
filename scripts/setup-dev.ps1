[CmdletBinding()]
param(
    [string]$Python = "python",
    [switch]$SkipPipUpgrade
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

Push-Location $RepoRoot
try {
    if (-not (Test-Path $VenvPython)) {
        Write-Host "Creating local virtual environment..."
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            throw "venv creation failed with exit code $LASTEXITCODE"
        }
    }

    if (-not $SkipPipUpgrade) {
        Write-Host "Upgrading pip..."
        & $VenvPython -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) {
            throw "pip upgrade failed with exit code $LASTEXITCODE"
        }
    }

    Write-Host "Installing project with development dependencies..."
    & $VenvPython -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) {
        throw "dependency install failed with exit code $LASTEXITCODE"
    }

    Write-Host "Checking CLI import..."
    & $VenvPython -m ai_operator_controller --help | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "CLI import check failed with exit code $LASTEXITCODE"
    }

    Write-Host "Development environment is ready: $VenvPython"
    Write-Host ""
    Write-Host "Next checks:"
    Write-Host "  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1"
    Write-Host "  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1 -WithMicrophone"
}
finally {
    Pop-Location
}
