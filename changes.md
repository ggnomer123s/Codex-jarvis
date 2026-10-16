# JARVIS change report

This tracked report records implemented changes, their source commits and the
verification actually performed. Add a dated entry for every subsequent change,
including documentation and CI fixes. Keep the newest entry first, link the
relevant commits or files, and distinguish automated checks from live hardware
validation. Do not record user conversations, recordings, credentials or local
machine configuration here. Dates below are report dates; Git history remains
the source of commit timestamps.




## 2026-10-16 — Complete context-rollover handover

- Expanded `readmeai.md` with a first-read resume card and navigation, established
  collaboration/product preferences, the latest Windows incident and remaining
  live-machine unknowns, source/CI history, cancellation/protocol/audio/storage
  contracts and defaults, guarded Windows/Linux update commands, cloud/CI
  investigation notes, competitor-research boundaries and the documentation map.
- Explicitly recorded that runtime 0.6.1 is implemented/published/verified, no
  feature backlog is implicitly approved, and the user's actual Windows service
  has not been remotely diagnosed or repaired. Preserved the distinction between
  default Full Access and human desktop ownership, including the idle timer
  restart caused by physical input and the unavailable old raw tool error.
- Added concrete instructions for continuing after context rollover without
  redoing completed work, repeating already-answered questions, changing the
  transport/account model or treating historical declined ideas as new tasks.
  No credentials, private file contents, transcripts or machine-specific secrets
  were added. Linked the expanded sections from README and refreshed the long
  handoff's stale source-version introduction.
- Verification: reviewed current source constants, paths, contracts, Git history,
  existing reports and CI definitions; checked Markdown links/anchors, English
  text, code fences, Bash snippet syntax and `git diff --check`. Documentation
  only: no runtime version bump, new platform/hardware run or environment setup
  change. This handover commit skips CI; preceding runtime evidence remains below.

## 2026-10-16 — Windows desktop ownership diagnostics (GUI 0.6.1)

- Investigated the reported temporary user-control hold against upstream
  Windows-MCP `c9a307c`. Full Access already defaults on with its saved checkbox;
  it controls Codex files/commands and does not grant permanent desktop ownership.
  The exact tool/error from the user's session was unavailable, so no claim of
  having fixed or remotely changed that Windows machine is made.
- Added Access > Check desktop control on Windows and `/desktop-status` through
  the existing app-server. Checks inventory for windows-mcp/ControlStatus, reads
  state/policy/remaining idle wait, and shows a labeled snapshot. It sends no
  model turn, input or backend configuration change. Missing tools, malformed
  results and refusals fail visibly with no alternate input route or retries.
  Stop cancels a pending owned check; diagnostic success/failure does not alter
  the reasoning heuristic's previous task state. Full Access persistence,
  shared Codex home/login and human takeover protection remain intact.
- Updated Skill and managed AGENTS guidance: distinguish ownership from sandbox
  access, report the actual wait, allow an idle interval, recheck before one
  observation attempt, and pause if still blocked. Unrelated authorized file
  work may continue; uncertain mutating actions are not automatically repeated.
- Updated README, readmeai, access/Windows/desktop/runtime guides and handoff;
  linked pinned upstream ownership/ControlStatus sources. GUI/lock/client is
  0.6.1; no new dependency or separate profile was added.
