# TIGO-CODEX MANAGED - compatibility installer; one shared Codex profile.
[CmdletBinding()]
param([string]$Acknowledgement)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'install-windows.ps1')
exit $LASTEXITCODE
