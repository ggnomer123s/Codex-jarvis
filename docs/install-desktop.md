# Desktop installation commands by operating system

These commands install the graphical Tigo app and voice dependencies from
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

## Automatic dependency-aware update: CachyOS and Windows 11

First choose **Quit Tigo**, including the background listener. These bootstrap
commands work before the repository has been cloned as well as for an existing
clean `main` checkout at the usual `Tigo` path. They download the
updater from this repository over HTTPS, check/install prerequisites, clone or
fast-forward the checkout, run the ordinary GUI installer and start Tigo.

CachyOS/Arch, from a normal user terminal (including fish):

```bash
bash -c 'set -e; command -v curl >/dev/null || sudo pacman -Syu --needed --noconfirm curl; f=$(mktemp); cleanup() { rm -f -- "$f"; }; trap cleanup EXIT; curl --proto "=https" --tlsv1.2 -fL https://raw.githubusercontent.com/ggnomer123s/Codex-jarvis/main/scripts/update-cachyos.sh -o "$f"; bash "$f"'
```

Windows 11, from a normal **PowerShell** window (enter `powershell` first in CMD):

```powershell
& { $ErrorActionPreference = 'Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $f = Join-Path ([IO.Path]::GetTempPath()) ('tigo-update-' + [guid]::NewGuid().ToString() + '.ps1'); try { Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/ggnomer123s/Codex-jarvis/main/scripts/update-windows.ps1' -OutFile $f; & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $f; if ($LASTEXITCODE -ne 0) { throw 'Tigo update failed; inspect the error above.' } } finally { Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue } }
```

The scripts install required system/GUI/CPU voice packages, use uv-managed
Python 3.12 with the frozen lock and import-check Qt/transcription dependencies.
They retain a compatible existing Codex CLI and install it through npm if absent;
the CachyOS helper can also replace an unsupported CLI with the user-local npm
installation. A custom unsupported native Windows Codex installation needs its
own upgrade; the script reports this rather than replacing it silently.
Node 22+ is checked. An old Node-manager selection can require selecting the
newly installed version. Existing Codex login/settings/Full Access preferences
are reused; device sign-in runs only when login status requires it.

CachyOS uses `sudo pacman -Syu --needed --noconfirm`, including the normal full
rolling-release system upgrade, to avoid partial upgrades. It may need your sudo
password. Windows uses winget for missing Git/Node/uv and the x64 Visual C++
runtime; App Installer (winget) must
be available. PATH is refreshed in-process after installs. Installer UAC prompts
remain native Windows prompts; Tigo and Codex never run elevated.

Both updaters download the default Russian/English neural speech models (about
134 MB total), verify their pinned checksums and cache them for offline use.
Windows no longer installs a Russian system speech capability or requests TTS
UAC approval. An existing voice cache is reused. Whisper model files download on first voice use, and
the selected third-party MCP can download its own package on first start.
CUDA/editor SDKs and manual OS/portal permissions are outside the default CPU setup.

