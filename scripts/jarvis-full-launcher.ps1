# JARVIS-CODEX MANAGED — optional, unsandboxed user-level Codex profile
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Commands)
$ErrorActionPreference = 'Stop'

if (([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
     [Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw 'JARVIS Full Access must not run elevated.'
}
$env:CODEX_HOME = Join-Path $env:LOCALAPPDATA 'jarvis-codex\full-codex-home'
$codex = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $codex) { $codex = Get-Command codex.cmd -ErrorAction SilentlyContinue }
if (-not $codex) { throw 'Codex CLI not found.' }

function Show-JarvisFullHelp {
  Write-Host @'
Usage: jarvis-full [fast|normal|deep|login|status|help]
       jarvis full [fast|normal|deep|login|status|help]

fast     Full Access with low reasoning effort
normal   Full Access with configured default reasoning
deep     Full Access with high reasoning effort
login    Sign in to independent Codex user profile
status   Inspect profile login and MCP registrations

All execution modes bypass Codex command approvals and shell sandbox.
This does NOT grant Administrator access or bypass Windows UAC.
'@
}

if ($Commands -and $Commands.Count -gt 1) {
  Show-JarvisFullHelp
  exit 2
}
$mode = if ($Commands -and $Commands.Count -gt 0) { $Commands[0].ToLowerInvariant() } else { 'normal' }

switch ($mode) {
  { $_ -in @('help','-h','--help') } {
    Show-JarvisFullHelp
    exit 0
  }
  'login' {
    & $codex.Source login
    exit $LASTEXITCODE
  }
  'status' {
    Write-Host "Independent CODEX_HOME: $env:CODEX_HOME"
    & $codex.Source login status
    & $codex.Source mcp list
    exit $LASTEXITCODE
  }
  { $_ -in @('fast','normal','start','deep') } {
    $launchArgs = @('--dangerously-bypass-approvals-and-sandbox')
    switch ($mode) {
      'fast' { $launchArgs += @('--config','model_reasoning_effort=low') }
      'deep' { $launchArgs += @('--config','model_reasoning_effort=high') }
    }
    Write-Warning "JARVIS FULL ACCESS ($mode): unsandboxed; no Codex command approvals."
    # Do not send a default task: launch the interactive CLI immediately.
    & $codex.Source @launchArgs
    exit $LASTEXITCODE
  }
  default {
    Show-JarvisFullHelp
    exit 2
  }
}
