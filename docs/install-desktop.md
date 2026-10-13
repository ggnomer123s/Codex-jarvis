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

## CachyOS, Arch, Manjaro, EndeavourOS

```bash
sudo pacman -Syu --needed git uv python nodejs npm portaudio mesa libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$HOME/Codex-jarvis-gui"
bash "$HOME/Codex-jarvis-gui/scripts/install-gui-linux.sh"
"$HOME/.local/bin/jarvis-gui"
```

## Ubuntu, Debian, Linux Mint, Pop!_OS

```bash
sudo apt update
sudo apt install -y git curl python3 nodejs npm libportaudio2 libegl1 libopengl0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0
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
sudo dnf install -y git curl python3 nodejs npm portaudio mesa-libEGL mesa-libGL libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil
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
sudo zypper install -y git curl python3 nodejs npm libportaudio2 libEGL1 libOpenGL0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0
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
The Linux installers create `~/.local/bin/jarvis-gui` and a JARVIS application
menu entry. Keep the cloned directory in place.

## Windows 11

Install prerequisites:

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
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$env:USERPROFILE\Codex-jarvis-gui"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Codex-jarvis-gui\scripts\install-gui-windows.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Codex-jarvis-gui\scripts\jarvis-gui-windows.ps1"
```

JARVIS also appears in the current user's Start menu. Keep the cloned directory
in place. Microphone access can be enabled in Windows Privacy settings.

## Update an existing GUI installation

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

## Desktop automation and first voice use

These commands install the frontend. For mouse/keyboard control, use the existing
[Linux backend setup](linux.md) or [Windows backend setup](windows11.md) to
configure the appropriate MCP in the normal Codex profile. Existing MCP settings
are retained. GUI input permissions remain dependent on that backend.

The first voice transcription downloads the multilingual Whisper model.
Speak, stop recording, review the recognized text and press Send. See
[Desktop application](desktop-app.md) for access modes, cancellation, offline
models and troubleshooting.
