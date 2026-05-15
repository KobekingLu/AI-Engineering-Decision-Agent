[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host "[demo] $Message"
}

function Stop-ProcessByIdIfPresent {
    param(
        [object]$Value,
        [string]$Label
    )

    if ($null -eq $Value) {
        return
    }

    $pidValue = 0
    try {
        $pidValue = [int]$Value
    } catch {
        return
    }

    try {
        Stop-Process -Id $pidValue -Force -ErrorAction Stop
        Write-Info "Stopped $Label (PID $pidValue)."
    } catch {
        Write-Info "$Label (PID $pidValue) was not running."
    }
}

$repoRoot = $PSScriptRoot
$stateFile = Join-Path $repoRoot '.tmp\demo\demo_state.json'

if (-not (Test-Path $stateFile)) {
    Write-Info 'No demo state file was found.'
    exit 0
}

try {
    $state = Get-Content -Path $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-Info 'Could not parse the demo state file.'
    exit 1
}

Stop-ProcessByIdIfPresent -Value $state.web.pid -Label 'Streamlit demo'
Stop-ProcessByIdIfPresent -Value $state.bridge.pid -Label 'OpenClaw bridge'

Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue
Write-Info 'Demo state cleared.'
