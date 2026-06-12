[CmdletBinding()]
param(
    [switch]$WithMicrophone,
    [double]$MicrophoneSeconds = 0.2,
    [switch]$WithSpeechModel,
    [string]$SpeechAudioPath,
    [switch]$WithDictateRun,
    [switch]$AllowModelDownload,
    [switch]$SkipBandit,
    [switch]$SkipPipAudit
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

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

function Get-PublicScanFiles {
    $paths = & git ls-files --cached --others --exclude-standard `
        AGENTS.md CHANGELOG.md CONTRIBUTING.md LICENSE README.md SECURITY.md `
        pyproject.toml config docs scripts src tests

    if ($LASTEXITCODE -ne 0) {
        throw "git ls-files failed with exit code $LASTEXITCODE"
    }

    $binaryExtensions = @(
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".wav", ".mp3",
        ".flac", ".ogg", ".msi", ".exe", ".pdf"
    )

    $paths |
        Where-Object { $_ -and (Test-Path $_ -PathType Leaf) } |
        Where-Object { $_ -ne "scripts/smoke.ps1" } |
        Where-Object { $binaryExtensions -notcontains ([System.IO.Path]::GetExtension($_).ToLowerInvariant()) }
}

function Invoke-PrivacyMarkerScan {
    $files = @(Get-PublicScanFiles)
    if ($files.Count -eq 0) {
        throw "No public files found for privacy scan"
    }

    $localName = -join @(
        [char]0x0414, [char]0x043C, [char]0x0438, [char]0x0442,
        [char]0x0440, [char]0x0438, [char]0x0439
    )
    $patterns = @(
        "C:" + [char]0x5C + [char]0x5C + "Users",
        "D:" + [char]0x5C + [char]0x5C,
        "One" + "Drive",
        $localName,
        "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "sk-[A-Za-z0-9]",
        "ghp_[A-Za-z0-9]",
        "github_pat_[A-Za-z0-9_]+",
        "BEGIN (RSA|OPENSSH|PRIVATE) KEY",
        "EXITA"
    )
    $pattern = $patterns -join "|"

    $matches = foreach ($file in $files) {
        Select-String -Path $file -Pattern $pattern -Encoding UTF8 -ErrorAction Stop
    }

    if ($matches) {
        $matches | ForEach-Object {
            Write-Host "$($_.Path):$($_.LineNumber):$($_.Line)"
        }
        throw "Privacy marker scan found candidate private data"
    }
}

function Invoke-DetectSecretsScan {
    $files = @(Get-PublicScanFiles)
    if ($files.Count -eq 0) {
        throw "No public files found for detect-secrets scan"
    }

    $outputFile = New-TemporaryFile
    try {
        & $VenvPython -m detect_secrets scan @files | Set-Content -Path $outputFile -Encoding UTF8
        if ($LASTEXITCODE -ne 0) {
            throw "detect-secrets scan failed with exit code $LASTEXITCODE"
        }

        $json = Get-Content -Path $outputFile -Raw | ConvertFrom-Json
        if ($json.results.PSObject.Properties.Count -gt 0) {
            $json.results | ConvertTo-Json -Depth 6
            throw "detect-secrets found candidate secrets"
        }
    }
    finally {
        Remove-Item -LiteralPath $outputFile -Force -ErrorAction SilentlyContinue
    }
}

if (-not (Test-Path $VenvPython)) {
    throw "Missing .venv. Run scripts\setup-dev.ps1 first."
}

if ($MicrophoneSeconds -le 0) {
    throw "MicrophoneSeconds must be positive"
}

if ($WithSpeechModel -and -not $SpeechAudioPath) {
    throw "SpeechAudioPath is required when WithSpeechModel is set"
}

Push-Location $RepoRoot
try {
    Invoke-Step "CLI help" {
        & $VenvPython -m ai_operator_controller --help | Out-Null
    }
    Invoke-Step "Doctor" {
        & $VenvPython -m ai_operator_controller doctor
    }
    Invoke-Step "Profile doctor" {
        & $VenvPython -m ai_operator_controller doctor --profile config\examples\profile.codex.windows.json
    }
    Invoke-Step "Action plan" {
        & $VenvPython -m ai_operator_controller plan-action cursor_left
    }
    Invoke-Step "Gamepad simulation" {
        & $VenvPython -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_y 0.8
    }
    Invoke-Step "Text cleanup" {
        & $VenvPython -m ai_operator_controller clean-text --rules config\examples\replacements.example.json --text "uh first line new line second line send"
    }
    Invoke-Step "Dictation preview" {
        & $VenvPython -m ai_operator_controller dictate-once --rules config\examples\replacements.example.json --text "uh first line new line second line send"
    }

    if ($WithMicrophone) {
        Invoke-Step "Microphone metadata dry run" {
            & $VenvPython -m ai_operator_controller record-once --seconds $MicrophoneSeconds --dry-run
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping microphone dry run. Pass -WithMicrophone to record metadata only."
    }

    if ($WithSpeechModel) {
        Invoke-Step "Speech model transcription dry run" {
            $transcribeArgs = @(
                "-m",
                "ai_operator_controller",
                "transcribe-file",
                "--speech-profile",
                "config\examples\speech.local-quality.example.json",
                "--audio-file",
                $SpeechAudioPath,
                "--dry-run"
            )
            if ($AllowModelDownload) {
                $transcribeArgs += "--allow-model-download"
            }
            & $VenvPython @transcribeArgs
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping speech model dry run. Pass -WithSpeechModel -SpeechAudioPath <file> to transcribe a local file."
    }

    if ($WithDictateRun) {
        Invoke-Step "Dictation runtime dry run" {
            $dictateRunArgs = @(
                "-m",
                "ai_operator_controller",
                "dictate-run",
                "--seconds",
                $MicrophoneSeconds,
                "--rules",
                "config\examples\replacements.example.json",
                "--dry-run"
            )
            if ($AllowModelDownload) {
                $dictateRunArgs += "--allow-model-download"
            }
            & $VenvPython @dictateRunArgs
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping dictation runtime dry run. Pass -WithDictateRun to record, transcribe, and plan output events."
    }

    Invoke-Step "Tests" {
        & $VenvPython -m pytest
    }
    Invoke-Step "Ruff" {
        & $VenvPython -m ruff check src tests
    }
    Invoke-Step "Compileall" {
        & $VenvPython -m compileall src tests
    }
    Invoke-Step "Diff whitespace check" {
        & git diff --check
    }
    Invoke-Step "Privacy marker scan" {
        Invoke-PrivacyMarkerScan
    }
    Invoke-Step "detect-secrets" {
        Invoke-DetectSecretsScan
    }

    if (-not $SkipBandit) {
        Invoke-Step "Bandit" {
            & $VenvPython -m bandit -r src
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping Bandit."
    }

    if (-not $SkipPipAudit) {
        Invoke-Step "pip-audit" {
            & $VenvPython -m pip_audit
        }
    }
    else {
        Write-Host ""
        Write-Host "Skipping pip-audit."
    }

    Write-Host ""
    Write-Host "Smoke checks completed."
}
finally {
    Pop-Location
}
