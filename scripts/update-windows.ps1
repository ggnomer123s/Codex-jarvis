# TIGO-CODEX MANAGED - dependency-aware Windows 11 bootstrap and update
[CmdletBinding()]
param([string]$RepoPath = (Join-Path $env:USERPROFILE 'Tigo'), [switch]$SkipRussianVoice)
$ErrorActionPreference = 'Stop'

function Refresh-TigoPath {
    $extra = @(
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd'),
        (Join-Path $env:LOCALAPPDATA 'Programs\nodejs'),
        (Join-Path $env:USERPROFILE '.local\bin'),
        (Join-Path $env:APPDATA 'npm'),
        (Join-Path $env:ProgramFiles 'Git\cmd'),
        (Join-Path $env:ProgramFiles 'nodejs')
    )
    $env:PATH = (@([Environment]::GetEnvironmentVariable('Path','User'),
                    [Environment]::GetEnvironmentVariable('Path','Machine')) + $extra + @($env:PATH)) -join ';'
}

function Install-TigoPackage([string]$id) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'Windows App Installer (winget) is missing. Install App Installer from Microsoft Store, then rerun this command.' }
    & $winget.Source install --exact --id $id --source winget --accept-source-agreements --accept-package-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed: $id (exit $LASTEXITCODE). Inspect the package-manager error above." }
    Refresh-TigoPath
}

function Invoke-TigoNative([string]$program, [string[]]$arguments) {
    & $program @arguments
    if ($LASTEXITCODE -ne 0) { throw "A required command failed (exit $LASTEXITCODE): $program" }
}

function Test-TigoNative([string]$program, [string[]]$arguments) {
    # Windows PowerShell 5 native stderr must not abort an expected probe failure.
    $ErrorActionPreference = 'Continue'
    & $program @arguments *> $null
    return ($LASTEXITCODE -eq 0)
}

function Test-TigoLoginNeeded([string]$program) {
    $ErrorActionPreference = 'Continue'
    $output = & $program login status 2>&1
    $code = $LASTEXITCODE
    if ($code -eq 0) { return $false }
    if (($output | Out-String) -match 'not logged in') { return $true }
    throw 'Could not verify existing Codex authentication. Run codex login status and fix that error; no replacement login was attempted.'
}

function Update-TigoCheckout([string]$path) {
    $git = (Get-Command git.exe -ErrorAction Stop).Source
    if (Test-Path -LiteralPath (Join-Path $path '.git')) {
        # Git normalizes long/8.3 path aliases differently from PowerShell.
        # An empty prefix establishes the checkout root without comparing aliases.
        $prefix = & $git -C $path rev-parse --show-prefix
        if ($LASTEXITCODE -ne 0 -or $prefix) { throw 'The target is not the root of its checkout.' }
        $origin = & $git -C $path remote get-url origin
        if ($LASTEXITCODE -ne 0 -or $origin -notin @('https://github.com/ggnomer123s/Codex-jarvis.git','https://github.com/ggnomer123s/Codex-jarvis','git@github.com:ggnomer123s/Codex-jarvis.git')) { throw 'The existing checkout origin is not the Tigo repository.' }
        $branch = & $git -C $path symbolic-ref --quiet --short HEAD
        if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'Select main manually after saving your work; detached or other branches are not updated.' }
        $changes = & $git -C $path status --porcelain
        if ($LASTEXITCODE -ne 0 -or $changes) { throw 'Local changes found or status failed. Save/commit your work before updating; nothing was discarded.' }
        if ($env:TIGO_UPDATE_EXPECTED_REV) {
            if ($env:TIGO_UPDATE_EXPECTED_REV -notmatch '^[0-9a-f]{40}$') { throw 'Invalid reviewed update revision.' }
            Invoke-TigoNative $git @('-C',$path,'fetch','--no-tags','origin','main')
            $revision = & $git -C $path rev-parse FETCH_HEAD
            if ($LASTEXITCODE -ne 0 -or $revision -ne $env:TIGO_UPDATE_EXPECTED_REV) { throw 'The update changed. Check again in Tigo.' }
            Invoke-TigoNative $git @('-C',$path,'merge','--ff-only',$env:TIGO_UPDATE_EXPECTED_REV)
        } else {
            Invoke-TigoNative $git @('-C',$path,'pull','--ff-only','origin','main')
        }
    } else {
        if ($env:TIGO_UPDATE_EXPECTED_REV) { throw 'The reviewed checkout is missing.' }
        Invoke-TigoNative $git @('clone','--branch','main','https://github.com/ggnomer123s/Codex-jarvis.git',$path)
    }
}

