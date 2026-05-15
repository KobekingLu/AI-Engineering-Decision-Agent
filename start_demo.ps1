[CmdletBinding()]
param(
    [int]$BridgePort = 8787,
    [int[]]$StreamlitPorts = @(8501, 8502, 8503, 8504, 8505),
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host "[demo] $Message"
}

function Add-ProxyBypassHost {
    param([string[]]$BypassHosts)

    $entries = New-Object System.Collections.Generic.List[string]
    foreach ($value in @($env:NO_PROXY, $env:no_proxy)) {
        if ([string]::IsNullOrWhiteSpace($value)) {
            continue
        }
        foreach ($entry in ($value -split ',')) {
            $trimmed = $entry.Trim()
            if ($trimmed) {
                $entries.Add($trimmed)
            }
        }
    }

    foreach ($entryHost in $BypassHosts) {
        $trimmedHost = [string]$entryHost
        if ([string]::IsNullOrWhiteSpace($trimmedHost)) {
            continue
        }
        if (-not ($entries -contains $trimmedHost)) {
            $entries.Add($trimmedHost)
        }
    }

    $joined = ($entries | Select-Object -Unique) -join ','
    $env:NO_PROXY = $joined
    $env:no_proxy = $joined
}

function Resolve-PythonLauncher {
    foreach ($name in @('python', 'py')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $cmd -and $cmd.CommandType -eq 'Application') {
            $path = $cmd.Source
            if (-not $path) {
                $path = $cmd.Path
            }
            if ($path) {
                if ($name -eq 'python') {
                    return @{
                        FilePath  = $path
                        Arguments = @()
                    }
                }
                return @{
                    FilePath  = $path
                    Arguments = @('-3')
                }
            }
        }
    }

    throw 'Python launcher not found. Install Python or add it to PATH.'
}

