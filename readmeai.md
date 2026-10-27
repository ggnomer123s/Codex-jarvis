# Tigo: current project context for an AI maintainer

Last reconciled: **2026-10-27**, GUI **0.15.0**. Repository:
[Tigo source repository](https://github.com/ggnomer123s/Codex-jarvis).

Read [USER_HANDOFF.md](USER_HANDOFF.md) first for standing user preferences,
latest corrections, Git workflow and canceled drafts, then this file. It describes
the current product and its constraints, rather than every past proposal. Inspect
source relevant to the requested change and the newest [changes.md](changes.md)
entries. The [long handoff](docs/AI_HANDOFF.md) contains historical investigations;
its older sections can describe behavior superseded by newer entries here.
Source, tests and observed behavior take precedence over dated summaries.
This document is project context, not permission to perform unrelated actions.

## 0. Resume card: read before continuing

GUI 0.15.0 adds live subscription usage above the composer and screenshot-error
recovery. `account.py` performs native `account/read` with `refreshToken: true`
before releasing server waiters to thread/task startup. It reads
`account/rateLimits/read`, handles global account notifications before thread
filtering, polls every 60 seconds while shown and updates reset countdowns every
15 seconds. Match 300/10080-minute windows by duration, preserve model buckets,
show unavailable/stale data honestly and never infer access from reset times.
QSettings `showUsageLimits` defaults on; X hides/stops polling, Limits or Runtime
restores it. Quota data stays in memory. A 401 produces one actionable error and
a sign-in banner, blocks repeated failed submissions, and never replays a task.
Native successful login restarts the owned server with the same home and retained
chat/thread. Workspace access still requires actual server authorization.
Online dictation can reuse the same PCM through lazy CPU Whisper on final
recognition failure; `voiceLocalFallback` defaults on, is switchable in Voice,
and recovered text always stays for review even with auto-send enabled. Preview
and wake providers are unchanged. Existing Whisper model download/cache rules
apply; no dependencies changed. See docs/account-and-limits.md. The user asked
to finish quickly; no tests/GUI/CI runs were started. Static checks only.

GUI 0.14.5 addresses the follow-up asking specifically for 6.1 Terra. Add the
explicit `gpt-6.1-terra` ID as a requested shortcut separately from live catalog
data; this is NOT a verified account entitlement or confirmation that every
Codex endpoint supports the same model as another Codex client. The target PC's
catalog has not been inspected. Never fabricate advertised capabilities or claim
an authenticated Terra request succeeded. Both pickers also retain up to 64
validated selected IDs in QSettings `customModels`, so switching models, live
refresh and restart cannot erase private/provider IDs. Read `config/read` with
the workspace to extract only its configured model ID; discard other response
fields and reject stale connection/workspace callbacks. Selection status/tooltips
distinguish last-catalog, configured and unconfirmed IDs. Never substitute another
model on an unavailable-ID error. A newly selected model with no advertised
reasoning metadata starts at Model default, without guessing its capabilities.
Codex app-server remains the only transport; no new dependency, account/profile,
provider or installer action is added. User explicitly authorized pushing this
fix. Test suites and CI remain unrun; only static checks are recorded.

GUI 0.14.4 fixes stale/missing model choices. Opening either picker or Preferences
uses `ensureModels()` to fetch a complete live `model/list` catalog with
`includeHidden: true`, following bounded nonrepeating cursors. Keep the local
cache only as initial fallback, include hidden cached entries, and never replace
a completed live list with stale cache data during preference saves. Catalog
callbacks use a connection generation, not a conversation/task epoch; publish
names/reasoning metadata atomically and retain the last good list on page errors.
Repeated picker checks coalesce for 60 seconds. Explicit Refresh restarts only
the idle owned app-server, preserves chat/model/thread ID and marks the thread
for resume on the next task; never send a prompt or alter login/access to list
models. Preserve editable draft/selection across QML catalog replacements.
The visible status reports loading/errors. The live catalog is not restricted
to a hardcoded allowlist; 0.14.5 adds a separate explicitly requested shortcut.
New models can still require a Codex CLI update and account/provider rollout.
User asked to fix and push this change directly. No test suites/GUI runs or CI
were started for this patch; publication uses `[skip ci]`. Static source/schema
inspection and syntax/whitespace checks are reported separately in changes.md.
No dependencies changed. Earlier dated results below do not verify this patch.

GUI 0.14.3 makes the Wayland activity frame use the full output (exclusive
zone -1), not the panel-reserved work area. Edges and banner text have explicit
click-through input regions; only Return control captures mouse input, refreshed
after GTK allocation/remapping. Linux setup now includes Pycairo/GI Cairo; see
[screen control](docs/screen-control.md). Hypruse guards/input transport remain
unchanged; frame geometry/protocol checks are not a game-latency benchmark.

GUI 0.14.2 queues each completed assistant Copy/Read message card as one speech
job, including progress/commentary, before the overall turn ends. Deltas update
chat only; completion and history never replay speech. See [Live voice](docs/live-voice.md)
for settings, privacy and bounds. Live dictation from 0.14.0 is preserved; online
recognition uses repeated phrase requests rather than a persistent streaming API.
The earlier canceled setup/wake drafts in the working tree remain separate.

**Tool discovery correction (2026-10-17):** The Tigo Skill and managed AGENTS
block now distinguish browser integration, desktop MCP and shell PATH. Inspect
current/deferred tools and an advertised read-only desktop inventory before
claiming no browser/computer access. An absent browser connection or CLI is not
proof that the desktop MCP is absent. This fallback never bypasses auth/scope/
ownership refusals. Normal installers already deploy these instruction files;
new sessions are required to load them. No runtime/dependency change is needed.

The context-rollover handover was published as `e970515`. The subsequent user
request adds full CachyOS/Windows update commands that check/install dependencies;
see section 13 and the newest change report for those bootstrap scripts. Runtime
implementation **0.6.1** was published as `d63f53d`; its verification report is
`b804dd0`. These are navigation baselines, not a claim about a future Git HEAD.

**Current state:** GUI 0.13.1 fixes quiet/short wake phrases dropped by the old
fixed RMS gate. Wake uses existing local WebRTC VAD (20 ms frames, 160 ms speech,
660 ms pause, four-second cap, 240 ms pre-roll/overlap) and bounded speech gain
before either provider. Mixed-script name tokens and finite tolerant Tido/Tiga
variants are recognized; do not widen to arbitrary edit-distance matching.
Preferences > Wake has content-free level/speech/phrase/result diagnostics on a
separate signal; ordinary transcripts/audio remain transient. Both voice
preflight checks require the existing locked webrtcvad import. No new dependency
or installer change is required. Quit/relaunch after an update to replace the
old worker. Synthetic checks are not evidence of live microphone accuracy.

GUI 0.13.0 adds independent local/keyless-online wake
transcription, explicitly hidden listener startup and opt-in wake-to-dictation /
voice-send-after-pause. WebRTC VAD works locally for both dictation providers;
only a detected speech-ending pause can auto-submit, and existing/edited drafts,
attachments, cancellation or incomplete worker exit keep review behavior.
Listening/auto-record/auto-send are separately saved and off by default.
Startup --background no longer minimizes/shows the main window without a tray
or on listener errors. Normal launch restores it via existing IPC. See
[voice activation](docs/voice-activation.md). Provider expansion to Claude Code,
Antigravity and direct APIs was explicitly deferred by the user and recorded in
[roadmap](docs/roadmap.md); do not implement it without a fresh request.

GUI 0.12.0 adds explicit local/keyless online dictation and
semantic-first interface targeting. Online dictation uses SpeechRecognition's
public personal-use Google Web Speech configuration, forced HTTPS, bounded
in-memory audio and no personal API key. It is not a guaranteed Cloud API.
Select a language; no online Auto detection or preview. Local Whisper defaults
to small only for new GUI settings; saved model choices stay intact. The CLI remains local; newer GUI wake/automation settings are described above. See [voice input](docs/voice-input.md).
X11 adds scoped AT-SPI ui_elements/click_ui via a system-Python helper with
PID/title/focus/state/ambiguity checks. Hypruse/Windows use existing native
trees; shipped instructions prefer them for labeled controls. Runtime reports
only actually advertised semantic tools, not ownership or app support. New GI/
AT-SPI distro prerequisites and SpeechRecognition are included in setup/lock/
platform import checks. See [semantic targeting](docs/gui-operator.md#semantic-interface-targeting).

GUI 0.11.0 adds an on-demand Update Center (sidebar Updates /
Ctrl+U), version/commit/notes review and a detached terminal installer handshake.
Checks fetch Git objects without changing working files; application shutdown
requires a ready installer, reviewed commit and an idle UI with no draft/files.
Root install.sh/install.ps1/install.cmd are the common setup entry points, with
new supported-family Linux dispatch and an optional verified private Node 22
runtime. Keep these entry points/platform scripts current whenever installation
requirements change; this persistent rule is in AGENTS.md. New UI transitions,
activity dots, dismissible notices and a saved Reduce interface motion setting
retain the efficient cached core. See [updates and setup](docs/updates.md).
GUI 0.10.0 adds a screen activity border/banner and human
task-stop button/shortcut for recognized desktop MCP events and workflows.
This is an activity indicator, not an OS ownership grant or input lock. Preserve
native MCP takeover guards. Hyprland uses a GTK4 layer-shell helper with system
Python bindings; Windows/X11 use Qt. See [screen control](docs/screen-control.md)
for shortcuts, dependencies and verification limits. GUI 0.9.0 adds male/female local and explicit online speech;
see [speech-output.md](docs/speech-output.md). Local remains the default; online
Microsoft speech sends spoken text only when selected. Separate provider voice
choices, bounded workers and microphone handoff are retained. GUI 0.8.0 renamed
the assistant to **Tigo** throughout the application,
CLI, source package (`tigo_gui`), Skill, installers, icons and documentation.
Wake-name matching uses **Tigo** / its Russian spelling, with a small explicit
set of transcription variants and split words. The old wake name is no longer
accepted. Local neural speech from 0.7.0 is retained. See [the rename guide](docs/rename.md)
for upgrade compatibility: old private history/attachments/repair memory and
verified voice caches remain in place, existing access choices and MCP grants
are retained, and Qt preferences migrate once without replacing Tigo settings.
The source repository URL remains unchanged until its owner renames it on GitHub.
The previous stop-testing request concerned the 0.7.0 speech publication; this
new speech request includes relevant regression, synthesis and GUI checks. Fresh results
belong in the newest `changes.md` entry; older CI reports remain historical.

**Core animation patch:** the core now uses frame-synchronized updates and
elapsed-time motion/audio smoothing. The masked artwork and static dial are
cached separately from the moving overlay. Keep rotation continuous across full
turns and pause hidden/minimized/stopped animation; do not restore per-frame
image masking or the old 20/30 Hz timer. See [the core guide](docs/desktop-app.md#animated-activity-core)
and the newest change report for the measured rendering scope and limitations.

**Previous unresolved live-machine issue:** the user reports that Tigo on Windows said the
screen service was temporarily unavailable because control belonged to the
user. They requested permanent control and a default-on checkbox. The existing
Full Access checkbox already defaults on. Version 0.6.1 adds read-only ownership
diagnostics and better installed instructions; it does **not** disable human
takeover or prove the user's machine has been repaired. The raw tool/error was
unavailable when requested. See [the incident handover](#10-latest-windows-incident-what-is-known-and-what-is-not)
before troubleshooting this again.

Quick navigation:

- [Purpose](#1-what-the-project-is-for), [decisions](#2-decisions-to-preserve),
  [architecture](#3-architecture-and-request-lifecycle), [features](#4-current-user-visible-features).
- [Local state](#5-state-installation-and-permissions), [source map](#6-source-map),
  [development](#7-development-and-validation), [verification limits](#8-evidence-limitations-and-handover-discipline).
- [User preferences](#9-collaboration-and-product-preferences),
  [Windows incident](#10-latest-windows-incident-what-is-known-and-what-is-not),
  [implementation history](#11-key-implementation-and-verification-history).
- [Implementation contracts](#12-implementation-contracts-that-are-easy-to-break),
  [update commands](#13-installation-and-update-handover),
  [cloud workflow](#14-development-environment-and-ci-investigation),
  [research and docs](#15-research-background-and-documentation-map),
  [continuation checklist](#16-first-actions-after-context-rollover).

## 1. What the project is for

Tigo is a personal computer assistant for **Linux and Windows 11**, built
around **OpenAI Codex CLI**. Users type a request or dictate and review it;
Codex reasons about the task and uses authorized shell, application API or
desktop MCP tools to complete it. The intended tasks include programming,
system troubleshooting, files, browsers, creative applications and supported
video-editing workflows. Verify actual outcomes, not just that input was sent.

The repository supplies a native desktop interface, terminal launchers,
installers, MCP integration, Skills, local speech features and diagnostics.
Codex supplies the reasoning model. This is an independent community project,
not an official OpenAI product or a separately trained Tigo model. General
desktop tools do not establish a reliable autonomous video editor.

The desired experience is a responsive Tigo-inspired assistant: calm,
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
  the chosen sandbox mode for GUI and regular Tigo CLI launchers. Do not
  restore the old typed confirmation phrase or a separate account profile.
- **Explicit voice automation.** Default dictation fills the draft for Send.
  Separate saved opt-ins allow wake-triggered recording and local-VAD speech-end
  automatic sending. Keep draft/attachment/cancellation safeguards; wake listening
  alone never submits ordinary wake transcripts or the rest of the wake phrase.
- **One assistant currently controls the desktop.** Specialized bots were
  discussed, not implemented. Claude Code and API-based providers are deferred.
  Remaining declined roadmap ideas are not authorization to implement them.
- Keep the animated original energy artwork, native Qt UI, persistent workers,
  existing user configuration and normal-user installation model.
- Record every change, verification and remaining limitation in
  [changes.md](changes.md). Update this snapshot when behavior changes.
- When installation dependencies change, update the relevant installation
  instructions, manifests, lockfiles and installer/update scripts together.
  Follow the persistent [repository maintenance rules](AGENTS.md).

## 3. Architecture and request lifecycle

```text
Typed request / reviewed push-to-talk transcript / reviewed local attachments
  -> Qt Quick GUI -> Backend -> owned Codex app-server, local stdio JSON-RPC
       -> existing Codex account + managed AGENTS instructions + installed Skill
            -> shell / native application API, where appropriate
            -> configured desktop MCP -> windows, pointer, keyboard, screenshots
       <- typed events -> streamed chat, activity, verification, final result
       -> local conversation history and content-free timing/checkpoint data
       -> successful final answer -> optional local / explicit online text-to-speech

Optional local/explicit-online wake listener -> matching wake name -> restore window
  -> optional dictation -> optional speech-end submission with draft guards
Terminal tigo launchers -> interactive Codex CLI in the same Codex home
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

On Windows, a user-ownership hold is separate from the Codex sandbox.
Preferences > Access > Check desktop control, or `/desktop-status`, reads the
installed `windows-mcp` ControlStatus through the existing app-server. It reports
state and idle wait, without a model turn, input action, configuration change or
forced takeover. Full Access remains on by default; the user can still take over.
Physical input restarts the service's idle timer (normally 10 seconds). The
installed Skill now explains checking status and resuming only after ownership
is released; missing tools/refusals do not trigger another input backend.

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

### Voice input and optional wake activation

Push-to-talk uses a separate persistent worker. Local mode uses faster-whisper;
explicit online mode uses keyless Google Web Speech over HTTPS, with a selected
language and no preview. It loads no local model and may be rate-limited.
Audio is sent to Google only in that mode. Local mode defaults to small for new
GUI settings, preserving saved choices. The following model/preview details
apply to local mode. It loads a
multilingual model once, retains it between recordings and unloads after five
idle minutes or settings changes. CPU int8 is default; optional CUDA needs a
compatible runtime. There are 15 explicit language presets including Russian,
plus Auto detect. The common model choices are tiny/base/small/medium; supported
multilingual model IDs and converted local directories are also accepted.

Capture is bounded to 60 seconds. Audio callbacks enqueue bounded PCM data;
inference runs separately. Audio remains in RAM. Optional provisional text is
chunk/pause processing, not true online decoding. Final transcription goes to
the draft by default; explicit auto-send can submit after VAD silence with draft/attachment guards. The CLI `tigo voice` instead asks
for explicit YES before starting Codex with the transcript.

**Preferences > Wake** separately enables opt-in local or explicit-online capture/transcription
of bounded phrases. Exact/tolerant English and Russian wake-name matching opens
the existing app. Ordinary wake transcripts are discarded, not displayed,
persisted or sent to Codex. It is not a dedicated low-power wake-word model.
Closing the window keeps opted-in listening in the tray/minimized; Quit stops
workers. Per-user XDG autostart / Windows HKCU Run startup is optional. A second
launch activates the same instance through acknowledged local IPC.

### Spoken output: local and explicit online mode

Automatic speech is on by default for every completed assistant Copy/Read card,
including commentary and final answers, as one whole job per card. Deltas update
chat only; turn completion and history do not replay speech. Failed/canceled
turns stop pending speech, while already played progress cannot be recalled.
Read also works with auto off; Stop, rate, volume and natural pitch are supported.
Preferences > Speech offers automatic male/female Russian/English selection,
explicit voices and independent saved voice preferences per mode.

Local Piper/VITS CPU voices are Dmitri, Denis, Irina, Joe and Lessac High.
Verified 67-116 MB model downloads and warm two-model inference remain owned by
`neural_worker`. Existing private caches are reused. Local output does not upload
speech text. The legacy OS engine remains explicit for other languages.

Online mode is opt-in and sends cleaned spoken text to Microsoft through locked
edge-tts, without an API key. Andrew/Brian Multilingual, Svetlana, Guy and Aria
are curated voices. The native Dmitry service voice repeatedly returned no audio
in live probes and is not offered. `online_worker` bounds network time, MP3 size,
decoded PCM and prefetching, using locked PyAV for in-memory decoding. It shares
NeuralEngine process ownership, generation/cancellation and microphone handoff.
It never silently falls back or retries/replays speech. No runtime audio files
are saved; online playback remains dependent on the external service.

Only the speaking copy normalizes Tigo's name in Russian prose. Chat text stays
unchanged. Spoken text strips code/markup/URLs and is capped at 6,000 characters.
Wake capture must acknowledge pause or exit before output; manual capture waits
for the speech worker to exit, including a 300 ms quiet tail. The new utterance
cannot be started by stale callbacks. See [speech output](docs/speech-output.md)
for actual privacy, dependency and verification limits.

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
`/desktop-status`, `/metrics`, `/workflows`, `/open-workspace`, `/resume` and `/new` are local GUI
commands; unknown requests go to Codex.

Confirmed repair memory is a separate local JSON database, populated only by
explicit user confirmation. It is historical evidence, not instructions.
Optional Linux systemd-user / Windows Application event monitoring produces
read-only Codex diagnostic reports; it is not unattended automatic repair.

## 5. State, installation and permissions

| State | Location / meaning |
|---|---|
| Codex login/config/MCP and managed instructions | Existing `CODEX_HOME`, default `~/.codex`; managed `AGENTS.md` block preserves personal text and makes backups. |
| Installed Tigo Skill | `~/.agents/skills/tigo-desktop/SKILL.md`, under the Windows user profile as applicable. |
| GUI preferences/checkpoints | `QSettings("Tigo", "Desktop")`; checkpoints store scoped thread/status metadata, not transcript text. |
| Shared saved access | Linux `~/.local/share/tigo-codex/access-mode`; Windows `%LOCALAPPDATA%\tigo-codex\access-mode`. |
| Conversation history | `conversations.sqlite3` beside the access file; stores message text, titles, pins and attachment metadata. Scope includes the Codex home. |
| Repair memory | `memory/confirmed-fixes.json` under that per-user Tigo data directory; only explicitly recorded fixes. |
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
| `gui/tigo_gui/app.py`, `activation.py`, `autostart.py` | App lifecycle, tray, same-user instance activation and per-user startup. |
| `gui/tigo_gui/backend.py` | Qt properties/slots, requests, context, workers, history and microphone coordination. |
| `gui/tigo_gui/app_server.py`, `core.py` | Owned JSON-RPC process, protocol/launch policy, bounded requests and cleanup. |
| `gui/tigo_gui/ui/` | Production Qt Quick window, artwork, chat cards, previews, history and speech settings. |
| `messages.py`, `presentation.py`, `attachments.py`, `history.py` under `gui/tigo_gui/` | Chat model, inert Markdown rendering, reviewed local files and SQLite persistence. |
| `voice.py`, `wake.py`, `wake_control.py`, `speech.py`, `speech_text.py`, `neural_speech.py`, `neural_worker.py`, `speech_models.py`, `online_worker.py`, `online_voices.py` under `gui/tigo_gui/` | Local transcription, acknowledged wake/mic ownership, speech lifecycle, warm neural worker and verified model assets. |
| `runtime.py`, `workflows.py`, `access.py`, `profiles.py`, `preferences.py`, `desktop_control.py` under `gui/tigo_gui/` | Timings/checkpoints, checked aliases, shared access/login, model/language settings and read-only ownership diagnostics. |
| `skills/tigo-desktop/SKILL.md`, `config/tigo-agents.md` | Installed conversation persona and instruction-based GUI routing. |
| `scripts/sync_agents.py` | Safe managed AGENTS block upgrades/backups; preserve unrelated text. |
| `scripts/install-*.sh`, `scripts/install-*.ps1`, `scripts/tigo-*.sh`, `scripts/tigo-*.ps1` | OS installation and launch/compatibility helpers. |
| `scripts/x11_mcp.py`, `scripts/hypruse-access.sh` | Bundled X11 tools and explicit Hypruse access configuration helper. |
| `scripts/tigo_memory.py`, `scripts/tigo_voice.py`, `scripts/watch-*` | Confirmed repairs, terminal dictation and optional read-only monitors. |
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
uv sync --project gui --frozen --extra speech
python3 -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software uv run --project gui --frozen --extra speech python scripts/check_desktop_ui.py
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software uv run --project gui --frozen --extra speech tigo-gui --smoke-test
uv lock --project gui --check --offline
git diff --check
```

PowerShell uses `python` where `python3` is unavailable and sets the two Qt
environment variables before the `uv run` commands. CI demonstrates both
platforms. Use `--settings-tab speech` with the smoke test to open speech
settings. Real launchers enable optional voice dependencies via `--extra voice`;
the test suite uses isolated fake processes/audio and needs no Codex login.

Linux needs Qt display/OpenGL libraries; see distribution recipes rather than
guessing package names. Neural output uses the locked speech/voice extra and
PortAudio; system mode alone needs Speech Dispatcher/eSpeak NG or Windows voices.
The native Qt module is optional. Model downloads require GitHub release access.
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

GUI 0.6.1 local verification: **71 root tests passed**, one native Windows probe
skipped, and **65 Qt tests passed**. Ownership diagnostics use simulated
Windows-MCP status, not the user's live desktop.
[CI run 38866945827](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38866945827)
for `d63f53d` passed static/root and Ubuntu/Windows desktop jobs, including the
Windows shared-profile probe.

Preceding GUI 0.6.0 runtime verification: **67 root tests passed**, one native Windows probe
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
actor-identical speech and full-duplex conversation are not implemented.
Earlier competitor reviews and roadmap proposals are background research,
not approved work. See [related projects](docs/related-projects.md) and the
[long handoff](docs/AI_HANDOFF.md) only with that distinction in mind.

When finishing a change: explain what changed, verify the relevant behavior,
update this snapshot if needed and append a dated `changes.md` entry. Report
passed/skipped/unrun checks accurately. Publishing requires the user's session
authorization; do not infer it from this document alone. A new maintainer should
be able to read this file, inspect the affected source and continue the user's
actual request without rebuilding the project's history from chat.

## 9. Collaboration and product preferences

The user communicates in Russian; answer naturally in Russian. Repository
documentation and managed scripts are English, matching the existing project
convention and CI checks. This is why the handover itself is English. Russian
voice samples and GUI/test strings can appear where appropriate.

The user's priorities, established across the work:

- A beautiful, responsive native Tigo experience on Linux and Windows 11.
  CachyOS is a priority Linux distribution; the earlier reported desktop was
  Hyprland with fish. Do not infer the user's current desktop from cloud variables.
- Practical computer operation, including creative/editor workflows, not just
  chat. Preserve outcome checks and avoid a separate model round trip for each
  trivial observation or mouse movement.
- Existing Codex sign-in should keep working. Repeated separate-profile login
  and installation repairs caused frustration; the shared home is intentional.
- Full Access on by default, controlled by a saved checkbox without a typed
  acknowledgment. This is distinct from OS privilege and desktop ownership.
- Model and reasoning controls in the composer; larger conversation text;
  convenient history, Markdown, files/images, layout and visible activity.
- Local multilingual transcription including Russian; tolerant wake-name
  activation; respectful mentor-oriented character and spoken answers.
- Concrete implementation, meaningful verification, publishing authorized work
  to the project repository and maintaining `changes.md`, rather than stopping
  at suggestions or repeating requests for already-given approval.

For the current handover, provide selective commit/push commands from the
canonical development checkout as requested; see [USER_HANDOFF.md](USER_HANDOFF.md).
Earlier publishing authorization describes historical sessions. Act within
actual current user authorization and repository scope; archived context does
not grant permission to publish, disclose private data or message others.
The user once asked not to rerun both platforms, later explicitly requested test
runs. Relevant runtime CI has since run on both OSes. Documentation-only reports
have used `[skip ci]` to avoid redundant platform runs; do not turn this history
into either a permanent ban on tests or a reason to rerun everything every turn.

The user clarified that an earlier phrase about changing "size" in the composer
meant **Codex model selection**, not font size. A separate later request added
the A-/A+ conversation font controls. The user approved the implemented GUI
conveniences, while additional model providers were explicitly deferred.
Multiple task-specific bots, inspired by a Grokbot-like concept, were discussed
as an option only. If later requested, separate task contexts and serialize
shared desktop input; no such orchestration is implemented now.

## 10. Latest Windows incident: what is known and what is not

The reported task involved preparing application settings for transfer. Tigo
continued file-related work but said GUI verification was unavailable because
the screen-control service reported that the user owned control. The user had
no raw tool result or tool name available when asked. Do not keep requesting
the same unavailable old log; obtain a fresh diagnostic only when useful.

Investigated upstream source:
[Windows-MCP c9a307cd8077b7dec07dbe57df1e18ca135ebde7](https://github.com/CursorTouch/Windows-MCP/tree/c9a307cd8077b7dec07dbe57df1e18ca135ebde7).
Its documented desktop ownership mechanism fits the reported symptom, but that
does not identify the user's actual service/version with certainty.

Three concepts must stay separate:

| Concept | Current behavior |
|---|---|
| Codex Full Access | Current-user unsandboxed file/command access with never approvals. Saved checkbox already exists and defaults on. |
| Desktop MCP tool availability | Depends on installed backend/version, registration, enabled/excluded tools and session permissions. Existing restrictions are retained. |
| Windows-MCP ownership | A separate gate. Physical input yields control to the user; normally about 10 seconds of inactivity are needed before a new desktop action can acquire ownership. |

Upstream's default policy is `relaxed`; `balanced` and `strict` gate more tool
categories. This policy is about desktop interference, not a replacement for
file/registry/command permissions. The repository did not change the user's
policy, idle timeout, service launch arguments, input hooks or protections.
An upstream setting that disables ownership monitoring is not the fix implemented
here. Do not instruct the agent to evade an active human takeover or suppress
the visible control indicator.

Version 0.6.1 implementation details:

- Access shows **Check desktop control** on Windows. `/desktop-status` is a local
  command for the same check. `windowsDesktop` controls native UI visibility;
  the QML test explicitly renders that Windows layout on both CI platforms.
- The check uses the existing owned app-server and can start/load a thread
  without a model turn. It queries `mcpServerStatus/list`, verifies the exact
  `windows-mcp` server and `ControlStatus` tool, then calls only that tool with
  empty arguments. Inventory paging is bounded to five pages.
- Inventory/status RPCs have 15-second bounds. Existing task guards invalidate
  stale results. Stop cancels the owned pending diagnostic connection; it does
  not restart a service to clear a human takeover.
- `desktop_control.py` accepts structured status or one bounded JSON text block,
  validates known states and finite nonnegative wait values, and returns a plain
  explanation. Unknown states, missing tools and refusals do not claim success.
- Reported states include `ready`, `ai`, `user`, `takeover_pending`, `unavailable`
  and `disabled`. A ready snapshot is not a promise that the next action will
  pass every backend/OS check. The check neither grants a lease nor keeps polling.
- Clicking Check or pressing Enter is physical input and can restart the timer.
  Seeing a user hold immediately after clicking is expected. After sending a
  task, leave mouse/keyboard idle; the agent can then use read-only ControlStatus
  to check without generating physical input.
- Updated Skill/managed AGENTS guidance distinguishes ownership from sandbox
  access, reports observed wait, respects an idle interval, checks before one
  fresh observation and pauses if still blocked. No automatic repetition of an
  uncertain mutating action is allowed. Unrelated authorized file work can
  continue while GUI verification remains pending.
- Diagnostic success/failure does not reset the previous reasoning heuristic's
  task outcome. No model prompt, synthesized input, configuration write, automatic
  fallback backend or permanent-control checkbox was added.

**Still unknown:** the user's installed Windows-MCP version, current registration,
actual ownership state, availability of ControlStatus, and whether the update was
installed and tested on that PC. If troubleshooting resumes, use a fresh
`/desktop-status` result and check relevant version/tool configuration. If the
backend differs, follow that backend's supported diagnostics. Do not claim that
the cloud exercised the user's Windows desktop or enabled access on it remotely.

## 11. Key implementation and verification history

These are navigation pointers into Git history, not instructions to revert to an
old version. Verify current HEAD before relying on any entry.

| Change | Source / verification |
|---|---|
| Original energy artwork and procedural runtime animation | `7cd7a76`; core still plus Qt Canvas states, replacing the central letter. |
| Local opt-in wake listener and background startup | `9cbc1d4`; real cross-process activation acknowledgment fixed in `2496dfe`; final [CI 38704976904](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38704976904). |
| Shared Codex home, saved default Full Access, composer model/reasoning controls | `0510971`; [CI 38740007768](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38740007768). |
| Conversation font controls | `03ef8fe`; [CI 38742059923](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38742059923). |
| Layout, Markdown, reviewed attachments and durable local history | `84f81f5`; Windows clipboard-cache ownership fix `eb34751`; final [CI 38747237298](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38747237298). |
| Mentor character and local system TTS | `208df7c`; optional native-library import/Ubuntu libpulse fix `f01ecf5`; final [CI 38779340998](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38779340998). |
| First consolidated AI overview | `fcb9448`, documentation only. |
| Windows ownership diagnostics and guidance | `d63f53d`; final [CI 38866945827](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38866945827); report `b804dd0`. |

The latest runtime CI passed static/root, Ubuntu desktop and Windows desktop,
including the native PowerShell 5 shared-profile probe. Local counts were 72 root
tests discovered, 71 passed and one Windows-only skip, plus 65 Qt tests passed.
This handover expansion does not create a newer runtime/hardware validation.

## 12. Implementation contracts that are easy to break

### Runtime, requests and cancellation

`Backend._begin`, `_ensure_server`, `_ensure_thread`, `_guard`, `_notification`
and `_finish` coordinate tasks. App-server transport is separate from these
thread/turn rules. Preserve epoch/task/turn checks and retired-turn filtering:
a late completed turn must not write into or finish the next task.
Use `initialize`/`initialized`, `thread/start` or `thread/resume`, `turn/start`
and `turn/interrupt`; do not infer protocol shape from another agent's SDK.

App-server uses newline UTF-8 JSON records bounded to 8 MiB and at most 64 pending
RPCs. Default RPC timeout is 30 seconds; thread operations and specific checks
can use different bounds. The GUI batches chat updates at about 33 ms. A timeout
can leave an action's outcome unknown, so it is not permission to retry blindly.
Only owned child processes are terminated: Unix process groups, or the owned
Windows PID tree. Do not kill every Codex/Python process on the machine.

Windows npm `codex.cmd` is launched via Node and its Codex JavaScript entry point,
not interpolated through a command shell. Keep prompt text and attachment paths
in structured protocol data. A working initialization/config-read probe does
not establish authenticated model requests, desktop input or image extraction.

### Defaults and bounded resources

| Setting / resource | Current default or bound |
|---|---|
| Shared access file absent | `full-access`; invalid/unreadable file selects read-only. Saved choices survive installers. |
| GUI reasoning/model | Low reasoning initially; empty model means Codex default. Live catalog constrains advertised reasoning options. |
| Voice input model/device/beam | Multilingual base, CPU int8, beam 3. Preview and adaptive reasoning are off by default. |
| Wake | Listening off; fuzzy matching and sign-in option initially on when configuring listening. Base model, independent saved language/mic. |
| Wake segmentation | 16 kHz, about 0.65 s silence or 4 s max phrase, short overlap, 8 s wake cooldown. |
| Wake pause acknowledgment | 1.5 s deadline, then kill only the stalled wake worker before releasing capture ownership. |
| Warm voice worker | Five idle minutes before unload; model/options changes and shutdown also unload. |
| Speech | Auto on; local male/female by default; optional explicit online Microsoft voices; natural pitch, volume 0.85. |
| Speech timing | 300 ms quiet tail plus interrupted-worker exit; neural preparation 120 s inactivity (progress refreshes), native start 5 s; total 10 min, 6,000-character spoken copy. |
| Layout | Font 14 px, 12-28 px bounds; normal core shown; full chat initially off. Saved pane width constrained to 420-1000. |
| History persistence | 750 ms debounce and explicit flushes at completion/context changes/exit; 8,000,000-byte transcript bound. |
| History list | 100 matching entries, pins first, Unicode case folding; no automatic history deletion. |
| Metrics/checkpoints | Bounded recent records; checkpoint scope hashes Codex home, workspace, access and model. |

### History, attachments and rendering

History has SQLite `conversations` rows containing scope, title/pin/time,
workspace/model/access/thread/status, JSON messages and searchable text. It is
separate from content-free QSettings checkpoints and explicitly confirmed repair
memory. Opening a conversation requires matching current access and does not
widen it. The restored workspace must exist. An entry without a thread starts
a new one only on the next Send, with an explanatory notice.

Clipboard caches can be referenced by multiple history scopes. Check references
before cleanup and canonicalize ownership paths, including Windows aliases and
short-path spellings. Never delete a user-selected original just because a chip
or conversation was removed. Previews are bounded; selecting a binary/PDF is
not proof that Codex read it. Markdown rendering must not load arbitrary remote
images or raw active HTML. Open external links only on user action for supported
HTTP(S) schemes; Copy preserves the source text.

### Speech, wake and settings

Keep speech synthesis separate from transcription and the Codex process.
Neural downloads/inference/playback belong in the owned worker, never the GUI
thread. Keep verified cache installs, bounded chunks, generation IDs and worker
exit before microphone callbacks. Do not kill the warm worker after a successful
utterance; stop an active one immediately on interruption. Neural pitch must
not be artificially lowered. For explicit legacy mode, enumerate Qt
voices by installed locales; `availableVoices()` alone can expose only the
current locale. Explicitly set the chosen locale before its voice. Native errors
can fire synchronously during configuration: recheck generation/cancellation
before `say`. If QtTextToSpeech cannot import because libpulse is missing, text
chat must still start; a test-only mock engine is never a production substitute.

For speech/mic handoff, wake capture must acknowledge pause before output/input
uses the device. Keep the speech tail quiet period. Manual recording can cancel
speech while it is preparing; a later acknowledgment must not start stale speech
or a canceled recording. Warm transcription may remain loaded without capturing.
Settings, refresh/testing, history opening and errors must not auto-submit text.

Preferences tabs currently are Intelligence, Voice, Access, Runtime, Automation,
Wake, Speech. Saved GUI settings use QSettings; the shared access file is the
exception because terminal launchers also read it. Do not rewrite the user's
global Codex sandbox config or inject a separate login to implement a UI toggle.
The installed Skill and AGENTS block are refreshed by the normal installers;
editing the checkout alone does not refresh already-running Codex instructions.

## 13. Installation and update handover

Dependency-aware bootstrap entry points now exist: `scripts/update-cachyos.sh`
and `scripts/update-windows.ps1`. The [download-and-run commands](docs/install-desktop.md#automatic-dependency-aware-update-cachyos-and-windows-11)
work before cloning, check packages, use uv Python 3.12/frozen voice dependencies,
run the existing installers and reuse login (device auth only when needed).
CachyOS includes a full pacman upgrade; Windows uses winget/PATH refresh.
Both preload verified default neural voices; no Windows speech capability or
TTS UAC step remains in 0.7.0. They reject dirty,
wrong-origin/non-main checkouts and stop on failures. Do not run them on this
cloud just to test: fixture tests replace package managers, login and launchers.
Whisper/backend packages can still download on first use; custom native Codex,
Node-manager selection and OS permission issues may require user attention.
Windows updater root validation uses Git's empty `--show-prefix`, not literal
path equality: Git/PowerShell may choose different long/8.3 aliases for the same
directory. The real-Git Windows fixture found this regression during CI. Final updater
[CI 38869795642](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38869795642)
for `9782c67` passed static/root and both desktop OS jobs, including the Windows
updater/native-stderr helpers. Local root tests passed 77 with three Windows-only
skips. These validate flow/guards without real pacman/winget/UAC installation.

Use the full [OS recipes](docs/install-desktop.md) for fresh installations.
Do not run `git pull` in the user's home directory without specifying the
checkout, and do not assume `scripts/` exists in the current shell directory.
The usual user checkout name is `Tigo`; change paths if it differs.
Close through **Quit Tigo** first: closing the window can leave wake listening
and the old process alive. Stop if Git/update/installation fails.

CachyOS/Linux update in Bash:

```bash
repo_dir="$HOME/Tigo"
git -C "$repo_dir" pull --ff-only &&
bash "$repo_dir/scripts/install-gui-linux.sh" &&
"$HOME/.local/bin/tigo-gui"
```

Windows 11 update in a normal PowerShell window:

```powershell
$repoPath = Join-Path $env:USERPROFILE 'Tigo'
git -C $repoPath pull --ff-only
if ($LASTEXITCODE -ne 0) { throw 'Git update failed; stop here.' }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoPath 'scripts\install-gui-windows.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Installation failed; inspect the error above.' }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoPath 'scripts\tigo-gui-windows.ps1')
```

`C:\Users\...>` is normally CMD, not PowerShell; enter `powershell` before
using PowerShell syntax. A missing relative installer is a checkout/path issue,
not something a newer PowerShell alone fixes. On Windows PowerShell 5, expected
native stderr from `codex mcp get windows-mcp` must not abort the missing-server
probe: the installer scopes a nonterminating policy to that probe and checks
the exit code. Real registration failures still stop installation.

Full updaters preload the two default neural models after installing locked
voice dependencies. Ordinary installers defer this to first use. Windows no
longer installs a Russian system speech capability; `-SkipRussianVoice` is a
compatibility no-op. No TTS elevation or language pack is needed. Linux output
and recording use PortAudio. Other distribution packages are in the recipes;
Speech Dispatcher/system voices apply only to explicit legacy mode.
Neither the GUI installer nor this cloud work bypasses UAC or installs a system
input daemon. After updating Skill/persona/ownership guidance, start a new
conversation to load it. Keep using the existing Codex login.

## 14. Development environment and CI investigation

Observed cloud checkout: `/workspace/Tigo`, local branch `work`, remote
`origin` points to this repository. Do not assume a future task restores the
same branch, cached files or running processes. Inspect actual status first.
Use the existing checkout; do not create an extra worktree unless requested.
Development here observed Python 3.12.14, uv 0.12.23 and Codex CLI 0.159.2.
These are observations, not promises about the user's installation. CI pins uv
and Python in `.github/workflows/validate.yml`; use the checked-in frozen lock.

In this cloud, writable cache directories under `/tmp` avoided cache permission
problems. A previously exercised invocation was:

```bash
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software XDG_CACHE_HOME=/tmp/tigo-cache UV_CACHE_DIR=/tmp/uv-cache uv run --project gui --frozen --extra speech python scripts/check_desktop_ui.py
```

The GUI environment is `gui/.venv`; root tests mostly use the standard library.
Do not run the real desktop installers just to prepare headless tests: they
modify the developer's Codex registration/managed instructions and menu entries.
No authenticated model request or live user desktop is needed for fixture tests.
There is no running web service or localhost preview required by this project.

Some temporary schema/source files existed under `/tmp` during development;
they are not part of the repository or a reproducible dependency. Inspect the
installed Codex schema/version when changing protocol assumptions. Importing
`tigo_gui.backend` needs Qt; pure helpers can be tested without Qt. A missing
native speech plugin in this headless machine does not mean Windows lacks voices.

The managed cloud uses a policy-controlled proxy. Use its runtime/setup Skills
and observed environment status when available; do not dump credentials or
disable proxy/TLS verification. Native Git HTTPS read/push worked with the
session's configured authentication without a visible personal token. GitHub
API access was not needed and was not established by successful Git operations.
No new environment draft was necessary for these documentation updates.

Public GitHub Actions pages supplied run/job/step state when API access was
unavailable. Inspect only relevant metadata or failure annotations, not whole
embedded page payloads. `scripts/check_desktop_ui.py` captures child test output
and publishes the exit code plus final traceback in a CI annotation; this also
helps diagnose native Qt crashes that bypass unittest summaries. A green workflow
includes the actual process/QML and smoke steps; verify those, not just a badge.

CI has a static/root job and a two-OS desktop matrix. Ubuntu installs Qt runtime
libraries including `libpulse0`; desktop jobs use offscreen/software rendering,
locked dependencies, process/QML tests, protocol/simulated audio and app smoke.
Windows additionally runs the PowerShell 5 shared-profile probe. Documentation
and managed scripts have an English-only check. Runtime changes need relevant
tests; documentation-only changes need source/links/format checks, not fabricated
new platform validation. Publish result-only reports with `[skip ci]` when no
new execution is needed. Preserve actual multiline commit/PR text; never log
private data, session tokens or credentials into reports.

## 15. Research background and documentation map

Earlier research examined Tigo/Codex/OpenCode projects and visual agents. It
informed mechanisms, not a wholesale code import or a transport migration.

| Reference | Relevant takeaway / boundary |
|---|---|
| Big-Guan/jarvis-codex | Owned app-server, scoped conversation resume and unified Stop. Its macOS-specific wake/cloud voice path is not our portable local Russian STT. |
| levinjeejan/opencode-jarvis | Typed incremental assistant text, persistent sessions, audio separation and explicit states. We kept Codex; Piper/full-duplex were not imported. |
| renjfk/opencode-voice | Saved microphone/model/language controls. No extra normalization model call is added to every utterance. |
| QwenAudio/qwen-audio-agent | Task lifecycle/status and persistence. No distributed gateway or parallel desktop-input workers were introduced. |
| JaimeParker/stable-jarvis | Deliberate verified knowledge and reusable Skills; a research assistant, not direct evidence of desktop automation. |
| Microsoft UFO / Agent-S / E2B Desktop | App routing, grounding, short verified batches and fewer planning round trips. No claimed performance superiority. |
| RoboticWorx/PolyCast5 | Queue/generation IDs discard abandoned tasks. Reviewed Bluetooth keyboard work lacked screen observation, and the reviewed STT upload selected English. It does not prove local Russian STT or verified desktop success; its CC BY-NC-SA source was not copied. |

Pinned source links and the review date are in [related-projects.md](docs/related-projects.md).
That review predates subsequent wake/system-TTS features: historical statements
that spoken output or wake are future work are superseded by this snapshot.
It is not a live inventory of upstream releases. Recheck licensing, installed
schemas and official source before adopting additional code/dependencies.

| Guide | Use it for |
|---|---|
| [README](README.md) | Public feature summary and entry points. |
| [Change report](changes.md) | Dated source changes, failures/fixes and actual verification. |
| [Long handoff](docs/AI_HANDOFF.md) | Historical investigation detail; older sections can be superseded. |
| [Desktop app](docs/desktop-app.md), [GUI conveniences](docs/gui-conveniences.md) | Window controls, artwork, messages, attachments, history, storage and shortcuts. |
| [Install recipes](docs/install-desktop.md), [Linux](docs/linux.md), [Windows](docs/windows11.md) | Fresh install/update prerequisites, platform integration and known failures. |
| [Access](docs/full-access.md), [Hypruse access](docs/hypruse-access.md), [security](docs/security.md) | Shared profile, checkbox, ownership, confinement and permission boundaries. |
| [Runtime](docs/runtime.md), [performance](docs/performance.md) | Persistent workers, protocol/workflows, timing and avoiding repeated round trips. |
| [Wake](docs/voice-activation.md), [speech](docs/speech-output.md), [voice notices](docs/voice-notices.md), [memory/voice](docs/memory-and-voice.md) | Microphone modes, neural voice setup/provenance, legacy mode and explicit repair memory. |
| [GUI operator](docs/gui-operator.md), [navigation](docs/gui-navigation.md), [shortcuts](docs/shortcuts.md) | Backend-aware actions, regions, pointer selection, keyboard/compositor differences. |
| [MCP/Skills](docs/mcp-and-skills.md), [usage](docs/usage.md), [related projects](docs/related-projects.md) | Instruction/tool integration, terminal usage and source research. |

## 16. First actions after context rollover

1. Read the resume card, preserved decisions and latest Windows incident above.
   Treat this document as a snapshot; incorporate newer user steering.
2. Inspect the real checkout/agent instructions, `git status`, recent commits and
   current remote before editing. Do not reset another contributor's changes.
3. Read the newest `changes.md` entries and relevant source/tests. The latest
   implemented GUI behavior is 0.14.2 as of this handover; inspect actual source
   and distinguish canceled working-tree drafts from released behavior. A later
   documentation commit does not require a runtime version bump.
4. Continue the actual requested task. If the user says to continue Windows
   troubleshooting, distinguish unknown live diagnostics from already-completed
   code work. Do not promise permanent screen ownership or repeat the old
   request for an unavailable raw error. Use a fresh supported status if needed.
5. Choose checks proportional to the new change. Preserve Codex app-server,
   shared account, cancellation guards, local voice review and human takeover.
   Do not add deferred providers, bots or roadmap features without a new request.
6. Update this snapshot and `changes.md`, publish within the session's authorized
   scope, verify remote state and report concrete results/limits in Russian.
   Avoid declaring hardware validation from fixtures or repeatedly running both
   platforms for a documentation-only follow-up.

At this handover point, the only live-machine follow-up identified is obtaining
fresh ownership/tool-version evidence if the user continues that Windows issue.
There is no approved backlog implied by the research table. The context needed
to maintain and extend the current implementation is now preserved in tracked
documentation rather than depending on temporary files or conversation memory.