function Main {
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Use 64-bit PowerShell on x86-64 Windows 11. Other architectures need separate packaging validation.' }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run this updater in a normal PowerShell window, not as Administrator.' }
    Write-Host 'Quit Tigo first, including the background listener.'
    Refresh-TigoPath
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { Install-TigoPackage 'Git.Git' }
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    if (-not $node -or -not (Get-Command npm.cmd -ErrorAction SilentlyContinue) -or -not (Test-TigoNative $node.Source @('-e','process.versions.node.match(/^[0-9]+/)[0]>=22?process.exit(0):process.exit(1)'))) {
        Install-TigoPackage 'OpenJS.NodeJS.LTS'
    }
    if (-not (Get-Command uv.exe -ErrorAction SilentlyContinue) -or -not (Get-Command uvx.exe -ErrorAction SilentlyContinue)) { Install-TigoPackage 'astral-sh.uv' }
    $vc = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64' -ErrorAction SilentlyContinue
    if (-not $vc -or $vc.Installed -ne 1) { Install-TigoPackage 'Microsoft.VCRedist.2015+.x64' }
    foreach ($command in @('git.exe','node.exe','npm.cmd','uv.exe','uvx.exe')) {
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "Missing $command after dependency installation. Reopen PowerShell, then rerun." }
    }
    if (-not (Test-TigoNative (Get-Command node.exe).Source @('-e','process.versions.node.match(/^[0-9]+/)[0]>=22?process.exit(0):process.exit(1)'))) { throw 'Your active Node manager still selects an old Node. Select Node 22+ or reopen PowerShell, then rerun.' }
    $codex = Get-Command codex.exe -ErrorAction SilentlyContinue
    if (-not $codex) { $codex = Get-Command codex.cmd -ErrorAction SilentlyContinue }
    if (-not $codex) {
        Invoke-TigoNative (Get-Command npm.cmd).Source @('install','--global','@openai/codex@latest')
        Refresh-TigoPath
        $codex = Get-Command codex.cmd -ErrorAction Stop
    }
    if (-not (Test-TigoNative $codex.Source @('app-server','--help'))) { throw 'The selected Codex installation lacks app-server support. Upgrade that installation and rerun; your existing account is retained.' }
    $path = [IO.Path]::GetFullPath($RepoPath)
    Update-TigoCheckout $path
    Invoke-TigoNative (Get-Command uv.exe).Source @('python','install','3.12')
    Invoke-TigoNative (Get-Command uv.exe).Source @('sync','--project',(Join-Path $path 'gui'),'--frozen','--extra','voice','--python','3.12')
    Invoke-TigoNative 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $path 'scripts\install-gui-windows.ps1'))
    Invoke-TigoNative (Get-Command uv.exe).Source @('run','--project',(Join-Path $path 'gui'),'--frozen','--extra','voice','python','-c','import PySide6.QtQuick, sounddevice, faster_whisper, sherpa_onnx, edge_tts, av, speech_recognition, webrtcvad; print(PySide6.__version__)')
    if (Test-TigoLoginNeeded $codex.Source) {
        Invoke-TigoNative $codex.Source @('login','--device-auth')
    }
    # Kept as a compatibility switch; neural speech needs no Windows voice component.
    Invoke-TigoNative (Get-Command uv.exe).Source @('run','--project',(Join-Path $path 'gui'),'--frozen','--extra','voice','python','-m','tigo_gui.speech_models')
    Write-Host 'Tigo updated. Existing settings and login are reused. Whisper models download on first voice use.'
    if ($env:TIGO_UPDATE_NO_LAUNCH -ne '1') {
        Invoke-TigoNative 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $path 'scripts\tigo-gui-windows.ps1'))
    }
}

if ($MyInvocation.InvocationName -ne '.') { Main }
