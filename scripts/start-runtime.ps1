[CmdletBinding()]
param(
    [ValidateSet("doctor", "gamepad-dry-run", "dictation-dry-run", "dictation-execute")]
    [string]$Mode = "doctor",
    [string]$Profile = "config\local\profile.codex.windows.json",
    [string]$SpeechProfile = "config\local\speech.local-quality.json",
    [string]$Rules = "config\local\replacements.json",
    [double]$Seconds = 2.0,
    [int]$GamepadMaxEvents = 10,
    [int]$MicDevice = -1,
    [int]$GamepadIndex = -1,
    [switch]$AllowModelDownload,
    [switch]$ConfirmExecute
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

function Assert-FileExists {
    param(
        [string]$Path,
        [string]$Hint
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing file: $Path. $Hint"
    }
}

function Invoke-Cli {
    param(
        [string[]]$Arguments
    )

    & $VenvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "ai_operator_controller failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    throw "Missing .venv. Run scripts\setup-dev.ps1 first."
}

if ($Seconds -le 0) {
    throw "Seconds must be positive"
}

if ($GamepadMaxEvents -le 0) {
    throw "GamepadMaxEvents must be positive"
}

Push-Location $RepoRoot
try {
    Assert-FileExists $Profile "Run scripts\setup-dev.ps1 or ai_operator_controller init-local-config."

    $profileArgs = @("--profile", $Profile)
    if ($GamepadIndex -ge 0) {
        $profileArgs += @("--gamepad-index", "$GamepadIndex")
    }

    if ($Mode -in @("doctor", "dictation-dry-run", "dictation-execute")) {
        Assert-FileExists $SpeechProfile "Run scripts\setup-dev.ps1 or ai_operator_controller init-local-config."
    }

    if ($Mode -in @("dictation-dry-run", "dictation-execute")) {
        Assert-FileExists $Rules "Run scripts\setup-dev.ps1 or ai_operator_controller init-local-config."
    }

    if ($Mode -eq "doctor") {
        $doctorArgs = @("-m", "ai_operator_controller", "doctor") + $profileArgs + @("--speech-profile", $SpeechProfile)
        if ($MicDevice -ge 0) {
            $doctorArgs += @("--mic-device", "$MicDevice")
        }
        Invoke-Cli $doctorArgs
        return
    }

    if ($Mode -eq "gamepad-dry-run") {
        Invoke-Cli @(
            "-m",
            "ai_operator_controller",
            "listen-gamepad",
            "--profile",
            $Profile,
            "--dry-run",
            "--max-events",
            "$GamepadMaxEvents"
        )
        return
    }

    $dictationArgs = @(
        "-m",
        "ai_operator_controller",
        "dictate-run",
        "--speech-profile",
        $SpeechProfile,
        "--rules",
        $Rules,
        "--seconds",
        "$Seconds"
    )
    if ($MicDevice -ge 0) {
        $dictationArgs += @("--mic-device", "$MicDevice")
    }
    if ($AllowModelDownload) {
        $dictationArgs += "--allow-model-download"
    }

    if ($Mode -eq "dictation-dry-run") {
        Invoke-Cli ($dictationArgs + "--dry-run")
        return
    }

    if (-not $ConfirmExecute) {
        throw "dictation-execute writes to the active window. Focus a safe target and rerun with -ConfirmExecute."
    }

    Invoke-Cli ($dictationArgs + "--execute-output")
}
finally {
    Pop-Location
}
