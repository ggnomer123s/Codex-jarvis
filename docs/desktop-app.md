# JARVIS desktop application

A native Qt Quick window for Linux and Windows 11, with an animated cyan core,
a conversation panel, model/workspace selection, reasoning presets and push-to-talk
voice input. The same interface runs on both platforms; platform-specific
launchers and menu installers are provided. This is a source distribution,
not a signed standalone EXE, AppImage, DEB or RPM release.

![JARVIS desktop command center](images/jarvis-desktop.png)

For a fresh installation, use the [complete commands for your operating system](install-desktop.md).
They cover Arch/CachyOS, Debian/Ubuntu/Mint, Fedora, openSUSE and Windows 11.

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
installer if you move it. It installs current-user launchers, menu entries and
the separate Full Access profile. Unmanaged launchers/menu entries with the same
names are refused. Remove the two generated GUI launcher/menu files
to uninstall the menu entry; existing CLI JARVIS configuration is unaffected.

The GUI installer also prepares the separate Full Access profile automatically.
Codex CLI and uv/uvx must be installed. Full Access starts off and is enabled
using one checkbox in Preferences. Preparation does not start an unsandboxed
Codex session. The separate profile retains its own login state.

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

The Windows GUI installer prepares the separate Full Access profile in a child
PowerShell process before creating the shortcut. Run it from a normal,
non-elevated PowerShell. For copy-ready commands that work from any directory,
including `C:\Users\Cosmo`, see [Windows installation](install-desktop.md#windows-11).

## Use the app

1. Choose **Workspace**. This is the working directory for Codex requests.
2. Type a request and press **Send** or Enter. Shift+Enter inserts a new line.
3. Replies appear in the conversation panel. Command/MCP activity appears below
   the animated core. Follow-up requests resume the current Codex thread.
4. **Stop** or Escape cancels the active task. Completed actions are not undone.
5. **New conversation** or Ctrl+N starts a fresh context. Changing the workspace
   or access mode also resets the context.

Preferences has **Intelligence**, **Voice** and **Access** tabs. Intelligence
offers a model picker from the active profile's local `models_cache.json`, an
editable model ID, and a Refresh button. No credentials are read from that file.
The cache can be empty or stale: run Codex once and refresh, or enter an ID from
your provider. Availability is validated by the actual request, not by the cache.
An empty selection / **Codex default** inherits the configured model. Changing
the model starts a fresh conversation. The selected ID is passed as a separate
`--model` argument to both new and resumed requests.

Preferences offer Fast (`low`), Normal (existing Codex default) and Deep (`high`)
reasoning. Choose Normal if your configured model does not support low reasoning.
Workspace access defaults to **Observe only** (`read-only`). **Allow workspace
edits** explicitly selects `workspace-write` for the chosen folder. This frontend
uses noninteractive `codex exec --json`; additional approval requests cannot be
answered in the window and fail under `approval_policy="never"`. Use the regular
interactive CLI for tasks needing those approvals.

## Full Access from the GUI

1. Install/update through the GUI installer, which prepares the included profile.
2. Open **Preferences > Access** and check **Enable Full Access**. No typed
   acknowledgement or extra confirmation button is required.
3. Use **Sign in to full profile** if this profile has no authentication. The
   device sign-in URL and code appear in the panel; **Open sign-in page** opens
   the official device page in your browser. Credentials are never copied from
   the normal profile.
4. An amber Full Access indicator remains visible. Uncheck the box to return to
   the retained normal workspace access mode. Save preferences applies any
   model, reasoning or voice edits made in the other tabs.

Full Access runs `codex exec --dangerously-bypass-approvals-and-sandbox` as the
current user, with the same separate `CODEX_HOME` used by `jarvis-full`. It can
change user-accessible files and run commands without Codex's sandbox or command
approvals. It does not grant root/Administrator access, bypass OS authentication
or override upstream MCP guards. Elevated execution is refused.

Unchecking **Enable Full Access** restores the retained normal access setting. Switching
profiles clears the current conversation so thread IDs cannot cross profiles.
Full Access is enabled only for the current window and returns to normal mode
after restart. Profile preparation and login are cancellable. Cancelling setup
does not remove files already installed. Automatic preparation requires the
source checkout. On older installations without a prepared profile, checking
the box prepares it automatically before activation; missing prerequisites are
reported in the profile log. Packaged-wheel users can prepare the profile using the
[existing Full Access installers](full-access.md).

![Full Access checkbox](images/jarvis-access-settings.png)

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
necessary. Before the first launch, `JARVIS_VOICE_LANGUAGE` (for example `ru`)
and `JARVIS_VOICE_MODEL` seed these preferences. Later changes can be made in
the Voice tab and are retained in user settings.

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

The app stores workspace, model, reasoning, normal access and voice preferences in user settings.
Conversation text stays in app memory; Codex maintains its own session history
under its existing configuration. Closing the app stops its active workers.
`JARVIS_GUI_CODEX` can point to an alternative Codex executable for development;
it is a path, not a shell command.

## Local speech languages and models

In **Preferences > Voice**, choose Auto detect or one of 15 explicit languages:
Russian, English, Ukrainian, German, French, Spanish, Italian, Portuguese,
Polish, Turkish, Arabic, Chinese, Japanese, Korean and Hindi. Russian uses the
Whisper `ru` language code; this preserves the original speech language rather
than translating it into English. Auto detect also supports other languages
covered by multilingual Whisper. Accuracy varies by language, audio and model.

The model picker offers `tiny`, `base`, `small`, and `medium`. Larger models use
more memory and computation. Other official multilingual Whisper sizes or a
local converted model folder can be entered manually. English-only `.en` model
names are not accepted. The saved selection is supplied to the voice worker
as `--language` and `--model`; existing `JARVIS_VOICE_*` variables seed the initial
preferences. Recordings remain capped at 60 seconds and are never submitted
automatically.

![Local voice preferences](images/jarvis-voice-settings.png)

The settings window now uses dark controls and tabs. The main screen shows the
selected Codex model, reasoning, voice language/model and active access level.
The core animation is limited to about 30 frames per second and pauses when
minimized. No model or transcription latency benchmark is claimed.

## Next performance improvements to investigate

- Keep a voice worker/model warm after first use, while leaving microphone
  capture off between recordings; measure latency against the memory cost.
- Use a persistent Codex app-server connection to avoid CLI/MCP initialization
  on each message and support richer progress and interactive approvals.
- Measure microphone, model startup, Codex and tool latency separately before
  adding automatic Fast/Deep routing.
- Add a Doctor screen for login, model, microphone, MCP and desktop readiness,
  plus resumable checkpoints for long editing workflows.

These are proposed follow-ups, not implemented features.
