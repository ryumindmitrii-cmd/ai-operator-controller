[CmdletBinding()]
param(
    [string]$Python = "python",
    [switch]$SkipPipUpgrade,
    [switch]$SkipLocalConfig,
    [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$LocalProfile = "config\local\profile.codex.windows.json"
$LocalSpeechProfile = "config\local\speech.local-quality.json"
$LocalRules = "config\local\replacements.json"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function Invoke-PythonVersionCheck {
    $versionScript = 'import sys; print(chr(80)+chr(121)+chr(116)+chr(104)+chr(111)+chr(110), sys.version.split()[0]); raise SystemExit(1 if sys.version_info < (3, 11) else 0)'

    & $Python -c $versionScript
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.11 or newer is required. Pass a specific executable with -Python <path>."
    }
}

Push-Location $RepoRoot
try {
    Invoke-Step "Check Python version" {
        Invoke-PythonVersionCheck
    }

    if (-not (Test-Path $VenvPython)) {
        Invoke-Step "Create local virtual environment" {
            & $Python -m venv .venv
        }
    }
    else {
        Write-Host ""
        Write-Host "==> Reuse local virtual environment"
        Write-Host ".venv already exists."
    }

    if (-not $SkipPipUpgrade) {
        Invoke-Step "Upgrade pip" {
            & $VenvPython -m pip install --upgrade pip
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping pip upgrade."
    }

    Invoke-Step "Install project with development dependencies" {
        & $VenvPython -m pip install -e ".[dev]"
    }

    Invoke-Step "Check CLI import" {
        & $VenvPython -m ai_operator_controller --help | Out-Null
    }

    if (-not $SkipLocalConfig) {
        Invoke-Step "Bootstrap local config" {
            & $VenvPython -m ai_operator_controller init-local-config
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping local config bootstrap."
    }

    if (-not $SkipDoctor) {
        Invoke-Step "Run read-only doctor" {
            & $VenvPython -m ai_operator_controller doctor --profile $LocalProfile --speech-profile $LocalSpeechProfile
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping doctor."
    }

    Write-Host ""
    Write-Host "Development environment is ready: $VenvPython"
    Write-Host ""
    Write-Host "Next checks:"
    Write-Host "  .\.venv\Scripts\python.exe -m ai_operator_controller doctor --profile $LocalProfile --speech-profile $LocalSpeechProfile"
    Write-Host "  .\.venv\Scripts\python.exe -m ai_operator_controller record-once --seconds 2 --dry-run"
    Write-Host "  .\.venv\Scripts\python.exe -m ai_operator_controller listen-gamepad --profile $LocalProfile --dry-run --max-events 5"
    Write-Host "  .\.venv\Scripts\python.exe -m ai_operator_controller dictate-run --speech-profile $LocalSpeechProfile --rules $LocalRules --seconds 2 --dry-run"
    Write-Host "  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1"
}
finally {
    Pop-Location
}
