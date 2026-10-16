# Linux installation — Debian, Ubuntu, Fedora, Arch, openSUSE and more

Tigo is **distribution-independent** at the application level. What matters most is your graphical session (**X11 vs Wayland**) and the GUI MCP backend that can interact with it.

## 1. Detect your environment

Run these commands **inside a graphical desktop terminal** (not over SSH):

~~~sh
echo "$XDG_SESSION_TYPE"
echo "$XDG_CURRENT_DESKTOP"
echo "$DESKTOP_SESSION"
command -v codex
command -v uv
command -v uvx
~~~

Examples:
- Ubuntu 24.04/26.04 with GNOME typically uses **GNOME Wayland** unless the user selects Xorg.
- Debian GNOME may be Wayland or X11 depending on version, GPU, and login session.
- Fedora Workstation usually uses **GNOME Wayland**; KDE spin uses **Plasma Wayland**.
- Linux Mint Cinnamon, XFCE, MATE and traditional window managers may run on **X11** (verify).
- Arch, EndeavourOS, CachyOS, Manjaro and openSUSE can run **either** display server.
- Hyprland always uses Wayland, while i3, Openbox and bspwm are X11 WMs. Sway and Niri use Wayland.

**Do not infer your session from the distribution name.**

## 2. Install prerequisites

