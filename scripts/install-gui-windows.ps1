# JARVIS-CODEX MANAGED - current-user Windows 11 Start menu shortcut
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$uv = Get-Command uv.exe -ErrorAction Stop
$root = Split-Path $PSScriptRoot -Parent
$project = Join-Path $root 'gui'
& $uv.Source sync --project $project --frozen --extra voice
if ($LASTEXITCODE -ne 0) { throw 'GUI dependency installation failed.' }
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
