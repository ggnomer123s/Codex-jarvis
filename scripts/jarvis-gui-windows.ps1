# JARVIS-CODEX MANAGED - native Windows 11 desktop application
[CmdletBinding()]
param([switch]$NoVoice, [switch]$SmokeTest, [switch]$Background)
$ErrorActionPreference = 'Stop'
$uv = Get-Command uv.exe -ErrorAction Stop
$project = Join-Path (Split-Path $PSScriptRoot -Parent) 'gui'
$launchArgs = @('run', '--project', $project, '--frozen')
if (-not $NoVoice) { $launchArgs += @('--extra', 'voice') }
$launchArgs += 'jarvis-gui'
if ($SmokeTest) { $launchArgs += '--smoke-test' }
if ($Background) { $launchArgs += '--background' }
& $uv.Source @launchArgs
exit $LASTEXITCODE
