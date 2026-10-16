# JARVIS-CODEX MANAGED - dependency-aware Windows 11 bootstrap and update
[CmdletBinding()]
param([string]$RepoPath = (Join-Path $env:USERPROFILE 'Codex-jarvis-gui'), [switch]$SkipRussianVoice)
$ErrorActionPreference = 'Stop'

function Refresh-JarvisPath {
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

function Install-JarvisPackage([string]$id) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'Windows App Installer (winget) is missing. Install App Installer from Microsoft Store, then rerun this command.' }
    & $winget.Source install --exact --id $id --source winget --accept-source-agreements --accept-package-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed: $id (exit $LASTEXITCODE). Inspect the package-manager error above." }
    Refresh-JarvisPath
}

function Invoke-JarvisNative([string]$program, [string[]]$arguments) {
    & $program @arguments
    if ($LASTEXITCODE -ne 0) { throw "A required command failed (exit $LASTEXITCODE): $program" }
}

function Test-JarvisNative([string]$program, [string[]]$arguments) {
    # Windows PowerShell 5 native stderr must not abort an expected probe failure.
    $ErrorActionPreference = 'Continue'
    & $program @arguments *> $null
    return ($LASTEXITCODE -eq 0)
}

function Test-JarvisLoginNeeded([string]$program) {
    $ErrorActionPreference = 'Continue'
    $output = & $program login status 2>&1
    $code = $LASTEXITCODE
    if ($code -eq 0) { return $false }
    if (($output | Out-String) -match 'not logged in') { return $true }
    throw 'Could not verify existing Codex authentication. Run codex login status and fix that error; no replacement login was attempted.'
}

function Update-JarvisCheckout([string]$path) {
    $git = (Get-Command git.exe -ErrorAction Stop).Source
    if (Test-Path -LiteralPath (Join-Path $path '.git')) {
        $top = & $git -C $path rev-parse --show-toplevel
        if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($top).TrimEnd('\','/') -ne $path.TrimEnd('\','/')) { throw 'The target is not the root of its checkout.' }
        $origin = & $git -C $path remote get-url origin
        if ($LASTEXITCODE -ne 0 -or $origin -notin @('https://github.com/ggnomer123s/Codex-jarvis.git','https://github.com/ggnomer123s/Codex-jarvis','git@github.com:ggnomer123s/Codex-jarvis.git')) { throw 'The existing checkout origin is not the JARVIS repository.' }
        $branch = & $git -C $path symbolic-ref --quiet --short HEAD
        if ($LASTEXITCODE -ne 0 -or $branch -ne 'main') { throw 'Select main manually after saving your work; detached or other branches are not updated.' }
        $changes = & $git -C $path status --porcelain
        if ($LASTEXITCODE -ne 0 -or $changes) { throw 'Local changes found or status failed. Save/commit your work before updating; nothing was discarded.' }
        Invoke-JarvisNative $git @('-C',$path,'pull','--ff-only','origin','main')
    } else {
        Invoke-JarvisNative $git @('clone','--branch','main','https://github.com/ggnomer123s/Codex-jarvis.git',$path)
    }
}

function Install-JarvisRussianVoice {
    $synth = $null
    try {
        Add-Type -AssemblyName System.Speech
        $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
        $russian = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'ru-*' })
        if ($russian.Count) { Write-Host 'Russian system speech voice is already installed.'; return }
    } catch {
        Write-Host 'Checking the Russian Text-to-Speech Windows component.'
    } finally {
        if ($synth) { $synth.Dispose() }
    }
    # Elevate only the official OS capability installation, never JARVIS/Codex.
    Write-Host 'Russian speech is missing. Windows may ask for UAC to install the official Text-to-Speech component.'
    try {
        $process = Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList @(
            '-NoProfile','-Command',
            '"Add-WindowsCapability -Online -Name Language.TextToSpeech~~~ru-RU~0.0.1.0 -ErrorAction Stop | Out-Host"'
        )
        if ($process.ExitCode -ne 0) { throw "Windows capability installation failed (exit $($process.ExitCode))." }
    } catch {
        Write-Warning ('JARVIS is installed, but Russian speech setup needs attention: ' + $_.Exception.Message + ' Add Russian in Settings > Time & language > Speech, then Refresh voices in JARVIS.')
    }
}

