# Desktop installation commands by operating system

These commands install the graphical JARVIS app and voice dependencies from
`main`. Run the Linux blocks in Bash from a normal user account. Use a normal
PowerShell window on Windows. Run each block in order; stop if a command fails.
If Codex is already installed and signed in, skip its npm install/login lines.

The commands target current x86-64 desktop distributions: Ubuntu 22.04+, Debian
12+, Linux Mint 21+, current Arch derivatives, supported Fedora releases,
openSUSE Tumbleweed/Leap 16, and Windows 11. The locked Qt x86-64 wheels require
glibc 2.34+; older Linux releases and Alpine/musl need a separate packaging
solution. Package availability can differ by distribution release. These are
installation recipes, not evidence of hardware testing on every distribution.

The GUI installer also registers the desktop MCP in the ordinary Codex home.
Install the [session-specific prerequisites](linux.md#2-install-prerequisites)
first: X11 needs `xdotool`, `wmctrl`, `maim`; Hyprland needs `grim`, `wtype`
and compositor tools; other Wayland desktops need their portal backend.
Existing MCP permissions are retained.

## CachyOS, Arch, Manjaro, EndeavourOS

```bash
sudo pacman -Syu --needed git uv python nodejs npm portaudio libpulse speech-dispatcher espeak-ng grim wtype xdotool wmctrl maim mesa libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
repo_dir="$HOME/Codex-jarvis-gui"
if [ -e "$repo_dir/.git" ]; then
  git -C "$repo_dir" pull --ff-only
else
  git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$repo_dir"
fi && bash "$repo_dir/scripts/install-gui-linux.sh" && "$HOME/.local/bin/jarvis-gui"
```

## Ubuntu, Debian, Linux Mint, Pop!_OS

```bash
sudo apt update
sudo apt install -y git curl python3 nodejs npm libportaudio2 libpulse0 speech-dispatcher espeak-ng libspeechd2 libegl1 libopengl0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0
curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$HOME/Codex-jarvis-gui"
bash "$HOME/Codex-jarvis-gui/scripts/install-gui-linux.sh"
"$HOME/.local/bin/jarvis-gui"
```

## Fedora

```bash
sudo dnf install -y git curl python3 nodejs npm portaudio pulseaudio-libs speech-dispatcher speech-dispatcher-espeak-ng espeak-ng mesa-libEGL mesa-libGL libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil
curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$HOME/Codex-jarvis-gui"
bash "$HOME/Codex-jarvis-gui/scripts/install-gui-linux.sh"
"$HOME/.local/bin/jarvis-gui"
```

## openSUSE Tumbleweed / Leap 16

```bash
sudo zypper install -y git curl python3 nodejs npm libportaudio2 libpulse0 libEGL1 libOpenGL0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0
curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$HOME/Codex-jarvis-gui"
bash "$HOME/Codex-jarvis-gui/scripts/install-gui-linux.sh"
"$HOME/.local/bin/jarvis-gui"
```

The curl command uses uv's official HTTPS installer. uv installs the locked
Python/Qt/voice dependencies without requiring a matching system Python version.
The Linux installers create `~/.local/bin/jarvis-gui`, a JARVIS application
menu entry and update the ordinary Codex desktop backend. Full Access defaults
on; disable it in Preferences > Access to save a sandbox mode for GUI and regular
CLI launchers. All modes reuse the current Codex login. Keep the checkout in place.

Linux spoken replies use Speech Dispatcher and an installed speech module.
For openSUSE, install the Speech Dispatcher/eSpeak NG packages available for
your release and configure its output module; see [speech setup](speech-output.md).

## Windows 11

If your prompt looks like `C:\Users\Cosmo>`, you are in Command Prompt (CMD).
Run `powershell` first to enter a normal PowerShell session. The blocks below
use PowerShell syntax and work from your user directory; do not run them in an
Administrator window.

Install prerequisites (skip packages already installed):

```powershell
winget install -e --id Git.Git --source winget
winget install -e --id OpenJS.NodeJS.LTS --source winget
winget install -e --id astral-sh.uv --source winget
```

Close PowerShell and open a new normal PowerShell window so the installed
commands are on PATH. Then:

```powershell
npm.cmd install --global @openai/codex
codex.cmd login
$repoPath = Join-Path $env:USERPROFILE 'Codex-jarvis-gui'
if (Test-Path -LiteralPath (Join-Path $repoPath '.git')) {
    git -C $repoPath pull --ff-only
} else {
    git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git $repoPath
}
if ($LASTEXITCODE -ne 0) { throw 'Git clone/update failed; installation stopped.' }
$installerPath = Join-Path $repoPath 'scripts\install-gui-windows.ps1'
if (-not (Test-Path -LiteralPath $installerPath)) { throw 'GUI installer is missing from this checkout.' }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath
if ($LASTEXITCODE -ne 0) { throw 'GUI installation failed; inspect the error above.' }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoPath 'scripts\jarvis-gui-windows.ps1')
```

JARVIS also appears in the current user's Start menu. Keep the cloned directory
in place. Full Access is on by default and can be disabled in
Preferences > Access. Your existing Codex login is reused; no second profile or
confirmation phrase is needed. Microphone access can be enabled in Windows Privacy settings.

### Why the previous commands failed

`git pull --ff-only` works inside a Git checkout, not directly in `C:\Users\Cosmo`.
Use `git -C "$repoPath" pull --ff-only` as above. Likewise,
`.\scripts\install-full-windows.ps1` is relative to the current directory. Its
absolute path would be inside the checkout, but the new GUI installer prepares
the ordinary shared Codex profile, so an extra full-profile installer is unnecessary. Installing a
newer PowerShell does not fix a missing checkout or a relative path.

## Update an existing GUI installation

First use **Quit JARVIS** to stop the background listener and old GUI process.
If `Codex-jarvis-gui` already exists, update it instead of cloning again.
Preserve local edits; `--ff-only` refuses a divergent history.

Linux:

```bash
git -C "$HOME/Codex-jarvis-gui" pull --ff-only
bash "$HOME/Codex-jarvis-gui/scripts/install-gui-linux.sh"
"$HOME/.local/bin/jarvis-gui"
```

Windows 11:

```powershell
git -C "$env:USERPROFILE\Codex-jarvis-gui" pull --ff-only
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Codex-jarvis-gui\scripts\install-gui-windows.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Codex-jarvis-gui\scripts\jarvis-gui-windows.ps1"
```

## Spoken replies

Speech is on by default. Open **Preferences > Speech** to test installed voices
and adjust voice/rate/pitch/volume. Windows uses native system voices; add the
Russian voice under **Settings > Time & language > Speech > Add voices** if
needed. Linux uses the packages listed above; existing CachyOS users can run
`sudo pacman -S --needed libpulse speech-dispatcher espeak-ng` before updating.
The installer updates the managed JARVIS Skill and AGENTS character instructions;
start a new conversation after updating. See [speech output](speech-output.md).

## Desktop automation and first voice use

These commands install the frontend, launchers and applicable desktop MCP in the
current Codex profile. All access modes reuse that configuration and login.
Existing MCP settings are retained. Backend GUI permissions remain authoritative.

The first voice transcription downloads the multilingual Whisper model.
Speak, stop recording, review the recognized text and press Send. See
[Desktop application](desktop-app.md) for access modes, cancellation, offline
models and troubleshooting.