Custom paths: run the downloaded CachyOS script with a checkout path argument,
or Windows with `-RepoPath 'C:\path\to\checkout'`. Windows accepts
`-SkipRussianVoice` as a compatibility no-op; there is no system voice install. Both scripts
reject another repository, a non-main/detached checkout or local changes rather
than reset/stash/delete work. Git divergence and dependency failures stop the
update. A locked old GUI process can still prevent environment replacement;
quit it first. See [normal updates](#update-an-existing-gui-installation) if the
dependencies are already prepared.

## CachyOS, Arch, Manjaro, EndeavourOS

```bash
sudo pacman -Syu --needed git uv python nodejs npm portaudio libpulse speech-dispatcher espeak-ng grim wtype xdotool wmctrl maim mesa libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
repo_dir="$HOME/Tigo"
if [ -e "$repo_dir/.git" ]; then
  git -C "$repo_dir" pull --ff-only
else
  git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$repo_dir"
fi && bash "$repo_dir/scripts/install-gui-linux.sh" && "$HOME/.local/bin/tigo-gui"
```

## Ubuntu, Debian, Linux Mint, Pop!_OS

```bash
sudo apt update
sudo apt install -y git curl python3 nodejs npm libportaudio2 libpulse0 speech-dispatcher espeak-ng libspeechd2 libegl1 libopengl0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0
curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$HOME/Tigo"
bash "$HOME/Tigo/scripts/install-gui-linux.sh"
"$HOME/.local/bin/tigo-gui"
```

## Fedora

```bash
sudo dnf install -y git curl python3 nodejs npm portaudio pulseaudio-libs speech-dispatcher speech-dispatcher-espeak-ng espeak-ng mesa-libEGL mesa-libGL libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil
curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$HOME/Tigo"
bash "$HOME/Tigo/scripts/install-gui-linux.sh"
"$HOME/.local/bin/tigo-gui"
```

## openSUSE Tumbleweed / Leap 16

```bash
sudo zypper install -y git curl python3 nodejs npm libportaudio2 libpulse0 libEGL1 libOpenGL0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0
curl --proto '=https' --tlsv1.2 -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" login
git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$HOME/Tigo"
bash "$HOME/Tigo/scripts/install-gui-linux.sh"
"$HOME/.local/bin/tigo-gui"
```

The curl command uses uv's official HTTPS installer. uv installs the locked
Python/Qt/voice dependencies without requiring a matching system Python version.
The Linux installers create `~/.local/bin/tigo-gui`, a Tigo application
menu entry and update the ordinary Codex desktop backend. Full Access defaults
on; disable it in Preferences > Access to save a sandbox mode for GUI and regular
CLI launchers. All modes reuse the current Codex login. Keep the checkout in place.

Linux spoken replies use local neural synthesis and PortAudio. Speech Dispatcher
and eSpeak output packages in older recipes are needed only for optional legacy
system mode; see [speech setup](speech-output.md).

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
$repoPath = Join-Path $env:USERPROFILE 'Tigo'
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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoPath 'scripts\tigo-gui-windows.ps1')
```

Tigo also appears in the current user's Start menu. Keep the cloned directory
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

First use **Quit Tigo** to stop the background listener and old GUI process.
If `Tigo` already exists, update it instead of cloning again.
Preserve local edits; `--ff-only` refuses a divergent history.

Linux:

```bash
git -C "$HOME/Tigo" pull --ff-only
bash "$HOME/Tigo/scripts/install-gui-linux.sh"
"$HOME/.local/bin/tigo-gui"
```

Windows 11:

```powershell
git -C "$env:USERPROFILE\Tigo" pull --ff-only
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Tigo\scripts\install-gui-windows.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Tigo\scripts\tigo-gui-windows.ps1"
```

## Spoken replies

Speech is on by default. **Preferences > Speech** offers local neural Dmitri
and Denis for Russian, Joe for English, rate/volume and Test voice. The first
0.7.0 launch resets old system voice IDs and rate/pitch to natural defaults,
preserving Speech off and volume. Default model downloads happen in the full
updaters or on first use with ordinary installers. Windows needs no system
Russian voice; Linux playback uses PortAudio. Pitch is kept natural in neural
mode. Legacy system output remains an explicit option.
The installer updates the managed Tigo Skill and AGENTS character instructions;
start a new conversation after updating. See [speech output](speech-output.md).

## Desktop automation and first voice use

These commands install the frontend, launchers and applicable desktop MCP in the
current Codex profile. All access modes reuse that configuration and login.
Existing MCP settings are retained. Backend GUI permissions remain authoritative.

The first voice transcription downloads the multilingual Whisper model.
Speak, stop recording, review the recognized text and press Send. See
[Desktop application](desktop-app.md) for access modes, cancellation, offline
models and troubleshooting.
