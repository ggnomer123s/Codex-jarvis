# TIGO-CODEX MANAGED - explicit Full Access in the shared Codex profile
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Commands)
$ErrorActionPreference = 'Stop'

if (([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
     [Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw 'Tigo Full Access must not run elevated.'
}
$codex = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $codex) { $codex = Get-Command codex.cmd -ErrorAction SilentlyContinue }
if (-not $codex) { throw 'Codex CLI not found.' }

function Show-TigoFullHelp {
  Write-Host @'
Usage: tigo-full [fast|normal|deep|login|status|help]
       tigo full [fast|normal|deep|login|status|help]

fast     Full Access with low reasoning effort
normal   Full Access with configured default reasoning
deep     Full Access with high reasoning effort
login    Sign in to current Codex profile
status   Inspect profile login and MCP registrations

All execution modes bypass Codex command approvals and shell sandbox.
This does NOT grant Administrator access or bypass Windows UAC.
'@
}

if ($Commands -and $Commands.Count -gt 1) {
  Show-TigoFullHelp
  exit 2
}
$mode = if ($Commands -and $Commands.Count -gt 0) { $Commands[0].ToLowerInvariant() } else { 'normal' }

switch ($mode) {
  { $_ -in @('help','-h','--help') } {
    Show-TigoFullHelp
    exit 0
  }
  'login' {
    & $codex.Source login
    exit $LASTEXITCODE
  }
  'status' {
    $sharedHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
    Write-Host "Shared CODEX_HOME: $sharedHome"
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
    Write-Warning "Tigo FULL ACCESS ($mode): unsandboxed; no Codex command approvals."
    # Do not send a default task: launch the interactive CLI immediately.
    & $codex.Source @launchArgs
    exit $LASTEXITCODE
  }
  default {
    Show-TigoFullHelp
    exit 2
  }
}
