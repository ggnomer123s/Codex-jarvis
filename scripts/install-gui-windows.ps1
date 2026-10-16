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
# The regular installer uses the current Codex home and existing login.
$installer = Join-Path $PSScriptRoot 'install-windows.ps1'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer
if ($LASTEXITCODE -ne 0) { throw 'Shared profile installation failed; inspect the error above.' }
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
Write-Host 'Full Access is on by default. Disable it in Preferences > Access if desired.'
Write-Host 'Local neural speech is on by default. Russian/English models download on first use; Preferences > Speech selects voices. No Windows voice component is needed.'
