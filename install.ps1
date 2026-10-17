# TIGO-CODEX MANAGED - single Windows 11 install/update entry point
[CmdletBinding()]
param([string]$RepoPath = (Join-Path $env:USERPROFILE 'Tigo'))
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$file = Join-Path ([IO.Path]::GetTempPath()) ('tigo-setup-' + [guid]::NewGuid().ToString() + '.ps1')
try {
    Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/ggnomer123s/Codex-jarvis/main/scripts/update-windows.ps1' -OutFile $file
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $file -RepoPath $RepoPath
    if ($LASTEXITCODE -ne 0) { throw 'Tigo installation stopped. Inspect the error above; your work was not discarded.' }
} finally {
    Remove-Item -LiteralPath $file -Force -ErrorAction SilentlyContinue
}
