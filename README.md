# JARVIS — cross-platform Codex desktop assistant

A community project that connects **OpenAI Codex CLI** to desktop automation via **Model Context Protocol (MCP)**, and adds a simple **`jarvis` command**, reusable Skills, troubleshooting instructions, and optional error monitoring.

> Not an official OpenAI product. Desktop automation has significant privacy and security implications. Desktop MCPs are independent upstream projects and capabilities vary by display server and compositor.

## Supported environments

| Operating system / desktop | GUI backend | Status |
|---|---|---|
| Linux — Hyprland (Wayland) | [Hypruse](https://github.com/IlyasKhallouki/hypruse) | Working user setup; automatic configuration |
| Linux — **GNOME Wayland**, **KDE Plasma Wayland** | [Wayland MCP](https://github.com/kurojs/wayland-mcp) via desktop portals | **Experimental**; portal + PyGObject prerequisites |
| Linux — Sway, River, Niri, COSMIC, other Wayland compositors | Wayland MCP, capability dependent | **Experimental / partial**; no guarantee of pointer control |
| Linux — GNOME on Xorg, KDE X11, XFCE, Cinnamon, MATE, i3, Openbox, bspwm | Bundled `jarvis-x11` (xdotool/maim/wmctrl) | Implemented, **not hardware-tested** |
| Windows 11 | [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) | Installer available; not hardware-tested |

**Distribution coverage** is not limited to Arch/CachyOS. See [Linux installation](docs/linux.md) for Debian, Ubuntu, Linux Mint, Fedora, openSUSE, Arch Linux, Manjaro, EndeavourOS, CachyOS and other Linux distributions. Most of the project is user-space; distro differences are system packages and active graphical session.

## How it works

```text
jarvis → Codex CLI → GUI MCP → active desktop
                    ↘ Skills + AGENTS.md
optional watcher → event logs → read-only Codex analysis report
```

**Important:** Codex does **not** watch your screen continuously. GUI MCP tools are called during an active agent task. The optional monitor only checks specific OS event sources and never auto-repairs.

## Linux quick start

Install and sign in to [Codex CLI](https://github.com/openai/codex). Install `git` and `uv` / `uvx`, then the display-specific native tools from [the Linux guide](docs/linux.md).

```bash
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
bash scripts/install-linux.sh
```

Open a new terminal and run:

```bash
jarvis
```

For **native X11 only**, mouse/keyboard MCP actions are off by default. To opt in after reviewing the [security guide](docs/security.md):

```bash
bash scripts/install-linux.sh --enable-gui-input
```

This option affects **new registrations** only. An existing MCP configuration is intentionally not overridden.

> For GNOME/KDE and generic Wayland, the installer registers a backend but **cannot guarantee** your portal supports both screenshots and remote input. Check `describe_environment` inside the MCP and see [advanced backend setup](docs/mcp-and-skills.md). No `/dev/input` permission change is performed.

## Windows 11 quick start

Open PowerShell on Windows (not WSL), install Git, Node.js LTS and uv, then install Codex. Full steps: [Windows 11 guide](docs/windows11.md).

```powershell
winget install -e --id Git.Git
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id astral-sh.uv
# Reopen PowerShell
npm.cmd install -g @openai/codex
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
# Reopen PowerShell, then: jarvis
```

## Memory and voice input

Both are opt-in and cross-platform. No always-on microphone or automatic memory capture.

```sh
jarvis voice                   # local push-to-talk Whisper transcription, confirm before sending
jarvis memory add              # save a manually verified repair
jarvis memory search dolphin   # search your previous confirmed fixes
jarvis memory list             # inspect saved notes
jarvis memory forget <id>      # delete one note (confirmation required)
```

Microphone dependencies: Linux requires a PortAudio runtime (such as `libportaudio2` or `portaudio`); Windows uses the PortAudio runtime provided with the sounddevice wheel when available. On first voice use, uv downloads dependencies and faster-whisper downloads the multilingual Whisper model. The recorded audio is processed locally and not stored on disk by this feature. **The recognized text is sent to Codex only after you type YES.**

Confirmed-fix memory remains on **your own device**, not in this GitHub repository; it is read only as troubleshooting history and is never automatically populated. See the [Memory & Voice guide](docs/memory-and-voice.md).

## Access to existing desktop applications (Hyprland)

Hypruse's default `HYPRUSE_CONFINE=launched` refuses to control windows opened before the agent. You can **explicitly** allow Telegram and kitty without granting access to every window:

```bash
bash scripts/hypruse-access.sh telegram
```

The command shows current MCP settings, requires typing `APPLY`, backs up your Codex config and switches to `HYPRUSE_CONFINE=class:org.telegram.desktop,kitty`. Restart Codex afterwards. To restore the default, run `bash scripts/hypruse-access.sh restricted`.

This is intentionally **not enabled by default**: messaging and terminal windows can contain sensitive content. You can restrict access to a single app using `bash scripts/hypruse-access.sh allow org.telegram.desktop`. See the [Hypruse application access guide](docs/hypruse-access.md) for scope, rollback and safety details.

## Performance modes

The default `jarvis` launcher now favors responsive desktop actions: it sets **Codex reasoning effort to low**, starts with **no automatic screen-inspection prompt**, and installs a shorter Skill that prefers semantic UI tools over repeated screenshots.

```sh
jarvis           # Fast default
jarvis fast      # Explicit fast mode
jarvis normal    # Your normal Codex reasoning setting
jarvis deep      # Medium reasoning for difficult problems
```

Use `jarvis normal` if the selected model does not support low reasoning effort. Speed varies with model/MCP approvals, accessibility and application behavior. Read [Performance tuning](docs/performance.md).

## Commands

| Command | What it does |
|---|---|
| `jarvis` / `jarvis fast` | Start Codex with low reasoning effort; no automatic inspection task |
| `jarvis normal` / `jarvis deep` | Default reasoning / medium reasoning for complex troubleshooting |
| `jarvis status` | Show configured GUI MCP and monitoring status |
| `jarvis gui-check` | Check GUI backend and navigation prerequisites |
| `jarvis reports` | List diagnostic reports |
| `jarvis monitor on` / `jarvis monitor off` | Enable/disable an installed watcher |
| `jarvis test` | Linux: simulate a failed **systemd user** service |
| `jarvis stop` | Hyprland: stop Hypruse; other platforms: exit Codex |

## Guides

- [Linux installation for Debian/Ubuntu, Fedora, Arch, openSUSE and more](docs/linux.md)
- [Desktop environment support and MCP/Skill setup](docs/mcp-and-skills.md)
- [High-accuracy GUI navigation: semantic controls, screenshots and zoom](docs/gui-navigation.md)
- [Performance tuning: fast mode and fewer model/tool round trips](docs/performance.md)
- [Windows 11 setup](docs/windows11.md)
- [Daily usage and end-to-end testing](docs/usage.md)
- [Security, permissions and privacy](docs/security.md)

## Validation status

The Linux installer and X11 MCP are new cross-desktop additions. They are not claimed tested on every distro. Your exact compositor, Wayland portal backend, Python distribution packages and Codex version can affect functionality. Report reproducible bugs with `echo $XDG_SESSION_TYPE`, `echo $XDG_CURRENT_DESKTOP`, `jarvis status` (after removing personal data).

## Credits

This project glues together third-party software; it does not own upstream MCP implementations. See the respective upstream repositories and their licenses. Source code is published here for review before installation.