function Test-PortInUse {
    param([int]$Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $async = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne(200)) {
            return $false
        }
        $client.EndConnect($async) | Out-Null
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Get-FirstFreePort {
    param([int[]]$Ports)

    foreach ($port in $Ports) {
        if (-not (Test-PortInUse -Port $port)) {
            return $port
        }
    }
    return $null
}

function Wait-ForPortOpen {
    param(
        [int]$Port,
        [int]$TimeoutSeconds
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-PortInUse -Port $Port) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Test-ProcessAlive {
    param([object]$Value)

    if ($null -eq $Value) {
        return $false
    }

    try {
        $pidValue = [int]$Value
    } catch {
        return $false
    }

    try {
        Get-Process -Id $pidValue -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Stop-ProcessByIdIfPresent {
    param(
        [object]$Value,
        [string]$Label
    )

    if ($null -eq $Value) {
        return
    }

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

function Test-BridgeHealth {
    param([string]$Url)

    try {
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec 2 -ErrorAction Stop
        return $response.ok -eq $true
    } catch {
        return $false
    }
}

function Wait-Until {
    param(
        [scriptblock]$Probe,
        [int]$TimeoutSeconds
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (& $Probe) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Start-BackgroundProcess {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$StdOut,
        [string]$StdErr
    )

    return Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -PassThru `
        -RedirectStandardOutput $StdOut `
        -RedirectStandardError $StdErr
}

function Initialize-LogFile {
    param([string]$Path)

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -Path $Path -Value '' -Encoding UTF8
}

function Save-State {
    param(
        [string]$Path,
        [hashtable]$State
    )

    $State | ConvertTo-Json -Depth 6 | Set-Content -Path $Path -Encoding UTF8
}

function Stop-StartedProcess {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$Name
    )

    if ($null -eq $Process) {
        return
    }

    try {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        Write-Info "Stopped $Name (PID $($Process.Id))."
    } catch {
        Write-Info "Could not stop $Name cleanly."
    }
}

$repoRoot = $PSScriptRoot
$stateDir = Join-Path $repoRoot '.tmp\demo'
$logDir = Join-Path $stateDir 'logs'
$stateFile = Join-Path $stateDir 'demo_state.json'
$bridgeOutLog = Join-Path $logDir 'bridge.out.log'
$bridgeErrLog = Join-Path $logDir 'bridge.err.log'
$webOutLog = Join-Path $logDir 'web.out.log'
$webErrLog = Join-Path $logDir 'web.err.log'
$streamlitHome = Join-Path $repoRoot '.tmp\streamlit_home'

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $streamlitHome | Out-Null

if (-not $env:HOME) {
    $env:HOME = $streamlitHome
}
if (-not $env:USERPROFILE) {
    $env:USERPROFILE = $streamlitHome
}
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = 'false'
$env:STREAMLIT_SERVER_FILE_WATCHER_TYPE = 'none'
$env:STREAMLIT_SERVER_RUN_ON_SAVE = 'false'
$env:PYTHONUNBUFFERED = '1'
Add-ProxyBypassHost -BypassHosts @('172.17.14.34')

$GemmaBaseUrl = 'http://172.17.14.34:8000/v1'
$GemmaModelName = 'google/gemma-4-26B-A4B-it'
$GemmaApiPath = '/chat/completions'
$DemoProfile = "gemma-local-v1|$GemmaBaseUrl|$GemmaModelName|$GemmaApiPath"

$python = Resolve-PythonLauncher
$pythonFile = $python.FilePath
$pythonArgs = @($python.Arguments)

$bridgeUrl = "http://127.0.0.1:$BridgePort/health"
$webUrl = $null
$bridgeProcess = $null
$webProcess = $null
$bridgeStartedByScript = $false
$webStartedByScript = $false

$existingState = $null
$bridgeAlreadyLive = $false
$webAlreadyLive = $false
$profileMismatch = $false
if (Test-Path $stateFile) {
    try {
        $existingState = Get-Content -Path $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        $existingState = $null
    }
}

if ($existingState) {
    if ([string]$existingState.profile -ne $DemoProfile) {
        $profileMismatch = $true
    }
    if (Test-ProcessAlive -Value $existingState.bridge.pid) {
        $bridgeAlreadyLive = $true
        $bridgeUrl = [string]$existingState.bridge.url
    }
    if (Test-ProcessAlive -Value $existingState.web.pid) {
        $webAlreadyLive = $true
        $webUrl = [string]$existingState.web.url
    }
    if ($profileMismatch) {
        Write-Info "Existing demo profile does not match the Gemma bridge profile. Restarting demo."
        Stop-ProcessByIdIfPresent -Value $existingState.web.pid -Label 'Streamlit demo'
        Stop-ProcessByIdIfPresent -Value $existingState.bridge.pid -Label 'OpenClaw bridge'
        Remove-Item -Path $stateFile -Force -ErrorAction SilentlyContinue
        $existingState = $null
        $bridgeAlreadyLive = $false
        $webAlreadyLive = $false
        $webUrl = $null
    } elseif ($bridgeAlreadyLive -and $webAlreadyLive) {
        Write-Info "Found running OpenClaw bridge at $bridgeUrl."
        Write-Info "Found running Streamlit demo at $webUrl."
        Write-Info "Demo already running."
        if (-not $NoBrowser) {
            Start-Process $webUrl | Out-Null
        }
        exit 0
    }
}

try {
    if ($bridgeAlreadyLive -or (Test-BridgeHealth -Url $bridgeUrl)) {
        Write-Info "OpenClaw bridge already running at $bridgeUrl."
    } else {
        if (Test-PortInUse -Port $BridgePort) {
            throw "Port $BridgePort is already in use, but bridge health did not respond."
        }

        Initialize-LogFile -Path $bridgeOutLog
        Initialize-LogFile -Path $bridgeErrLog

        $bridgeArgs = @(
            $pythonArgs + @(
                '-m'
                'decision_agent.openclaw_bridge'
                '--host'
                '127.0.0.1'
                '--port'
                "$BridgePort"
                '--assistant-mode'
                'local'
                '--assistant-style'
                'bullet'
                '--local-model-base-url'
                $GemmaBaseUrl
                '--local-model-model'
                $GemmaModelName
                '--local-model-api-path'
                $GemmaApiPath
                '--local-model-timeout-seconds'
                '30'
                '--local-model-max-tokens'
                '256'
                '--local-model-temperature'
                '0.2'
            )
        )

        $bridgeProcess = Start-BackgroundProcess `
            -FilePath $pythonFile `
            -Arguments $bridgeArgs `
            -WorkingDirectory $repoRoot `
            -StdOut $bridgeOutLog `
            -StdErr $bridgeErrLog

        $bridgeStartedByScript = $true
        if (-not (Wait-Until -Probe { Test-BridgeHealth -Url $bridgeUrl } -TimeoutSeconds 30)) {
            throw "OpenClaw bridge did not become healthy. See $bridgeOutLog and $bridgeErrLog."
        }

        Write-Info "OpenClaw bridge started at $bridgeUrl (PID $($bridgeProcess.Id))."
    }

    if ($webAlreadyLive) {
        Write-Info "Streamlit demo already running at $webUrl."
    } else {
        $webPort = Get-FirstFreePort -Ports $StreamlitPorts
        if ($null -eq $webPort) {
            throw 'No free Streamlit port was found in the 8501-8505 range.'
        }

        Initialize-LogFile -Path $webOutLog
        Initialize-LogFile -Path $webErrLog

        $appPath = Join-Path $repoRoot 'web_app\app.py'
        $webArgs = @(
            $pythonArgs + @(
                '-m'
                'streamlit'
                'run'
                $appPath
                '--server.headless=true'
                '--server.address=127.0.0.1'
                "--server.port=$webPort"
            )
        )

        $webProcess = Start-BackgroundProcess `
            -FilePath $pythonFile `
            -Arguments $webArgs `
            -WorkingDirectory $repoRoot `
            -StdOut $webOutLog `
            -StdErr $webErrLog

        $webStartedByScript = $true
        $webUrl = "http://127.0.0.1:$webPort"

        if (-not (Wait-ForPortOpen -Port $webPort -TimeoutSeconds 60)) {
            throw "Streamlit demo did not become ready at $webUrl. See $webOutLog and $webErrLog."
        }

        Write-Info "Streamlit demo started at $webUrl (PID $($webProcess.Id))."
    }

    $state = @{
        profile = $DemoProfile
        started_at = (Get-Date).ToString('o')
        repo_root = $repoRoot
        bridge = @{
            status = $(if ($bridgeStartedByScript) { 'started' } else { 'already_running' })
            pid = $(if ($bridgeProcess) { $bridgeProcess.Id } else { $null })
            url = $bridgeUrl
            assistant_mode = 'local'
            local_model_base_url = $GemmaBaseUrl
            local_model_model = $GemmaModelName
            out_log = $bridgeOutLog
            err_log = $bridgeErrLog
        }
        web = @{
            status = $(if ($webStartedByScript) { 'started' } else { 'already_running' })
            pid = $(if ($webProcess) { $webProcess.Id } else { $null })
            url = $webUrl
            out_log = $webOutLog
            err_log = $webErrLog
        }
    }
    Save-State -Path $stateFile -State $state

    Write-Info "Demo ready."
    Write-Info "Bridge: $bridgeUrl"
    Write-Info "Web UI: $webUrl"
    Write-Info "Logs: $logDir"

    if (-not $NoBrowser) {
        Start-Process $webUrl | Out-Null
    }

    return 0
} catch {
    if ($webStartedByScript) {
        Stop-StartedProcess -Process $webProcess -Name 'Streamlit demo'
    }
    if ($bridgeStartedByScript) {
        Stop-StartedProcess -Process $bridgeProcess -Name 'OpenClaw bridge'
    }
    Write-Error $_
    return 1
}