function Main {
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Use 64-bit PowerShell on x86-64 Windows 11. Other architectures need separate packaging validation.' }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run this updater in a normal PowerShell window, not as Administrator.' }
    Write-Host 'Quit JARVIS first, including the background listener.'
    Refresh-JarvisPath
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { Install-JarvisPackage 'Git.Git' }
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    if (-not $node -or -not (Get-Command npm.cmd -ErrorAction SilentlyContinue) -or -not (Test-JarvisNative $node.Source @('-e','process.versions.node.match(/^[0-9]+/)[0]>=22?process.exit(0):process.exit(1)'))) {
        Install-JarvisPackage 'OpenJS.NodeJS.LTS'
    }
    if (-not (Get-Command uv.exe -ErrorAction SilentlyContinue) -or -not (Get-Command uvx.exe -ErrorAction SilentlyContinue)) { Install-JarvisPackage 'astral-sh.uv' }
    $vc = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64' -ErrorAction SilentlyContinue
    if (-not $vc -or $vc.Installed -ne 1) { Install-JarvisPackage 'Microsoft.VCRedist.2015+.x64' }
    foreach ($command in @('git.exe','node.exe','npm.cmd','uv.exe','uvx.exe')) {
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "Missing $command after dependency installation. Reopen PowerShell, then rerun." }
    }
    if (-not (Test-JarvisNative (Get-Command node.exe).Source @('-e','process.versions.node.match(/^[0-9]+/)[0]>=22?process.exit(0):process.exit(1)'))) { throw 'Your active Node manager still selects an old Node. Select Node 22+ or reopen PowerShell, then rerun.' }
    $codex = Get-Command codex.exe -ErrorAction SilentlyContinue
    if (-not $codex) { $codex = Get-Command codex.cmd -ErrorAction SilentlyContinue }
    if (-not $codex) {
        Invoke-JarvisNative (Get-Command npm.cmd).Source @('install','--global','@openai/codex@latest')
        Refresh-JarvisPath
        $codex = Get-Command codex.cmd -ErrorAction Stop
    }
    if (-not (Test-JarvisNative $codex.Source @('app-server','--help'))) { throw 'The selected Codex installation lacks app-server support. Upgrade that installation and rerun; your existing account is retained.' }
    $path = [IO.Path]::GetFullPath($RepoPath)
    Update-JarvisCheckout $path
    Invoke-JarvisNative (Get-Command uv.exe).Source @('python','install','3.12')
    Invoke-JarvisNative (Get-Command uv.exe).Source @('sync','--project',(Join-Path $path 'gui'),'--frozen','--extra','voice','--python','3.12')
    Invoke-JarvisNative 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $path 'scripts\install-gui-windows.ps1'))
    Invoke-JarvisNative (Get-Command uv.exe).Source @('run','--project',(Join-Path $path 'gui'),'--frozen','--extra','voice','python','-c','import PySide6.QtQuick, sounddevice, faster_whisper; print(PySide6.__version__)')
    if (Test-JarvisLoginNeeded $codex.Source) {
        Invoke-JarvisNative $codex.Source @('login','--device-auth')
    }
    if (-not $SkipRussianVoice) { Install-JarvisRussianVoice }
    Write-Host 'JARVIS updated. Existing settings and login are reused. Whisper models download on first voice use.'
    Invoke-JarvisNative 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $path 'scripts\jarvis-gui-windows.ps1'))
}

if ($MyInvocation.InvocationName -ne '.') { Main }
