# JARVIS — cross-platform Codex desktop assistant

Implementation history and verification results: [changes.md](changes.md).

A community project that connects **OpenAI Codex CLI** to desktop automation via **Model Context Protocol (MCP)**, and adds a simple **`jarvis` command**, reusable Skills, troubleshooting instructions, and optional error monitoring.

## JARVIS desktop app — Linux and Windows 11

A native desktop interface is now available: an original animated woven-light core,
streaming Codex app-server chat with continuing conversation context, task cancellation, model/workspace
and reasoning settings, Full Access on by default with a saved settings checkbox, and local
push-to-talk transcription with a warm model and 15 language presets including Russian. Voice text is
reviewed before sending. The app uses your existing Codex login and MCP setup.

The GUI now keeps an owned **Codex app-server** connection between messages,
keeps Whisper ready between recordings, and includes checked desktop workflow
aliases, timing export, optional adaptive reasoning and scoped conversation
checkpoints. **Preferences > Runtime / Automation** exposes the new controls.
See [runtime guide](docs/runtime.md) and the [source review of other Jarvis,
Codex and OpenCode projects](docs/related-projects.md). Codex app-server is the
GUI's only model transport; there is no OpenCode runtime or exec fallback.

**Conversation tools:** resize the chat pane, hide the core or switch to full
chat, read Markdown and copy code, edit requests into the draft, preview dragged
files/clipboard screenshots, and search/pin/rename local conversations. A status
card shows the current activity, elapsed time and errors. See the
[GUI controls and history guide](docs/gui-conveniences.md).

**Optional voice activation:** enable **Preferences > Wake** to listen locally
for Jarvis or its Russian name and restore the app from the background. Includes
tolerant matching, microphone/model/language settings and per-user login startup.
The microphone stays on while enabled; ordinary transcripts are discarded and
waking opens the window without submitting a task. See [voice activation](docs/voice-activation.md).

![JARVIS desktop app](docs/images/jarvis-desktop.png)