You need an installed, signed-in [Codex CLI](https://github.com/openai/codex), Git and [uv](https://docs.astral.sh/uv/getting-started/installation/) (provides **uv** and **uvx**). If `uvx` is missing, install uv from a trusted package manager, pipx or the official upstream instructions. Do not use `sudo pip install`.

### Debian / Ubuntu / Linux Mint / Pop!_OS

~~~sh
sudo apt update
sudo apt install git
# For X11:
sudo apt install xdotool wmctrl maim
# For Hyprland if it is your session:
sudo apt install grim wtype
# For GNOME/KDE Wayland portal fallbacks:
sudo apt install xdg-desktop-portal python3-gi
~~~

Also install the portal backend for your current desktop (for example `xdg-desktop-portal-gnome` or `xdg-desktop-portal-kde` where available). Package names and availability depend on release. For screenshots you may need `gnome-screenshot` (GNOME) or `spectacle` (Plasma).

### Fedora

~~~sh
sudo dnf install git
# X11:
sudo dnf install xdotool wmctrl maim
# Hyprland:
sudo dnf install grim wtype
# GNOME/KDE Wayland:
sudo dnf install xdg-desktop-portal python3-gobject
~~~

Use the corresponding `xdg-desktop-portal-gnome` / `xdg-desktop-portal-kde` packages if available.

### Arch Linux / EndeavourOS / Manjaro / CachyOS

~~~sh
sudo pacman -S --needed git uv
# X11:
sudo pacman -S --needed xdotool wmctrl maim
# Hyprland:
sudo pacman -S --needed grim wtype
# GNOME/KDE Wayland:
sudo pacman -S --needed xdg-desktop-portal python-gobject
~~~

Use `xdg-desktop-portal-gnome` for GNOME, `xdg-desktop-portal-kde` for Plasma and the appropriate compositor-specific portal where available.

### openSUSE Tumbleweed / Leap

~~~sh
sudo zypper install git
# X11:
sudo zypper install xdotool wmctrl maim
# Hyprland:
sudo zypper install grim wtype
# Wayland:
sudo zypper install xdg-desktop-portal python3-gobject
~~~

Some openSUSE editions use different package names; search with `zypper search` before installing. Install uv from the official installation instructions if your repositories do not provide it.

### Other distributions

Install `git`, `uv`, `codex` plus:
- Hyprland: `grim`, `wtype`, Hyprland IPC tools;
- X11: `xdotool`, `wmctrl`, `maim`;
- GNOME/KDE/other Wayland: `xdg-desktop-portal`, matching desktop portal backend, optional PyGObject/desktop screenshot helpers.

Do **not** modify `/dev/input` permissions or install a privileged `ydotoold` daemon just to make the wizard say “success.”

## 3. Install Tigo

~~~sh
git clone https://github.com/ggnomer123s/Codex-jarvis.git Tigo
cd Tigo
bash scripts/install-linux.sh
~~~

The installer chooses a backend based on `XDG_SESSION_TYPE` and `XDG_CURRENT_DESKTOP`:
- **Hyprland/Wayland:** registers Hypruse, preserving your existing registration and its security flags.
- **X11:** adds the bundled `tigo-x11` MCP, which supports screenshots, window enumeration, focus, keyboard and mouse via xdotool. **Input is enabled for new registrations**; existing permissions are preserved.
- **Other Wayland:** registers upstream `wayland-mcp-kurojs` via uvx as an **experimental** backend. It probes compositor capabilities; usable screenshot/input may require extra portal dependencies or permissions.
- Unknown/headless session: installs launcher/Skill, skips GUI MCP.

It also installs the Tigo Skill, appends user-level Codex instructions and, if a **systemd --user** instance is available, installs the *optional* watcher. It does **not** install system packages or require root.

All launchers and the GUI reuse `CODEX_HOME` or `~/.codex`, including its login
and MCP settings. Full Access defaults on; disable it in GUI Preferences >
Access to save a sandbox mode for the GUI and regular `tigo` command.

Open a new terminal:

~~~sh
tigo
~~~

### Enable X11 GUI input

New X11 installations enable input. The legacy option remains accepted:

~~~sh
bash scripts/install-linux.sh --enable-gui-input
~~~

**Existing MCP registrations are deliberately preserved**, so if `tigo-x11` was already registered in read-only mode, you must explicitly remove that server after inspecting it, then rerun the installer:

~~~sh
codex mcp get tigo-x11
codex mcp remove tigo-x11
bash scripts/install-linux.sh --enable-gui-input
~~~

Review the registration before deliberately changing it.

## 4. GNOME, KDE Plasma and other Wayland sessions

A configured Wayland MCP is **not proof that GUI control works**. The upstream generic backend prefers the `org.freedesktop.portal.RemoteDesktop` API for input and a screenshot portal/native tool for capture.

- **GNOME Wayland**: uses portals; [GNOME Desktop MCP](https://github.com/sbuysse/gnome-desktop-mcp) is a separate optional native alternative requiring a GNOME Shell extension, GNOME Shell 45–49 and Python 3.12+.
- **KDE Plasma 6 Wayland**: portals are one route; [kwin-mcp](https://github.com/isac322/kwin-mcp) is an optional native alternative for virtual or live KWin sessions.
- **Sway/Hyprland/wlroots**: screenshots may work via `grim` but RemoteDesktop portal pointer input is frequently unavailable; Hypruse is preferred **for Hyprland only**.
- **Niri, River, COSMIC and others**: capabilities vary by compositor, supported portal, and screenshot method. No universal promise of full control.

**PyGObject note:** `uvx` uses an isolated Python environment, so it may not see your distro's `python3-gi` package. If portal calls are missing, check [the advanced MCP guide](mcp-and-skills.md) for a `uv venv --system-site-packages` configuration. Never make input devices world-writable.

## 5. Optional voice and memory

`tigo voice` records only when you press Enter. It transcribes audio locally using the multilingual Whisper **base** model and asks for explicit YES before forwarding the text to Codex.

Install the OS PortAudio runtime first: Debian/Ubuntu: `sudo apt install libportaudio2`, Fedora: `sudo dnf install portaudio`, Arch-based: `sudo pacman -S --needed portaudio`. See the openSUSE-specific package search in [Memory & Voice](memory-and-voice.md).

`tigo memory add`, `tigo memory search <keyword>` and `tigo memory forget <id>` manage manually confirmed solutions without cloud syncing or auto-learning. The installer does not import older conversations into memory.

See [Memory & Voice](memory-and-voice.md) for first-run downloads, privacy and microphone troubleshooting.

## 6. Verify and troubleshoot

~~~sh
tigo status
codex mcp list
# Hyprland:
uvx hypruse doctor
# All:
tigo
~~~

In Codex: “Discover desktop MCP tools. Report available screenshot, window and input capabilities. Inspect the active window without changing anything.”

Then run a harmless notepad/terminal text-input test after checking the actual tool permissions in your environment.

### Monitoring (systemd user services only)

The watcher polls **failed user systemd services** every two minutes and may send diagnostic logs to Codex for read-only analysis. It is **not** a general crash detector; it does not automatically repair anything.

~~~sh
tigo status
tigo reports
tigo monitor off
tigo monitor on
tigo test
~~~

`tigo test` creates a short-lived failing test user-service then clears the failed state. If your distribution doesn't use systemd --user, the watcher is skipped; GUI tools can still work.

### Paths and shells

The installed script is `~/.local/bin/tigo`. Fish gets `~/.config/fish/functions/tigo.fish`. For Bash or Zsh ensure `~/.local/bin` is in PATH (the installer adds a managed PATH line to your interactive shell configuration when needed).

## 7. Safety

Screenshot and log content may include private data. All desktop MCPs are third-party programs with powerful local access. On X11 any sufficiently privileged client can typically observe and inject input across windows, so enabling input affects other applications on the display. On Wayland, portals mediate permissions differently by compositor.

Review [Security](security.md) and [MCP configuration](mcp-and-skills.md) before using on a real desktop.