- Verification: 72 root tests discovered (71 passed; native Windows probe skipped
  locally), 65 passing Qt tests including the production-window diagnostic
  button, read-only calls with no model turn, missing tools, refusal and Stop.
  Targeted final regressions, Python syntax, English Markdown, 119 local links/
  fragments, Access-tab smoke, frozen lock and diff checks passed. Cross-platform
  CI [run 38866945827](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38866945827)
  for [d63f53d](https://github.com/ggnomer123s/Codex-jarvis/commit/d63f53d) passed
  static/root and Ubuntu/Windows desktop jobs, including the native Windows
  shared-profile probe. Real Windows desktop input, service ownership and
  authenticated model tasks were not exercised in this cloud. This result-only
  documentation follow-up skips CI.

## 2026-10-15 — Consolidated AI project overview

- Added root `readmeai.md` as the first-read context for another AI maintainer:
  project purpose, JARVIS mentor character, app-server/MCP architecture and
  lifecycle, current GUI/voice/speech/workflow features, local state, access,
  installation, source map, development checks and known regression paths.
- Recorded decisions to preserve: one existing Codex home/login, app-server-only
  GUI transport, saved default Full Access, reviewed voice submission and one
  current desktop assistant. Distinguished deferred providers/specialist bots,
  declined roadmap ideas and hardware limitations from implemented behavior.
- Linked the overview prominently from README and the long AI handoff; refreshed
  the stale README continuation date and explained that older handoff sections
  can describe superseded behavior. The root overview does not replace installed
  Skills/AGENTS instructions or grant authority to publish or run unrelated work.
- Verification: source/documentation consistency review, local Markdown link and
  fragment checks, English documentation check and `git diff --check`. This is a
  documentation-only update; no runtime/model/audio/hardware or new platform
  test run is implied. The commit skips CI; the preceding runtime verification
  remains recorded below.

## 2026-10-15 — JARVIS mentor character and local speech (GUI 0.6.0)

- Updated the installed `jarvis-desktop` Skill and managed AGENTS instructions:
  composed, respectful mentor-oriented conversation in the user's language,
  concise results, restrained wit and thoughtful disagreement. The persona
  does not change tool authorization or claim fictional identity. Existing
  installers refresh both managed sources; start a new conversation afterward.
- Added lazy local Qt TextToSpeech output through Windows winrt/sapi or Linux
  speechd/flite. Automatic reading defaults on for the current successful final
  answer; Read also works with auto off. Streaming/commentary, canceled/failed
  turns and opened history remain silent. Native errors stay visible without
  resending requests. Test/mock engines are injected only in tests.
- Added Preferences > Speech: installed voice selection, rate/pitch/volume,
  refresh, test and stop; immediate saved Speech on/off in the composer, message
  Read, Stop speech/Escape and a distinct cyan speaking animation. Enumerates
  every installed Qt locale so Russian can be selected on an English desktop;
  Automatic matches Russian/English and prefers an installed adult male voice.
  Missing matching voices are reported rather than reading in another language.
- Spoken text removes fenced code, images, raw URLs and Markdown; limits output
  to 6,000 characters with a continuation notice. Chat text is preserved.
- Speech waits for the real wake-worker pause acknowledgment or process exit.
  Wake capture stays paused during output and a 300 ms tail cooldown. Manual
  recording interrupts speech and waits for quiet; generation/recording IDs
  reject canceled or superseded callbacks. Warm transcription remains reusable.
- Added speech prerequisites to distribution recipes and installer messages,
  a speech setup/privacy/troubleshooting guide, and updated README, Windows,
  desktop, runtime, wake, security and handoff docs. GUI/lock/client version is
  0.6.0; Qt speech is bundled, with no new Python dependency or cloud TTS key.
- Verification: 68 root tests discovered (67 passed, one Windows-native probe
  skipped locally), 60 passing Qt process/QML tests, and successful normal and
  Speech-settings smoke checks. English docs/scripts, relative Markdown links,
  Python/Bash syntax and the frozen dependency lock passed. Tests cover native
  Qt API via its test plugin,
  locale-specific voice discovery, errors/cancellation, final-only reading,
  real subprocess wake/manual-mic handoff, and production-window controls.
  This cloud has no usable system speech runtime/speakers; missing-engine UI
  was checked. Actual OS voice quality and physical audio remain target-machine
  checks. Initial [CI run 38779085859](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38779085859)
  passed static/root but found Ubuntu lacked `libpulse.so.0`, required to import
  QtTextToSpeech. Added libpulse client-library prerequisites to CI and recipes;
  missing speech-module imports now become a visible speech error while the
  text GUI stays usable. Added an isolated-process missing-library regression.
  Final [CI run 38779340998](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38779340998)
  for `f01ecf5` passed static/root, Ubuntu desktop and Windows desktop jobs,
  including the Windows PowerShell 5 shared-profile probe. Source commits:
  [208df7c](https://github.com/ggnomer123s/Codex-jarvis/commit/208df7c) and
  [f01ecf5](https://github.com/ggnomer123s/Codex-jarvis/commit/f01ecf5).
  This result-only report update skips CI.

## 2026-10-15 — Conversation workspace conveniences (GUI 0.5.0)

- Added a draggable core/chat splitter, saved pane width, Hide/Show core and a
  saved Full chat mode that hides both artwork and sidebar. Moved the single
  composer below the conversation so input/model/reasoning/voice stay reachable
  in every layout. Hidden artwork animation pauses. Scrolling away from the end
  stops automatic following; Latest restores it.
- Added `presentation.py` and `MessageCard.qml`: Markdown headings, lists, tables,
  emphasis/web links, fenced code/language labels and Copy code. Raw HTML/image
  loading and non-HTTP(S) links are inert. Message Copy preserves source text;
  Edit & resend restores a request to the draft and requires manual Send as a
  new turn. Existing messages/actions are not rewritten or replayed.
- Added local file picking, drag/drop, clipboard screenshot paste, removable
  attachment chips and `AttachmentPreview.qml`. Images use app-server localImage;
  other files use explicit name/path text references with Codex tool permissions.
  Preview supports bounded image/UTF-8 content, including split multibyte text.
  Limits are 10 regular local files, 20 MB each, 20 megapixels per image.
  Changed/missing files reject Send while preserving the draft/selection.
- Added `history.py`, local SQLite storage and `HistoryPopup.qml`: searchable
  titles/message contents (Unicode case folding), pin/unpin, rename, explicit
  deletion and conversation reopening. Saves are debounced and flushed at task
  completion/context changes/exit. Current Codex-home scope is retained; opening
  never widens access or starts a request. Next Send resumes the saved thread.
  A transcript without a thread explains that its next request starts a new one.
- History stores local message/attachment metadata and private clipboard-image
  copies separately from QSettings checkpoints, repair memory and content-free
  timing exports. Original files remain untouched; unused owned clipboard images
  are cleaned after reference checks. History errors are surfaced without losing
  the active conversation; individual transcript limit is 8 MB, list limit is
  100 matching entries without automatic history deletion.
- Added a visible activity/error card with request elapsed time, live phase,
  tool/connection details and Stop. Added Ctrl+H, Ctrl+Shift+F, Ctrl+O and
  Ctrl+Shift+V; retained existing new/send/voice/settings/access behavior.
- Updated README, desktop/runtime/security/shortcut guides, handoff and UI
  screenshots; added `docs/gui-conveniences.md`. Updated app/lock/client version
  to 0.5.0 without new dependencies. Claude Code and API backends remain deferred.
- Verification: 66 root tests discovered (65 passed, one Windows-native probe
  skipped locally), plus 48 passing Qt tests. New durable-history/scoping/search
  and real-process attachment/resume/clipboard/rendering cases, actual-window
  divider drag/full-chat/code-copy/file-drop/history controls, and full/compact
  rendered previews passed. App smoke, Python syntax and frozen lock passed.
  Input tags were checked against the installed Codex-generated JSON schema
  and upstream UserInput definitions (structured mentions target apps/plugins);
  no authenticated model/image/PDF request or real desktop/microphone task ran.
  CI outcomes are recorded below.
- Initial [CI run 38746821392](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38746821392)
  passed static/root and Ubuntu desktop checks, but Windows found that an
  unsubmitted clipboard-image cache file was retained after removal. Attachment
  inspection canonicalizes paths while settings can retain another spelling.
  Cleanup now resolves both parent paths before checking ownership; the
  clipboard regression also exercises a noncanonical parent spelling. All five
  targeted convenience tests pass locally.
- Final [CI run 38747237298](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38747237298)
  for `eb34751` passed all three jobs: static/root checks, Ubuntu desktop and
  Windows desktop, including the clipboard cleanup regression and real QML
  controls. This report/handoff-only follow-up skips another CI run. Native
  user-machine file/model/clipboard/desktop permissions remain environment-specific.

## 2026-10-15 — Adjustable conversation text size (GUI 0.4.1)

- Added A- / A+ buttons and a size indicator beside CONVERSATION in the right
  panel. Requests, streamed responses and status text update immediately from
  12 to 28 pixels, in two-pixel steps. Increased the default from 12 to 14 pixels.
- Persisted `conversationFontSize` in GUI settings. Changing it leaves model,
  access, connection, conversation and composer draft intact, and is available
  during active requests. Added dedicated notification rather than runtime refresh.
- Updated the actual QML window check to exercise both buttons, disabled limits,
  rendered user/assistant fonts, persistence, unchanged history/runtime/draft,
  and compact-window control bounds. Updated the desktop guide, version/lock
  and screenshots; no new dependencies.
- Local verification: all 43 Qt tests passed, including actual-window font
  changes during an active request and restart persistence. Actual application
  smoke passed; inspected full and compact (1060x760) renders with 20 px sample
  messages. Python syntax, frozen lock, documentation links/language and
  whitespace checks passed.
- Final [CI run 38742059923](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38742059923)
  for implementation `03ef8fe` passed static/root checks and both Ubuntu/Windows
  desktop jobs. This report/handoff-only follow-up skips another CI run.
  Preview messages were local fixtures; no authenticated task or real microphone
  was used for this UI change.

## 2026-10-15 — One Codex account, default Full Access and composer controls

- GUI, Linux/Windows CLI and legacy Full Access commands now reuse the existing
  `CODEX_HOME` or ordinary `.codex` directory, login and MCP configuration.
  Removed separate-home preparation, extra authentication and acknowledgement
  requirements; old full installers delegate to the standard installers.
  Existing private home directories are not deleted or imported.
- Full Access defaults on. The Access checkbox saves a small shared preference
  for the GUI and regular `jarvis` command, including sandbox selection across
  restarts. Explicit `jarvis-full` aliases still request Full Access in the same
  home. A corrupt preference falls back to read-only. Access changes close the
  owned app-server and clear context; Codex app-server remains the sole transport.
- Fixed Windows PowerShell 5 native-stderr handling for an absent `windows-mcp`:
  the probe reports absence without aborting installation, while failed actual
  registration still fails. Removed ambiguous non-ASCII installer banners and
  retained `codex.cmd` compatibility and per-process execution policy.
- Updated GUI installers, normal/full launchers and custom-home instruction
  paths for all supported Linux session backends and Windows. New registrations
  enable X11 input, omit Hypruse confinement and Windows tool exclusions;
  existing registrations retain their settings. OS/authentication guards and
  refusal to launch Full Access elevated remain.
- Added model and reasoning selectors at the bottom left of the input composer,
  preserving the unsent draft. Models may be selected or entered; reasoning
  choices follow model-advertised support with validated fallback. Model changes
  reset the conversation; changing reasoning alone preserves it. Preferences
  uses the same options. GUI and lock version are now 0.4.0, without new dependencies.
- Updated README, install, access, runtime, security, backend and handoff guides.
  Added shared-preference and four-session installer integration checks, same-home
  GUI lifecycle/checkbox/model tests and a native Windows PowerShell 5 regression
  in the Windows CI job. Refreshed actual main/Access/Voice/Wake QML screenshots.
- Local verification: 63 root tests discovered (62 passed, native Windows-only
  probe skipped on Linux), plus 43 passing Qt tests. Actual QML smoke screenshots,
  compact control bounds, Bash/Python syntax, frozen lock, local document links,
  English docs/scripts and whitespace checks passed. New four-session installer
  tests use fake binaries and temporary homes; no authenticated user task,
  microphone recording or real desktop input was executed.
- Final CI [run 38740007768](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38740007768)
  for implementation `0510971` passed all three jobs: static/root checks, Ubuntu
  desktop and Windows desktop. Both desktop process/QML, protocol/audio and
  actual-window smoke steps succeeded; the native Windows PowerShell 5 missing-MCP
  regression also passed. This report/handoff-only follow-up skips another CI
  run. Real target-machine microphone, portal and desktop permissions still need
  verification on the user's system.

## 2026-10-15 — Optional local background voice activation

- Added `wake.py`: continuous local CPU Whisper transcription in bounded
  speech-gated phrases, English/Russian wake-name matching with optional known
  variants/one-edit tolerance, an eight-second cooldown and pause generations.
  Only wake/status events leave the worker; audio/ordinary transcripts remain
  transient memory. An inference backlog is bounded and reported.
- Added `wake_control.py`: opt-in settings, owned process, status/errors,
  acknowledged stream closure before manual voice starts, stale-event rejection
  and a bounded stop fallback for stalled pause. Disable stops listening even
  if startup-entry removal fails.
- Added `autostart.py`: owned XDG desktop entry on Linux and per-user HKCU Run
  value on Windows, safely quoted environment paths and refusal to overwrite
  unrelated registrations. Startup is registered only through user settings.
- Added `activation.py`: same-user local IPC and an instance lock so a second
  launch restores the existing GUI instead of opening a duplicate.
- Updated `app.py` for `--background`, tray restore/disable/quit controls,
  minimized fallback without tray support and wake-to-window activation.
- Updated `backend.py`, `Main.qml` and new `HudCheckBox.qml` with Wake settings,
  microphone status, background-close behavior and manual voice coordination.
  Waking opens the window only; it never sends a model request or executes speech.
- Added Windows launcher's `-Background` switch. Bumped GUI/lock version to 0.3.0
  with no new dependencies. Added `docs/voice-activation.md` and updated README,
  runtime, desktop, memory/voice, security, source-review and handoff guidance.
- Added 11 stdlib/audio/model-fixture tests and 10 Qt process/IPC/lifecycle tests;
  the production window test now visits the Wake tab. Local validation currently
  passes 60 root and 44 Qt tests (104 total), with no real microphone/model
  download or OS startup modification during tests. Inspected the actual Wake
  settings screenshot. Python syntax, frozen lock, English docs/scripts, local
  documentation links and whitespace checks passed. Tests also cover Stop/Cancel
  before microphone handoff. Final CI outcome is recorded below.
- Scope: explicitly requested wake activation supersedes the earlier deferred
  wake proposal only. Other declined features and specialized bots are unchanged.
- Initial [CI run 38703887487](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38703887487)
  for `9cbc1d4` passed static/root checks and Ubuntu desktop, but Windows desktop
  failed. The public annotation truncated the traceback. Updated
  `scripts/check_desktop_ui.py` to include the child exit code, enable Python
  fault traces and keep the final error within the public annotation limit;
  investigating before claiming Windows success.
- Diagnostic [run 38704668136](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38704668136)
  showed a failed activation assertion rather than a native crash. Updated
  `activation.py` to wait for an explicit owner acknowledgement before closing
  the local channel, and changed the IPC regression to launch a real second
  process so the owner's event loop can accept the Windows named pipe.
- Final [CI run 38704976904](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38704976904)
  for [2496dfe](https://github.com/ggnomer123s/Codex-jarvis/commit/2496dfe) passed
  all three jobs: static/root checks, Ubuntu desktop and Windows desktop,
  including real cross-process activation, Qt/QML, simulated speech/protocol and
  window smoke tests. A separate local normal-app/menu boot and clean quit also
  passed with isolated disabled wake settings. No native microphone accuracy or
  real login startup is claimed. This result-only report/handoff update skips CI.

## 2026-10-15 — Activity-reactive artwork replaces the central J

- Added original generated artwork in `gui/jarvis_gui/ui/energy-core.png`.
  Rebuilt `Orb.qml` with woven filaments, orbital particles, breathing,
  audio-level response and activity-specific motion instead of a central letter.
- Mapped preparation, recording, transcription, planning, action, verification,
  completion, failure and stop to distinct effects, colors and text labels.
  Completion waves settle; stopped motion freezes. Animation targets 20 Hz in
  standby / about 30 Hz while active and pauses when minimized. One Canvas and
  the bundled PNG require no new runtime dependency or network call.
- Updated `Main.qml` to show preparation during profile setup and size the core
  according to window height, keeping input controls visible in short windows.
- Updated README, the desktop guide and maintainer handoff; refreshed the public
  screenshot and added an animated preview captured from simulated states in the
  real QML window. Documented the state effects and actual visualization limits.
- Recorded the scope decision: previous unimplemented roadmap proposals are
  declined; specialized bots are a design discussion, not part of this change.
- Verification: rendered all 13 runtime/voice state inputs without QML warnings;
  checked audio attack/release, active motion, minimized pause/resume, stopped
  freeze and profile-preparation mapping. Checked compact/short layouts for
  fully visible composer and Send controls at 1060x760, 1440x760 and 1440x900.
  The existing actual-window test, documentation links/language and whitespace
  checks passed locally.
- Published implementation as [7cd7a76](https://github.com/ggnomer123s/Codex-jarvis/commit/7cd7a76).
  [CI run 38700213462](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38700213462)
  passed static/root checks and both Ubuntu/Windows desktop jobs, including
  process/QML tests, protocol/simulated audio and window smoke tests. The
  result-only report/handoff update uses `[skip ci]`. This is rendering and
  automated-test coverage, not a new real-microphone or live-desktop test.

## 2026-10-15 — Fresh Linux and Windows CI passed

- Requested a new full GitHub Actions run through a report-only push to `main`,
  following the request to run the platform checks again. This replaces the
  earlier pause on additional runs.
- The existing workflow covers static checks, root unit tests and separate
  Ubuntu/Windows desktop jobs with process/QML tests, simulated audio and a
  desktop-window smoke test. No application or workflow code changed.
- Result: [run 38698094096](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38698094096)
  for [c9e7b2d](https://github.com/ggnomer123s/Codex-jarvis/commit/c9e7b2d)
  completed successfully. Verified all three jobs and their individual steps:
  static/root checks, Windows desktop and Ubuntu desktop. Both desktop jobs
  passed locked dependency installation, process/QML tests, protocol/simulated
  audio tests and window loading; Ubuntu also installed the Qt runtime libraries.
- Updated this report and the maintainer handoff with the completed result.
  Checked documentation links, the English-only rule and whitespace. Publishing
  this result uses `[skip ci]` to avoid starting another run for the report.

## 2026-10-15 — Verification completed and change reporting started

- Created this report, including a backfill of the current runtime work and a
  commit-linked overview of the preceding GUI/install changes.
- Linked the report from [README.md](README.md) and added ongoing maintenance
  instructions and current CI evidence to [the maintainer handoff](docs/AI_HANDOFF.md).
- Read the existing [GitHub Actions run 38629351827](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38629351827)
  for [8abce2e](https://github.com/ggnomer123s/Codex-jarvis/commit/8abce2e).
  Its static-check, Ubuntu desktop and Windows desktop jobs all succeeded.
  In particular, Ubuntu installed the missing Qt libraries and passed the
  process/QML tests, protocol/simulated-audio tests and desktop-window smoke test.
- No additional platform runs were requested for this verification. The run
  above had already been triggered before the request to avoid repeating both
  platforms. This documentation-only update uses `[skip ci]` in its commit
  message; it does not change application code or workflow coverage.
- Checked this documentation update for whitespace errors, local Markdown-link
  targets and the repository's English-only documentation rule. The previous
  application tests were not rerun for documentation-only changes.

## Runtime and performance update — backfilled 2026-10-15

Implementation: [93b0437](https://github.com/ggnomer123s/Codex-jarvis/commit/93b0437).
Behavior and configuration: [runtime guide](docs/runtime.md).

### Codex connection and chat

- Added `gui/jarvis_gui/app_server.py`: an owned, persistent local stdio
  JSON-RPC connection to Codex app-server, initialization, thread start/resume,
  model and MCP discovery, task dispatch and protocol interruption.
- Updated `backend.py` and `core.py` to use app-server as the GUI's only model
  transport. Removed the per-message exec transport; added bounded messages,
  pending requests, deadlines and cleanup of the owned process tree.
- Retained process/thread context between follow-ups. Scoped access/profile
  changes close the old process and clear runtime context. Unexpected approval
  requests are declined; Full Access remains separate and checkbox-gated.
- Added `messages.py` for incremental chat rows. Text deltas are coalesced at
  approximately 33 ms; completed messages replace provisional content without
  duplicate answers. Reasoning/tool events report activity separately.
- Added stale-event guards for task, turn, profile and recording changes.

### Local voice

- Added a persistent `voice.py --worker` path that retains one multilingual
  faster-whisper model between recordings and unloads it after five idle minutes.
  The one-shot CLI voice path remains available.
- Moved processing out of the realtime audio callback into a bounded PCM queue.
  Recording is explicit, limited to 60 seconds and held in memory.
- Added microphone selection, CPU int8 or optional NVIDIA CUDA int8-fp16,
  beam sizes 1/3/5 and a model preparation/microphone-list control. Retained
  automatic language detection and 15 language presets, including Russian.
- Added optional provisional chunk text on pauses/intervals, followed by a
  final Whisper transcription. Final text still requires review and manual Send.
  This is chunk preview rather than true online decoding or always listening.

### Timing, commands and checked workflows

- Added `runtime.py`: the last 30 completed task timing records, per-tool
  durations, voice timings and JSON export without prompts, responses, tool
  arguments, screenshots or audio.
- Added optional local reasoning selection without a separate classifier-model
  request. Added up to 30 conversation pointers scoped to workspace, Codex home,
  access and model. Resume explicitly restores conversation rather than replaying
  desktop actions.
- Added local `/help`, `/status`, `/metrics`, `/workflows`, `/open-workspace`,
  `/resume` and `/new` commands without model inference.
- Added `workflows.py`: user-saved exact aliases for 1–5 serial desktop MCP steps,
  optional preconditions, required postconditions, bounded observation waits
  and stop on refusal/failure. Actions are never automatically repeated.
- Restricted direct workflow tools to the configured supported desktop servers.
  Existing backend input/confinement guards remain in effect; these shortcuts
  do not expose arbitrary shell, registry or filesystem tools.
- Updated `scripts/x11_mcp.py` with structured active-window identity and bounded
  synchronous visible-window waiting. Updated the desktop Skill accordingly.

### Interface, dependencies and documentation

- Updated `Main.qml` and `Orb.qml`: Runtime/Automation preferences, connection
  badge, timing summary, Resume control, task-state colors, smoothed audio
  response and ripple effects; animation pauses when minimized.
- Bumped `gui/pyproject.toml` and `gui/uv.lock` to GUI version 0.2.0 without adding
  dependencies.
- Added [the source review](docs/related-projects.md) of jarvis-codex,
  opencode-jarvis, opencode-voice, qwen-audio-agent and stable-jarvis, plus earlier
  references including PolyCast5. Recorded commit snapshots, useful mechanisms
  and adopted scope. No external source/assets were copied and no OpenCode
  runtime was introduced.
- Added `docs/runtime.md`; updated README, `docs/desktop-app.md`,
  `docs/performance.md` and `docs/AI_HANDOFF.md` to reflect implemented behavior
  and remaining work.

### Verification and limits

- Added/updated the fake app-server fixture, Qt backend/window/workflow tests,
  protocol/runtime/simulated-voice tests and X11 regressions.
- Passed 49 root unittest tests and 34 Qt/process/QML/workflow tests locally
  (83 total). The Qt suite also passed in a fresh Python 3.12 environment.
- Passed the desktop smoke test, lock-file check, Python/Bash syntax checks,
  documentation checks and local-link/whitespace checks. Inspected a rendered
  Linux offscreen GUI screenshot.
- A real Codex CLI 0.159.2 initialization and `config/read` probe succeeded on
  Linux without making an authenticated model request.
- CI evidence for the final code is linked in the 2026-10-15 entry above.
  Audio and desktop tests use simulated counterparts; real microphone capture,
  CUDA, authenticated model tasks and live desktop workflows still require
  target-machine validation. No measured end-to-end speedup is claimed.
- General task replay/rollback, Doctor auto-repair, Premiere/DaVinci bridges,
  wake words, continuous screen understanding and spoken answers remain future
  work.

## CI fixes — backfilled 2026-10-15

- [7c63158](https://github.com/ggnomer123s/Codex-jarvis/commit/7c63158): added
  `scripts/check_desktop_ui.py` to capture process/QML test failures, including
  native crashes, and publish failure details in GitHub annotations. Updated
  `.github/workflows/validate.yml` to use it and set matrix `fail-fast: false`,
  allowing each platform's result to remain visible independently.
- [8abce2e](https://github.com/ggnomer123s/Codex-jarvis/commit/8abce2e): fixed the
  Ubuntu runner's missing `libEGL.so.1` by installing `libegl1`, `libopengl0`,
  `libxcb-cursor0` and `libxkbcommon-x11-0` before Qt tests. Updated the handoff
  with the diagnosed cause. The subsequent existing CI run succeeded.

## Earlier GUI/install work — historical source summary

These entries identify preceding repository changes; they do not claim that
their native hardware scenarios were revalidated when this report was created.

| Commit | Implemented change |
|---|---|
| [c222034](https://github.com/ggnomer123s/Codex-jarvis/commit/c222034) | GUI installers prepare the separate Full Access profile; activation uses a checkbox without typed acknowledgement. Windows instructions use an explicit checkout path and clone/update selection to avoid running Git/scripts from the wrong directory. |
| [f2c8534](https://github.com/ggnomer123s/Codex-jarvis/commit/f2c8534) | GUI access/profile controls and sign-in, model selection, multilingual local voice settings and visual preference/status improvements. The later runtime update supersedes its per-message process implementation. |
| [f2cb2f6](https://github.com/ggnomer123s/Codex-jarvis/commit/f2cb2f6) | Copy-ready installation/update instructions for Arch/CachyOS, Debian-family systems, Fedora, openSUSE and Windows 11. |
| [cb8afce](https://github.com/ggnomer123s/Codex-jarvis/commit/cb8afce) | Initial Linux/Windows PySide6/Qt Quick desktop GUI, animated core, Codex chat, local push-to-talk voice and platform launch/menu installation scripts. |
