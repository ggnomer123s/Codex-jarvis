# JARVIS desktop application

A native Qt Quick window for Linux and Windows 11, with an animated cyan core,
a conversation panel, workspace selection, reasoning presets and push-to-talk
voice input. The same interface runs on both platforms; platform-specific
launchers and menu installers are provided. This is a source distribution,
not a signed standalone EXE, AppImage, DEB or RPM release.

![JARVIS desktop command center](images/jarvis-desktop.png)

## Prerequisites

- Install Git, [uv](https://docs.astral.sh/uv/getting-started/installation/)
  and [Codex CLI](https://github.com/openai/codex).
- Run `codex login` in your normal terminal before sending requests.
- Python 3.11 through 3.14 is supported. uv can provision a compatible Python.
- For actual desktop operations, set up the normal JARVIS desktop MCP using
  the existing [Linux](linux.md) or [Windows](windows11.md) instructions.
  The frontend uses existing Codex authentication, instructions and MCP entries;
  it does not register or change them.

## Linux

From the repository root:

```bash
bash scripts/jarvis-gui-linux.sh
```

The first launch installs the locked Qt and voice dependencies in `gui/.venv`.
For a launcher in your application menu and a `~/.local/bin/jarvis-gui` command:

```bash
bash scripts/install-gui-linux.sh
```

Keep the checkout at its current path: the menu entry points to it. Re-run the
installer if you move it. It installs only current-user menu/launcher files and
preserves unrelated files with the same names. Remove those two generated files
to uninstall the menu entry; existing CLI JARVIS configuration is unaffected.

Qt requires a graphical X11 or Wayland session and its native platform libraries.
Install missing runtime libraries using your distribution's package manager.
Typical Debian/Ubuntu packages are `libegl1`, `libopengl0`, `libxcb-cursor0`,
`libxkbcommon-x11-0` and `libportaudio2`. Fedora commonly uses `mesa-libEGL`,
`libxcb`, `xcb-util-cursor`, `libxkbcommon-x11` and `portaudio`; Arch uses
`mesa`, `libxcb`, `xcb-util-cursor`, `libxkbcommon-x11` and `portaudio`.
Package names vary by release. If a Wayland session fails to select its Qt
platform plugin, try `QT_QPA_PLATFORM=wayland bash scripts/jarvis-gui-linux.sh`;
use `xcb` only when an X display is available.

The UI is designed for Linux distributions supported by Qt, rather than tied
to one desktop compositor. Actual GUI automation still depends on the configured
MCP's capabilities. Every distribution/compositor combination has not been tested.

## Windows 11

Open a normal PowerShell window at the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\jarvis-gui-windows.ps1
```

For a Start menu shortcut that opens the window without a console:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-gui-windows.ps1
```

The shortcut uses the project's virtual-environment `pythonw.exe`. Keep the
checkout in place. Remove `JARVIS.lnk` from your current-user Start menu to remove
the shortcut. No Administrator session or global execution-policy changes are
required. The npm `codex.cmd` installation is launched through its Node entry
point, avoiding shell interpolation of paths or requests.

## Use the app

1. Choose **Workspace**. This is the working directory for Codex requests.
2. Type a request and press **Send** or Enter. Shift+Enter inserts a new line.
3. Replies appear in the conversation panel. Command/MCP activity appears below
   the animated core. Follow-up requests resume the current Codex thread.
4. **Stop** or Escape cancels the active task. Completed actions are not undone.
5. **New conversation** or Ctrl+N starts a fresh context. Changing the workspace
   or access mode also resets the context.

Preferences offer Fast (`low`), Normal (existing Codex default) and Deep (`high`)
reasoning. Choose Normal if your configured model does not support low reasoning.
Workspace access defaults to **Observe only** (`read-only`). **Allow workspace
edits** explicitly selects `workspace-write` for the chosen folder. This frontend
uses noninteractive `codex exec --json`; additional approval requests cannot be
answered in the window and fail under `approval_policy="never"`. Use the regular
interactive CLI for tasks needing those approvals. Full Access is not exposed
as a GUI toggle.

MCP mouse/keyboard permissions are independent of the shell sandbox and are
inherited from your existing setup. The UI does not claim that CLI detection
establishes login or desktop readiness: request errors are displayed in the chat.

## Voice input

Click the microphone button, speak, then click it again. Recording stops after
60 seconds at most. The ring responds to the microphone level. Local
faster-whisper transcribes on the CPU using the multilingual `base` model;
Russian and other languages are detected automatically. The first transcription
downloads and caches the model. Internet access to the Hugging Face model/CDN
hosts is needed for that download; a configured local model directory can be
supplied through `JARVIS_VOICE_MODEL` for offline use. Audio is held in memory
and is not saved or uploaded by the voice worker.

The transcript is placed in the composer and **never submitted automatically**.
Review/edit it, then press Send to submit its text to Codex. Cancel is available
during microphone startup, recording, downloading and transcription. Request
microphone permission in Windows Privacy settings or your Linux desktop when
necessary. `JARVIS_VOICE_LANGUAGE` can override language detection, for example
`ru`; `JARVIS_VOICE_MODEL` can select another model.

For text-only use, without the voice packages:

```bash
bash scripts/jarvis-gui-linux.sh --no-voice
```

```powershell
.\scripts\jarvis-gui-windows.ps1 -NoVoice
```

## Development and validation

```bash
uv sync --project gui --frozen --extra voice
python3 -m unittest discover -s tests -v
uv run --project gui --frozen python -m unittest discover -s gui/tests -v
```

Headless Linux smoke test (does not send a Codex request or access a microphone):

```bash
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
  uv run --project gui --frozen jarvis-gui --smoke-test --screenshot /tmp/jarvis.png
```

`gui/uv.lock` pins the dependencies. An isolated QML test exercises the real
composer and conversation panel against a fake CLI process, including compact
layout rendering. Process tests cover stdin prompts, resume, fragmented JSON,
failures, cancellation and transcript review. Audio/model tests use simulated
devices and transcription; they do not establish hardware-level microphone or
model accuracy. A Qt process/window CI job runs on Ubuntu and Windows runners.

Local validation has covered the Linux offscreen UI and simulated integrations.
Live Windows desktop behavior, microphone capture/transcription, authenticated
model requests and compositor-specific GUI actions require checks on the target
machine. Do not interpret simulated test results as those checks.

The app stores only workspace/reasoning/access preferences in user settings.
Conversation text stays in app memory; Codex maintains its own session history
under its existing configuration. Closing the app stops its active workers.
`JARVIS_GUI_CODEX` can point to an alternative Codex executable for development;
it is a path, not a shell command.
