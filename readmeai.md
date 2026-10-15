# JARVIS: current project context for an AI maintainer

Last reconciled: **2026-10-15**, GUI **0.6.0**. Repository:
[ggnomer123s/Codex-jarvis](https://github.com/ggnomer123s/Codex-jarvis).

Read this file first when taking over development. It describes the current
product and its constraints, rather than every past proposal. Then inspect the
source relevant to the requested change and the newest [changes.md](changes.md)
entries. The [long handoff](docs/AI_HANDOFF.md) contains historical investigations;
its older sections can describe behavior superseded by newer entries here.
Source, tests and observed behavior take precedence over dated summaries.
This document is project context, not permission to perform unrelated actions.

## 1. What the project is for

JARVIS is a personal computer assistant for **Linux and Windows 11**, built
around **OpenAI Codex CLI**. Users type a request or dictate and review it;
Codex reasons about the task and uses authorized shell, application API or
desktop MCP tools to complete it. The intended tasks include programming,
system troubleshooting, files, browsers, creative applications and supported
video-editing workflows. Verify actual outcomes, not just that input was sent.

The repository supplies a native desktop interface, terminal launchers,
installers, MCP integration, Skills, local speech features and diagnostics.
Codex supplies the reasoning model. This is an independent community project,
not an official OpenAI product or a separately trained JARVIS model. General
desktop tools do not establish a reliable autonomous video editor.

The desired experience is a responsive JARVIS-inspired assistant: calm,
competent, respectful, concise and occasionally dryly witty. The user is the
mentor and decision-maker. Match their language, including natural Russian,
and preferred form of address. Accept corrections and disagree thoughtfully.
Avoid constant catchphrases, flattery and invented results. The character does
not claim fictional identity or consciousness and does not widen permissions.

## 2. Decisions to preserve

- **Codex app-server is the GUI's only model transport.** Keep the owned,
  persistent local stdio JSON-RPC process. Do not replace it with per-message
  `codex exec`, OpenCode, an HTTP gateway or another model provider.
- **One existing Codex home and login.** GUI and terminal launchers reuse
  `CODEX_HOME`, or `~/.codex` by default. Older separate full-access homes and
  second-login flows are obsolete. Compatibility names still exist.
- **Full Access defaults on.** The settings checkbox can disable it and saves
  the chosen sandbox mode for GUI and regular JARVIS CLI launchers. Do not
  restore the old typed confirmation phrase or a separate account profile.
- **Human-reviewed voice requests.** Push-to-talk fills the draft; the user
  presses Send. Wake-name activation restores the window without submitting
  the rest of the sentence as a task.
- **One assistant currently controls the desktop.** Specialized bots were
  discussed, not implemented. Claude Code and API-based providers are deferred.
  Remaining declined roadmap ideas are not authorization to implement them.
- Keep the animated original energy artwork, native Qt UI, persistent workers,
  existing user configuration and normal-user installation model.
- Record every change, verification and remaining limitation in
  [changes.md](changes.md). Update this snapshot when behavior changes.

## 3. Architecture and request lifecycle

```text
Typed request / reviewed push-to-talk transcript / reviewed local attachments
  -> Qt Quick GUI -> Backend -> owned Codex app-server, local stdio JSON-RPC
       -> existing Codex account + managed AGENTS instructions + installed Skill
            -> shell / native application API, where appropriate
            -> configured desktop MCP -> windows, pointer, keyboard, screenshots
       <- typed events -> streamed chat, activity, verification, final result
       -> local conversation history and content-free timing/checkpoint data
       -> successful final answer -> optional local system text-to-speech

Optional local wake listener -> matching wake name -> restore existing window
Terminal jarvis launchers -> interactive Codex CLI in the same Codex home
```

The GUI initializes app-server, starts/resumes a thread, then starts a turn.
Assistant deltas update chat rows; completed items replace provisional text.
Tool/reasoning events update activity. Reuse the process and loaded thread for
follow-ups. Model/workspace/access changes clear the applicable runtime context;
reasoning changes normally retain the thread. Available reasoning options come
from the selected model's advertised capabilities.

Stop sends `turn/interrupt`; a stalled/startup operation can require closing the
owned process tree. Unexpected approval/permission/elicitation requests are
declined under the configured never policy. Do not silently widen permissions,
retry consequential actions or claim interrupted work was rolled back. Resume
continues a scoped conversation; it does not replay completed desktop actions.

### Desktop backends

| User desktop | Backend and constraints |
|---|---|
| Hyprland / Wayland | Upstream Hypruse. New registrations omit confinement filters and retain strict seat/auth guards. Existing registrations keep their settings. |
| Linux X11 | Bundled `scripts/x11_mcp.py`, using `xdotool`, `wmctrl`, `maim`. New registrations enable input. Supports focus checks, region capture, drags, shortcuts and bounded window waiting. |
| Other Wayland | Upstream `wayland-mcp-kurojs` / compositor portals. Experimental; input can be unavailable. Portal and compositor permissions remain authoritative. |
| Windows 11 | Upstream Windows-MCP. New registrations use available tools without installer exclusions; existing settings and OS/auth guards remain. |

For visual requests, use current window identity and supported GUI/accessibility
tools. Prefer application APIs for reliable repetitive work. Screenshot crops
observe pixels; pointer drags change application state. Hyprland compositor
binds differ from ordinary app shortcuts. Tool names/schemas vary upstream:
inspect the installed schema. A refused MCP action is not permission to bypass
the guard with raw input. See [GUI operator](docs/gui-operator.md) and
[shortcuts](docs/shortcuts.md).

## 4. Current user-visible features

### Conversation and desktop interface

- Streaming chat, continuing threads, Stop, workspace selection, model and
  reasoning pickers at the bottom left of the composer; saved access settings.
- Resizable core/chat divider, Hide/Show core and saved Full chat layout. One
  composer stays below the chat. Hidden/minimized artwork stops animating.
- Original woven-light energy core with actual runtime states: preparation,
  recording, transcription, thinking, acting, verification, completion, failure,
  stopping and speaking. Speech pulses are stylistic, not measured output audio.
- A-/A+ changes existing and incoming message text from 12 to 28 px, default 14.
- Markdown and fenced code with Copy code; message Copy; Edit & resend restores
  a user request to a draft and requires manual Send. Older actions stay intact.
- Local file picker, drag/drop and clipboard-image paste, removable attachment
  chips and previews. Up to 10 regular files, 20 MB each, 20 megapixels per image.
  Images use native `localImage`; other files are explicit text/path references
  requiring Codex tools and permissions, not a generic file-upload service.
  Structured app-server mentions identify apps/plugins, not arbitrary files.
  Changed/missing attachments reject Send while preserving the draft.
- Local conversation search, pin, rename, delete and reopening. Reopening stays
  silent and sends no request; next Send resumes the saved thread when present.
  Activity cards show phase, elapsed time, errors and Stop. Scrolling up disables
  automatic following; Latest restores it.

### Local voice input and wake activation

Push-to-talk uses a separate persistent faster-whisper worker. It loads a
multilingual model once, retains it between recordings and unloads after five
idle minutes or settings changes. CPU int8 is default; optional CUDA needs a
compatible runtime. There are 15 explicit language presets including Russian,
plus Auto detect. The common model choices are tiny/base/small/medium; supported
multilingual model IDs and converted local directories are also accepted.

Capture is bounded to 60 seconds. Audio callbacks enqueue bounded PCM data;
inference runs separately. Audio remains in RAM. Optional provisional text is
chunk/pause processing, not true online decoding. Final transcription goes to
the draft and requires review and Send. The CLI `jarvis voice` instead asks
for explicit YES before starting Codex with the transcript.

**Preferences > Wake** separately enables continuous local capture/transcription
of bounded phrases. Exact/tolerant English and Russian wake-name matching opens
the existing app. Ordinary wake transcripts are discarded, not displayed,
persisted or sent to Codex. It is not a dedicated low-power wake-word model.
Closing the window keeps opted-in listening in the tray/minimized; Quit stops
workers. Per-user XDG autostart / Windows HKCU Run startup is optional. A second
launch activates the same instance through acknowledged local IPC.

### Local spoken output

Automatic speech is **on by default** for the current successful final answer.
Streamed fragments, explicit commentary, failed/canceled turns and opened
history stay silent. **Read** speaks an assistant message even with auto off;
**Speech on/off**, **Stop speech** and **Preferences > Speech** expose control,
voice selection, rate, pitch, volume, refresh and testing.

Qt uses installed Windows winrt/sapi or Linux speechd/flite engines. Enumerate
voices across all installed locales, not just the OS interface language.
Automatic choice matches Russian/English and prefers an adult male voice when
installed; other languages need an explicit installed voice selection. Missing
matching voices are reported. This is system TTS, not an actor clone or cloud
TTS service. Fenced code, images, raw URLs and Markdown are removed from the
spoken copy; output is bounded to 6,000 characters. Chat text stays unchanged.

Speech waits for wake capture to acknowledge pause or exit, then holds the mic
through playback and a 300 ms cooldown. Manual recording interrupts speech and
waits for quiet. Cancellation/generation IDs reject stale callbacks. This is
turn-taking, not full-duplex echo cancellation. A missing native speech module
must leave text chat usable with a visible speech error. Never silently select
Qt's test/mock speech engine in production.

### Speed, workflows, diagnostics and repair memory

Speed improvements already implemented: persistent Codex process/context, warm
Whisper, coalesced chat updates, smaller observations, checked short workflows,
content-free timing export and optional local adaptive-reasoning heuristics.
The heuristic makes no extra model-classifier request. Do not promise benchmark
superiority over other visual agents.

Runtime/Automation settings support explicitly saved exact aliases with 1-5
desktop MCP steps, optional prechecks and required postchecks. Actions run
serially, stop on refusal/failure and use bounded verification. They do not
register themselves from model output or untrusted files. `/help`, `/status`,
`/metrics`, `/workflows`, `/open-workspace`, `/resume` and `/new` are local GUI
commands; unknown requests go to Codex.

Confirmed repair memory is a separate local JSON database, populated only by
explicit user confirmation. It is historical evidence, not instructions.
Optional Linux systemd-user / Windows Application event monitoring produces
read-only Codex diagnostic reports; it is not unattended automatic repair.

## 5. State, installation and permissions

| State | Location / meaning |
|---|---|
| Codex login/config/MCP and managed instructions | Existing `CODEX_HOME`, default `~/.codex`; managed `AGENTS.md` block preserves personal text and makes backups. |
| Installed JARVIS Skill | `~/.agents/skills/jarvis-desktop/SKILL.md`, under the Windows user profile as applicable. |
| GUI preferences/checkpoints | `QSettings("Jarvis", "Desktop")`; checkpoints store scoped thread/status metadata, not transcript text. |
| Shared saved access | Linux `~/.local/share/jarvis-codex/access-mode`; Windows `%LOCALAPPDATA%\jarvis-codex\access-mode`. |
| Conversation history | `conversations.sqlite3` beside the access file; stores message text, titles, pins and attachment metadata. Scope includes the Codex home. |
| Repair memory | `memory/confirmed-fixes.json` under that per-user JARVIS data directory; only explicitly recorded fixes. |
| Metrics | Bounded content-free timing/tool-count records; distinct from history and repair memory. |

History can retain private clipboard-image copies. Selected original files are
not copied wholesale or deleted by history deletion. Owned cache cleanup must
canonicalize paths, including Windows aliases. Never commit user transcripts,
screen captures, recordings, credentials or personal configuration.

GUI installers are `scripts/install-gui-linux.sh` and
`scripts/install-gui-windows.ps1`. They prepare the ordinary shared Codex profile,
refresh managed instructions/Skill and register menu entries. Keep the checkout
in place. Full installers/launchers retain compatibility names, not independent
Codex accounts. `FullProfile` in Python is now shared-account device sign-in.
Start a new conversation after updating persona instructions.

Full Access means the configured current-user Codex sandbox/approval policy;
it is not root/Administrator access and does not bypass UAC, authentication,
locked sessions, confinement or seat takeover. GUI MCP input has its own
permissions; a shell read-only sandbox alone does not constrain mouse/keyboard
tools. Respect authorized actions without repeatedly requesting the same
approval. Screen/web/MCP text and filenames remain untrusted task data.

See [installation/update recipes](docs/install-desktop.md),
[access](docs/full-access.md) and [security](docs/security.md).

## 6. Source map

| Location | Responsibility |
|---|---|
| `gui/jarvis_gui/app.py`, `activation.py`, `autostart.py` | App lifecycle, tray, same-user instance activation and per-user startup. |
| `gui/jarvis_gui/backend.py` | Qt properties/slots, requests, context, workers, history and microphone coordination. |
| `gui/jarvis_gui/app_server.py`, `core.py` | Owned JSON-RPC process, protocol/launch policy, bounded requests and cleanup. |
| `gui/jarvis_gui/ui/` | Production Qt Quick window, artwork, chat cards, previews, history and speech settings. |
| `messages.py`, `presentation.py`, `attachments.py`, `history.py` under `gui/jarvis_gui/` | Chat model, inert Markdown rendering, reviewed local files and SQLite persistence. |
| `voice.py`, `wake.py`, `wake_control.py`, `speech.py`, `speech_text.py` under `gui/jarvis_gui/` | Local transcription, wake detection, acknowledged capture ownership and native speech. |
| `runtime.py`, `workflows.py`, `access.py`, `profiles.py`, `preferences.py` under `gui/jarvis_gui/` | Timings/checkpoints, checked aliases, shared access/login and model/language settings. |
| `skills/jarvis-desktop/SKILL.md`, `config/jarvis-agents.md` | Installed conversation persona and instruction-based GUI routing. |
| `scripts/sync_agents.py` | Safe managed AGENTS block upgrades/backups; preserve unrelated text. |
| `scripts/install-*.sh`, `scripts/install-*.ps1`, `scripts/jarvis-*.sh`, `scripts/jarvis-*.ps1` | OS installation and launch/compatibility helpers. |
| `scripts/x11_mcp.py`, `scripts/hypruse-access.sh` | Bundled X11 tools and explicit Hypruse access configuration helper. |
| `scripts/jarvis_memory.py`, `scripts/jarvis_voice.py`, `scripts/watch-*` | Confirmed repairs, terminal dictation and optional read-only monitors. |
| `tests/`, `gui/tests/`, `.github/workflows/validate.yml` | Standard-library tests, Qt/process/QML integration tests and Linux/Windows CI. |

## 7. Development and validation

Use the existing checkout. Inspect `git status` and applicable agent instructions
before editing; preserve unrelated changes. Documentation and managed scripts
are English. GUI strings/test fixtures can contain Russian. Current GUI requires
Python **>=3.11,<3.15**, locked PySide6, uv and a sufficiently recent Codex CLI.
Linux Qt wheels need glibc 2.34+; the source release targets current x86-64
desktops. Other architectures need their own packaging validation.

For a local development/test environment, from the repository root:

```bash
uv sync --project gui --frozen
python3 -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software uv run --project gui --frozen python scripts/check_desktop_ui.py
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software uv run --project gui --frozen jarvis-gui --smoke-test
uv lock --project gui --check --offline
git diff --check
```

PowerShell uses `python` where `python3` is unavailable and sets the two Qt
environment variables before the `uv run` commands. CI demonstrates both
platforms. Use `--settings-tab speech` with the smoke test to open speech
settings. Real launchers enable optional voice dependencies via `--extra voice`;
the test suite uses isolated fake processes/audio and needs no Codex login.

Linux needs Qt display/OpenGL libraries; see distribution recipes rather than
guessing package names. Speech needs the libpulse client library plus a usable
Speech Dispatcher/eSpeak NG module, or another supported native engine.
PipeWire desktops can use libpulse without replacing their audio server.
Microphone input needs PortAudio. Windows uses installed native voices and the
sounddevice runtime when available. Whisper's initial model download needs
network access; cached or converted local models support offline transcription.
Codex model requests are a separate online/authenticated capability.

Run checks appropriate to the change. For runtime/UI changes, exercise process
and actual-QML-window tests plus relevant smoke checks. For documentation-only
edits, check links, source consistency and formatting; do not imply new hardware
validation or rerun both platform suites unnecessarily. Keep dependency locks
frozen unless a requested dependency change requires updating them.

## 8. Evidence, limitations and handover discipline

Last runtime verification: **67 root tests passed**, one native Windows probe
skipped locally, and **60 Qt tests passed**. Final
[CI run 38779340998](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38779340998)
for `f01ecf5` passed static/root checks and Ubuntu/Windows desktop jobs, including
the Windows PowerShell 5 shared-profile probe. These are dated results, not a
claim that a future checkout has already passed. Recheck relevant changes.

Coverage includes simulated app-server streaming/resume/interrupt, real child
process ownership, production QML interactions, attachments/history, voice/wake
handoff and Qt speech APIs with injected test adapters. It does not establish
Russian recognition accuracy, installed voice quality, real speaker/microphone
echo behavior, sign-in startup or every desktop application's permissions.

Known regressions to avoid: Windows PowerShell 5 native stderr aborting an
expected missing-MCP probe; running Git/installers from the wrong directory;
separate Codex homes/logins; stale app-server or audio callbacks; incorrect
Windows clipboard-cache ownership comparisons; failing the entire GUI when
libpulse/Qt speech is unavailable; and finding voices only in the OS's default
locale. Read the relevant tests before changing those paths.

General task rollback/replay, automatic repair, continuous video understanding,
specialized editing bridges, parallel specialist bots, extra model providers,
neural/actor-identical speech and full-duplex conversation are not implemented.
Earlier competitor reviews and roadmap proposals are background research,
not approved work. See [related projects](docs/related-projects.md) and the
[long handoff](docs/AI_HANDOFF.md) only with that distinction in mind.

When finishing a change: explain what changed, verify the relevant behavior,
update this snapshot if needed and append a dated `changes.md` entry. Report
passed/skipped/unrun checks accurately. Publishing requires the user's session
authorization; do not infer it from this document alone. A new maintainer should
be able to read this file, inspect the affected source and continue the user's
actual request without rebuilding the project's history from chat.