The central letter has been replaced with an energy sculpture: filament orbits,
audio-reactive motion, action trails and verification sweeps follow the actual
runtime state. See the [animated preview and state guide](docs/desktop-app.md#animated-activity-core).

```bash
# Linux, from this checkout
bash scripts/jarvis-gui-linux.sh
```

```powershell
# Windows 11, from this checkout
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\jarvis-gui-windows.ps1
```

Install `uv` and Codex CLI, then run `codex login` first. Separate Linux application
menu and Windows Start menu installers are provided. See [Desktop application](docs/desktop-app.md)
for prerequisites, installation, permissions and validation limits. The current
release runs from source; signed standalone installers are not yet provided.

### Fresh installation by operating system

Copy-ready commands, including dependencies, Codex login and menu installation:

| Operating system | Installation commands |
|---|---|
| CachyOS, Arch, Manjaro, EndeavourOS | [Arch-family installation](docs/install-desktop.md#cachyos-arch-manjaro-endeavouros) |
| Ubuntu, Debian, Linux Mint, Pop!_OS | [Debian-family installation](docs/install-desktop.md#ubuntu-debian-linux-mint-pop_os) |
| Fedora | [Fedora installation](docs/install-desktop.md#fedora) |
| openSUSE Tumbleweed / Leap 16 | [openSUSE installation](docs/install-desktop.md#opensuse-tumbleweed--leap-16) |
| Windows 11 | [Windows installation](docs/install-desktop.md#windows-11) |

If you already cloned `Codex-jarvis-gui`, use the [update commands](docs/install-desktop.md#update-an-existing-gui-installation).

GUI and CLI use your current Codex profile and existing sign-in. Full Access is
on by default. Disable it in **Preferences > Access**; the saved setting also
applies to the regular `jarvis` CLI. Model and reasoning pickers are at the
bottom left of the composer.
For Windows, the [installation instructions](docs/install-desktop.md#windows-11)
use an explicit checkout path and work from your user directory as well.

> Not an official OpenAI product. Desktop automation has significant privacy and security implications. Desktop MCPs are independent upstream projects and capabilities vary by display server and compositor.

## Start here: project handoff for another AI

**Continuation status — 2026-10-14.** This README is the project's public entry point. A much more detailed, source-checked maintainer handoff is maintained at **[docs/AI_HANDOFF.md](docs/AI_HANDOFF.md)**. If you are an AI coding agent taking over JARVIS, read **both files**, then fetch the latest source, tests and GitHub Actions output before making changes. The code always takes precedence over any dated summary.

### What we are building

JARVIS is a **Codex CLI-based AI computer operator** with terminal and native desktop interfaces. Codex supplies model reasoning. It should understand requests and **use the computer**: open/focus applications, interact visually through mouse/keyboard/accessibility, edit video projects where supported, diagnose Linux/Windows problems, write code and manage files. For large tasks, it should favor reliable native application APIs/shell tools alongside GUI interactions. The human should not have to spell out every mouse click. Reliable outcome verification matters more than spectacular-looking cursor motion.

**Architecture at a glance:**

```text
User text / optional push-to-talk
      |
      v
GUI (owned app-server) / terminal jarvis or jarvis-full
      |
      v
OpenAI Codex CLI + managed AGENTS.md + jarvis-desktop Skill
      |
      +---- GUI MCP: Hypruse (Hyprland), jarvis-x11 (X11),
      |               wayland-mcp-kurojs (experimental Wayland),
      |               Windows-MCP (Windows 11)
      |
      +---- Native shell / application APIs, where appropriate
      |
      +---- Optional user-confirmed repair memory and read-only monitors
      |
      v
Observed result / user-facing report
```

### Features already added to the source

| Area | Implemented source and behavior |
|---|---|
| Linux and Windows installers | `scripts/install-linux.sh` and `scripts/install-windows.ps1`; detect/register appropriate desktop MCP, install user-facing launchers and Skills |
| Native desktop frontend | `gui/`; streaming app-server chat, live model selection, scoped conversation resume, Full Access checkbox, Markdown/code copy, reviewed attachments, searchable local history, warm multilingual voice, workflows and timings |
| Reasoning profiles | `jarvis` / `fast` = `low`; `normal` = configured default; `deep` = `high` |
| Shared profile and access | One `CODEX_HOME` / login / MCP configuration; Full Access defaults on, with a saved GUI/CLI access setting and compatibility `jarvis-full` aliases |
| GUI intelligence | `skills/jarvis-desktop/SKILL.md` and `config/jarvis-agents.md`; **instruction-based** selection of actual GUI tools for visual tasks, semantic-first navigation, region capture, mouse drag selection and keyboard shortcuts |
| Window permissions | `scripts/hypruse-access.sh`; optional `jarvis access all` or restricted/class-based Hypruse permissions, with explicit confirmation and config backup |
| Native X11 desktop MCP | `scripts/x11_mcp.py`; screenshots, region crops, human-selected capture rectangle, focus-checked shortcuts, pointer click/drag/scroll and configurable input |
| Voice | `gui/jarvis_gui/voice.py` warm worker; `scripts/jarvis_voice.py` one-shot CLI; local faster-whisper, review before submission |
| Voice activation | Optional `wake.py` background local transcription; English/Russian tolerant name matching restores the GUI, with tray controls and user-level sign-in startup |
| Repair memory | `scripts/jarvis_memory.py`; local JSON of **explicitly confirmed** fixes, manual add/search/list/delete |
| Diagnostics | `jarvis gui-check`; opt-in Linux systemd-user and Windows Application event watchers; read-only Codex analysis reports |
| Maintenance | `scripts/sync_agents.py` refreshes only JARVIS's AGENTS block with backups; GitHub Actions checks Bash/PowerShell/Python/tests |

**Access behavior:** JARVIS defaults to Full Access under the current user account. Disable it in Preferences > Access to use a shell sandbox; that choice persists across restarts and is shared with regular CLI launchers. All modes reuse `CODEX_HOME` or `~/.codex`. Full Access does not grant root/Administrator privileges or bypass OS authentication, locked sessions or MCP-specific guards.

### Important bugs already investigated

- **Spotify/Firefox refused clicks** when Hypruse was configured with `HYPRUSE_CONFINE=class:org.telegram.desktop,kitty`. Visible windows and screenshots did not imply input permission. The explicit `jarvis access all` profile removes the filter; new registrations omit the confinement filter; existing registrations retain it.
- **Red borders** came from upstream Hypruse `HYPRUSE_MARK=1`. New registrations and access profiles now set `HYPRUSE_MARK=0`; old runtime rules may require a user-approved `hyprctl reload`.
- **Sluggish screenshot loops** led to a smaller GUI Skill preferring `desktop`, `ui`, `click_ui`, `sequence`, `wait_for`, targeted screenshot/zoom and meaningful final verification. This is a behavioral improvement, **not a measured performance benchmark**.
- **X11 shortcut focus** and missing drag/region capture were addressed with focus checks, bounded screenshot regions, drag cleanup, regression tests and support for negative monitor coordinates.
- **Stale AGENTS.md** after reinstalls and **misplaced Full Access Skill** were corrected in installers. Full Access now supports `fast|normal|deep` without an extra startup task.

### What is NOT implemented yet

General **task replay/rollback**, **JARVIS Doctor auto-repair**, an **application-specific Premiere Pro/DaVinci editing bridge**, **continuous video understanding**, and full-duplex spoken conversation remain unimplemented. Optional local background wake-name detection now opens the GUI without starting tasks. The GUI now provides content-free task/voice timings, an optional local reasoning heuristic, connection/MCP diagnostics, checked short workflows and explicit conversation checkpoint resume. Conversation resume does not replay desktop actions. Do not claim visual-agent benchmark superiority over [Microsoft UFO](https://github.com/microsoft/UFO), [Agent-S](https://github.com/simular-ai/Agent-S) or [E2B Desktop](https://github.com/e2b-dev/desktop); validation is mostly static/unit CI and simulated desktop-frontend tests, plus a Linux app-server handshake/config probe, not broad hardware-level testing.

### Instructions for the next coding agent

1. Read **[the full AI handoff](docs/AI_HANDOFF.md)** and the implementation files related to the requested change, not only this overview.
2. Preserve the existing user setup and shared Codex home; diagnose before altering working MCP registrations or OS settings.
3. When a user asks to operate an application, use an authorized GUI MCP if it exists; when deterministic APIs are more reliable, use them. Verify actions rather than inventing outcomes.
4. For code changes, update related tests/docs and check the latest GitHub Actions result. Do not mistake a green syntax/unit-test run for successful real-world visual automation.
5. Update this README and the detailed handoff whenever architecture, supported commands, known problems or major milestones change. Record every change and its actual validation in [changes.md](changes.md).

**Source-of-truth files:** [main CLI installers](scripts/) · [GUI Skill](skills/jarvis-desktop/SKILL.md) · [managed agent rules](config/jarvis-agents.md) · [tests](tests/) · [CI workflow](.github/workflows/validate.yml) · [complete technical handoff](docs/AI_HANDOFF.md).

---

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

New **native X11** registrations enable desktop input by default. Existing registrations retain their configured permissions. The legacy input flag remains accepted:

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

Both are opt-in and cross-platform. CLI voice uses push-to-talk. The GUI also
offers a separate, explicitly enabled [background wake listener](docs/voice-activation.md).
Repair memory is never populated automatically.

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

An existing Hypruse registration with `HYPRUSE_CONFINE=launched` refuses to control windows opened before the agent. New installations omit this filter. You can **explicitly** allow Telegram and kitty without granting access to every window:

```bash
bash scripts/hypruse-access.sh telegram
```

The command shows current MCP settings, requires typing `APPLY`, backs up your Codex config and switches to `HYPRUSE_CONFINE=class:org.telegram.desktop,kitty`. Restart Codex afterwards. To explicitly restrict control to agent-launched windows, run `bash scripts/hypruse-access.sh restricted`.

These helpers deliberately replace the selected MCP registration after review; reinstalling alone preserves it. You can restrict access to a single app using `bash scripts/hypruse-access.sh allow org.telegram.desktop`. See the [Hypruse application access guide](docs/hypruse-access.md) for scope, rollback and safety details.

## Performance modes

The default `jarvis` launcher now favors responsive desktop actions: it sets **Codex reasoning effort to low**, starts with **no automatic screen-inspection prompt**, and installs a shorter Skill that prefers semantic UI tools over repeated screenshots.

```sh
jarvis           # Fast default
jarvis fast      # Explicit fast mode
jarvis normal    # Your normal Codex reasoning setting
jarvis deep      # High reasoning for debugging, coding, long editing tasks
jarvis full      # Explicit Full Access using the same Codex profile
```

Use `jarvis normal` if the selected model does not support low reasoning effort. Speed varies with model/MCP approvals, accessibility and application behavior. Read [Performance tuning](docs/performance.md).

## One Codex profile and access settings

All installers, GUI and terminal launchers reuse `CODEX_HOME`, or `~/.codex`
when it is unset. Sign in once with `codex login`; changing access never switches
accounts or requires another login. Full Access is on by default. Turn it off in
**Preferences > Access** for read-only or workspace-edit shell access; the saved
setting also applies to `jarvis fast|normal|deep`. Existing MCP registrations and
OS authentication remain authoritative.

Old `install-full-*` entry points now delegate to the ordinary installer.
`jarvis-full` / `jarvis full` explicitly request Full Access in the same profile.
No private profile is created or migrated and credentials are not copied.
See [Full Access and migration](docs/full-access.md).

## Intent-driven desktop automation and selecting regions

JARVIS now explicitly routes requests that describe visible app interaction to the available GUI MCP tools: opening windows, choosing playlists, switching tabs, dragging or selecting content in file managers, browsers and creative editors. For batch file processing and development it can still use deterministic native APIs and shell tools. This behavior is guided by the installed [Desktop Skill](skills/jarvis-desktop/SKILL.md) and versioned managed agent rules.

**Two meanings of region selection:** `drag` changes a selection inside an application; `screenshot_region` (or Hypruse `screenshot(region=...)`) captures pixels without touching the app. Linux X11 additionally has `user_select_screenshot` so the person can draw a capture rectangle. Hypruse and Windows-MCP already supply native pointer drags and region screenshots, so no duplicate pointer backend is installed on those systems.

Read [GUI Operator](docs/gui-operator.md) for platform examples and the design comparison with Microsoft UFO, Agent-S, E2B Desktop and Windows-MCP.

## Commands

| Command | What it does |
|---|---|
| `jarvis` / `jarvis fast` | Start Codex with low reasoning effort; no automatic inspection task |
| `jarvis normal` / `jarvis deep` | Model's configured default / high reasoning for complex tasks |
| `jarvis-full fast` / `normal` / `deep` | Explicit Full Access with low / configured default / high reasoning in the shared profile |
| `jarvis full fast` / `normal` / `deep` | Aliases to the same Full Access modes |
| `jarvis access status` / `jarvis access all` | Hyprland-only: inspect or change Hypruse window permissions with confirmation |
| `jarvis status` | Show configured GUI MCP and monitoring status |
| `jarvis gui-check` | Check GUI backend and navigation prerequisites |
| `jarvis reports` | List diagnostic reports |
| `jarvis monitor on` / `jarvis monitor off` | Enable/disable an installed watcher |
| `jarvis test` | Linux: simulate a failed **systemd user** service |
| `jarvis stop` | Hyprland: stop Hypruse; other platforms: exit Codex |

## Guides

- [Native desktop app for Linux and Windows 11](docs/desktop-app.md)
- [Copy-ready installation commands by operating system](docs/install-desktop.md)
- [Linux installation for Debian/Ubuntu, Fedora, Arch, openSUSE and more](docs/linux.md)
- [Desktop environment support and MCP/Skill setup](docs/mcp-and-skills.md)
- [High-accuracy GUI navigation: semantic controls, screenshots and zoom](docs/gui-navigation.md)
- [Intent-driven GUI Operator and drag/region selection](docs/gui-operator.md)
- [Keyboard shortcuts on Hyprland, Linux X11 and Windows](docs/shortcuts.md)
- [Shared profile and Full Access](docs/full-access.md)
- [Performance tuning: fast mode and fewer model/tool round trips](docs/performance.md)
- [Persistent app-server, warm voice, checked workflows and timings](docs/runtime.md)
- [Other Jarvis/Codex/OpenCode projects: checked sources and design decisions](docs/related-projects.md)
- [Windows 11 setup](docs/windows11.md)
- [Daily usage and end-to-end testing](docs/usage.md)
- [Security, permissions and privacy](docs/security.md)

## Validation status

The Linux installer and X11 MCP are new cross-desktop additions. They are not claimed tested on every distro. Your exact compositor, Wayland portal backend, Python distribution packages and Codex version can affect functionality. Report reproducible bugs with `echo $XDG_SESSION_TYPE`, `echo $XDG_CURRENT_DESKTOP`, `jarvis status` (after removing personal data).

## Credits

This project glues together third-party software; it does not own upstream MCP implementations. See the respective upstream repositories and their licenses. Source code is published here for review before installation.
