# JARVIS-CODEX MANAGED - current-user Windows 11 Start menu shortcut
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$uv = Get-Command uv.exe -ErrorAction Stop
$null = Get-Command uvx.exe -ErrorAction Stop
$codex = Get-Command codex.exe -ErrorAction SilentlyContinue
if (-not $codex) { $codex = Get-Command codex.cmd -ErrorAction SilentlyContinue }
if (-not $codex) { throw 'Install Codex CLI and reopen PowerShell; see docs/install-desktop.md.' }
$root = Split-Path $PSScriptRoot -Parent
$project = Join-Path $root 'gui'
& $uv.Source sync --project $project --frozen --extra voice
if ($LASTEXITCODE -ne 0) { throw 'GUI dependency installation failed.' }
# Run in a child process: the full installer changes CODEX_HOME only there.
$fullInstaller = Join-Path $PSScriptRoot 'install-full-windows.ps1'
Write-Host 'Preparing the included Full Access profile. Enable it later with the GUI checkbox.'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $fullInstaller -Acknowledgement 'ENABLE FULL ACCESS'
if ($LASTEXITCODE -ne 0) { throw 'Full Access profile preparation failed. The normal profile was not switched.' }
$python = Join-Path $project '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $python)) { throw 'GUI Python runtime was not created.' }
$menu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$shortcutPath = Join-Path $menu 'JARVIS.lnk'
$shell = New-Object -ComObject WScript.Shell
if (Test-Path $shortcutPath) {
  $existing = $shell.CreateShortcut($shortcutPath)
  if ($existing.Description -ne 'JARVIS-CODEX MANAGED') { throw 'Refusing to replace an unrelated JARVIS shortcut.' }
}
New-Item -ItemType Directory -Path $menu -Force | Out-Null
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $python
$shortcut.Arguments = '-m jarvis_gui'
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = (Join-Path $project 'jarvis_gui\ui\icon.ico') + ',0'
$shortcut.Description = 'JARVIS-CODEX MANAGED'
$shortcut.Save()
Write-Host 'Installed JARVIS in your Start menu. Keep this checkout in place.'
Write-Host 'Full Access is prepared and initially off. Enable it with the checkbox in Preferences > Access.'
