# Tigo change report

This tracked report records implemented changes, their source commits and the
verification actually performed. Add a dated entry for every subsequent change,
including documentation and CI fixes. Keep the newest entry first, link the
relevant commits or files, and distinguish automated checks from live hardware
validation. Do not record user conversations, recordings, credentials or local
machine configuration here. Dates below are report dates; Git history remains
the source of commit timestamps.

## 2026-10-27 — Live usage panel and account/dictation recovery (GUI 0.15.0)

- Added [native account status](gui/tigo_gui/account.py) and a
  [usage panel](gui/tigo_gui/ui/UsageLimits.qml) above the composer. Displays
  actual five-hour/weekly remaining percentages, reset countdowns and snapshot
  time; reads every minute and consumes account notifications before thread
  filtering. Duration/model buckets, stale and unavailable data are handled
  explicitly. X hides and stops polling; Limits/Runtime restores the saved view.
- Refreshes the existing managed Codex token before thread/task startup.
  Routing/auth 401 errors now provide a deduplicated sign-in recovery flow;
  repeated submissions are blocked without replay. Native successful login
  reconnects the same profile while retaining the chat/thread. The GUI cannot
  grant missing workspace/account access or confirm live recovery in this cloud.
- Final online dictation can fall back to the saved CPU Whisper model using the
  same bounded recording. The default-on Voice checkbox can disable it. A first
  fallback can download the model; recovered text always requires review/Send.
  Preview/wake providers and microphone ownership/cancellation remain separate.
- Added unexecuted account/quota/auth regression cases and account fixture
  responses. Updated current handovers, version metadata and
  [account guidance](docs/account-and-limits.md), dictation/live-voice and
  installation docs. No dependencies or setup commands changed.
- Verification: protocol/schema and source review, changed Python syntax,
  manifest/lock version alignment, documentation links and whitespace. No test
  suites, GUI/hardware checks, authenticated quota/model request or CI run was
  performed, following the user's earlier preference and request to finish
  faster. Publication skips CI. Actual account access remains server-controlled.

## 2026-10-27 — Keep Terra and custom model IDs selectable (GUI 0.14.5)

- The prior catalog fix could only show IDs reported by Codex or the currently
  selected manual ID. Added an explicitly requested `gpt-6.1-terra` shortcut
  separately from advertised models in [preferences](gui/tigo_gui/preferences.py).
  It remains selectable in both pickers even when a Codex catalog omits it;
  this does not claim that the user's account/endpoint supports that model.
- Added up to 64 validated, deduplicated previously selected IDs in QSettings
  `customModels`. Refresh, switching models and restart retain these choices.
  Read-only `config/read` also extracts the effective workspace model ID when
  it is not advertised; other response fields are discarded. Connection and
  workspace guards reject stale config responses, and workspace changes avoid
  reusing another workspace's configured choice through the freshness timer.
- Added reactive selection notes/tooltips identifying catalog-reported,
  configured and unconfirmed IDs. A newly selected model with no advertised
  reasoning metadata starts with Model default. Selection still passes the
  exact ID through existing Codex app-server thread/turn parameters; no silent
  model substitution, alternate transport, account change or access grant occurs.
- Updated catalog regressions for the separate shortcut/config request and
  added two unexecuted cases for Terra/custom persistence and configured-ID
  status. Updated README, model/update guides and both current handovers.
  GUI/version lock metadata is 0.14.5; dependencies/installers are unchanged.
- Verification: reviewed the patch and installed `config/read` protocol schema,
  parsed changed Python and version metadata, checked edited public docs'
  English convention and whitespace. No test suite, GUI run, CI or authenticated
  Terra request was executed, following the earlier stop-testing preference.
  The cloud has no model cache for this inspection; the user's actual desktop
  model catalog and Terra entitlement remain unverified. Publication skips CI.

## 2026-10-27 — Refresh the full Codex model catalog (GUI 0.14.4)

- Fixed [catalog discovery](gui/tigo_gui/backend.py) to request hidden picker
  entries and follow `model/list` pagination, with repeated-cursor/page bounds.
  Names and reasoning metadata publish together only after all pages succeed;
  failures retain the last complete list and expose a visible status/error.
  Hidden picker entries are not a guarantee of account/provider availability.
- Model pickers and Preferences discover live models on opening, coalescing
  checks for 60 seconds. Explicit Refresh reconnects the idle owned app-server
  to reload Codex/provider state while retaining chat, selected model and thread
  ID for resume. Catalog results use a connection generation, so switching
  conversations no longer discards a valid catalog response. Listing never
  starts a thread/turn or changes login/access settings.
- Removed stale disk-cache replacement during preference saves. The initial
  cache reader includes hidden entries and recognizes slug/model/id records.
  [Both QML pickers](gui/tigo_gui/ui/Main.qml) retain selections and typed IDs
  across catalog replacement, and Preferences shows loading/progress/errors.
- Added four focused, unexecuted regressions for paginated hidden models,
  catalog results across conversation changes, failed pages/repeated cursors,
  and chat/thread preservation on explicit refresh. Added a paginated fixture.
- Updated [model guidance](docs/desktop-app.md#use-the-app),
  [update notes](docs/updates.md), README and maintainer/user handovers. New
  releases can also require a Codex CLI update through its original package
  manager and appropriate account access. No dependencies, installer commands,
  Codex transport or account profiles changed. Version/lock metadata is 0.14.4.
- Verification: inspected the installed Codex 0.159.2 generated protocol schema
  (`includeHidden`, cursor pagination, no force-refresh parameter), reviewed the
  patch, parsed changed Python sources and manifest/lock versions, checked the
  edited public docs' English convention and `git diff --check`. No test suites,
  GUI/hardware checks, authenticated model requests or CI were run; publication
  uses `[skip ci]` following the user's earlier stop-testing preference. Newly
  released model availability on the user's actual account remains unverified.

## 2026-10-18 — Hyprland fullscreen indicator and responsive observation (GUI 0.14.3)

- Wayland layer surfaces now use exclusive zone -1, so the border reaches the
  full monitor instead of avoiding panel-reserved work areas. On the observed
  1920x1080 Hyprland output, old edges began at (56,8); new edges span (0,0)
  through the actual screen boundaries, including over a fullscreen window.
- Explicit empty GDK input regions make all four edges click-through. Banner
  background/text also pass clicks through; only Return control accepts input.
  Its clipped logical rectangle updates after GTK allocation/remapping, including
  translation changes; no polling loop, fullscreen input surface or keyboard
  grab is added. Return control hides the saved helper state before signaling.
- Added fullscreen/animated-window guidance to the shipped desktop Skill/managed
  AGENTS and GUI operator guide: use current geometry, avoid repeated empty-tree
  queries and stable-frame waiting for continuously changing games/video.
  This removes avoidable observation waits, not Codex inference latency. The
  existing Hypruse transport, strict seat/auth/lock guards and user takeover
  remain unchanged. No camera/relative-pointer game backend is introduced.
- Added system Pycairo/GI Cairo to the CachyOS/Debian/Fedora setup paths and
  Wayland preflight/diagnostics; updated installation/screen guides, maintainer
  context, handover and GUI version/lock metadata. Windows dependencies/layout
  are unchanged. Earlier canceled wake/setup drafts remain separate.
- Verification: the isolated feature patch passed all 120 GUI/process/QML tests
  and 142 root tests discovered (138 passed, four skips including the opt-in live
  helper test). Installer fixtures check Cairo packages and both successful and
  missing-helper preflight flows without real installation. The mixed working
  tree's separate Debian flow still fails on the canceled setup-state draft;
  that draft was excluded, preserved and not repaired by this task. Frozen lock,
  shell/Python syntax, Skill validation, documentation links/English-only and
  whitespace checks passed.
- Three targeted live/geometry tests passed with the native helper on Hyprland,
  checking full-output edges, empty edge input masks, localized button masks,
  visibility/remapping and EOF cleanup. Final desktop inventory confirmed the
  disposable test window and indicators were removed. A live test click was
  refused after cursor/focus changed; it was not retried or bypassed. No
  successful end-to-end fullscreen click or game-latency measurement is claimed.

## 2026-10-18 — User preferences and next-assistant handover

- Added USER_HANDOFF.md consolidating explicit collaboration rules, selective
  Git handoff, change-report/setup maintenance, established product preferences,
  exact whole-message Copy/Read speech behavior, GUI tool discovery and native
  human-control safeguards. Distinguished deferred providers/ideas and canceled
  working-tree drafts from current assignments and released features.
- Linked the handover from repository AGENTS.md and readmeai.md. Reconciled old
  final-only speech, publishing and runtime-version text in the maintainer guide
  with the latest user correction and observed source state. Existing unrelated
  wake/setup drafts were preserved. No runtime/dependency/installer change.
- Verification: all 83 relative file links across the four handover documents
  resolve; English-only and whitespace checks passed. A four-file commit patch
  excludes earlier wake/setup drafts and passes Git cached-apply validation.
  No runtime/hardware tests were run for this documentation-only change.

## 2026-10-18 — Speak complete message cards (GUI 0.14.2)

- Automatic speech now queues each completed assistant message card (the block
  with Copy and Read) as one job, including commentary/progress and final answers.
  It starts after that card completes, while the overall task can still be busy.
  Text deltas update chat only; the completed canonical text uses the same
  sanitizer and existing 6,000-character speaking-copy limit as manual Read.
- Removed the superseded sentence-speech assembler and its tests, retaining live
  dictation assembly. Per-card completion deduplication and ordered playback
  prevent repeats at turn completion. Stop clears/mutes remaining cards for the
  current task; a new task can speak again. Incomplete cards and restored history
  stay silent. Cancellation, error, microphone and quiet-tail guards remain.
- Updated Speech settings text, speech guides, maintainer resume context and GUI
  version/lock metadata. Dependencies and installation steps are unchanged.
  Earlier canceled wake/setup drafts remain separate and are not included.
- Verification: sixteen targeted speech/Qt tests passed. An isolated patch over
  clean HEAD, excluding canceled drafts, passed all 120 GUI/process/QML tests and
  138 root tests discovered (135 passed, three Windows-only skips). Frozen offline
  lock, Python syntax, changed-guide English-only and diff checks passed. No live
  Windows speaker, microphone or online service latency measurement is claimed.

## 2026-10-17 — Sentence-level speech and shorter playback gaps (GUI 0.14.1)

- Wrapped lines and commas no longer split prose into single-word synthesis
  requests. Completed sentences are emitted separately even when one model delta
  contains several; partial text remains buffered until a sentence or message
  boundary. Fenced code and incomplete-link handling remain in place.
- Removed the fixed 300 ms delay between queued sentences. Dispatch proceeds on
  the next event-loop opportunity once the engine is quiet; the microphone stays
  reserved through the queue instead of being prepared again for every sentence.
  Late-arriving queued speech can also bypass an already-started completion tail.
  The final speaker tail and error/cancellation microphone safeguards remain.
- Added the reported greeting as a character-by-character/wrapped-line fixture
  and queue tests checking sub-300-ms dispatch, sentence order, a single microphone
  reservation and the final quiet tail. Updated live-voice documentation and GUI
  version/lock metadata; no dependencies or installer changes are required.
- Targeted verification: four pure text tests and fourteen speech/Qt tests passed.
  The isolated clean-HEAD GUI/process/QML suite passed all 118 tests, without
  including canceled setup/wake drafts. Final targeted speech tests, frozen-lock,
  Python syntax, English-only guide and diff checks also passed. No live Windows audio
  or online latency measurement is claimed; synthesis and network latency remain.
  This change does not alter dictation or earlier canceled setup/wake drafts.

## 2026-10-17 — Live dictation and incremental assistant speech (GUI 0.14.0)

- Added bounded rolling local/online provisional transcription, refreshed after
  about 1.2 seconds of captured audio when inference is available. Current-window
  text is revised rather than appended repeatedly; window overlap merges words.
  Final full-recording recognition remains authoritative. The existing online
  service receives partial audio while Live text is enabled; this is phrase HTTP,
  not a persistent realtime API. No personal key or new dependency is required.
- Partial text now appears directly in the composer. Final text replaces its
  provisional suffix once. Cancellation restores the original unedited draft;
  manual edits stop automatic replacements and retain send safeguards. Existing
  saved preview opt-out is preserved; new settings default Live text on.
- Assistant message deltas feed a bounded prose/sentence queue, including
  commentary and the final answer, with per-item completion deduplication. Code
  fences, URLs, reasoning and tool payloads are excluded. Local/online/system
  speech use the same queue. Stop speech suppresses further chunks for that turn;
  new tasks reset it. Playback generations and microphone handoff remain in use.
  Queue overflow reports an error; history opening does not trigger speech.
- Updated Voice/Speech UI text, added the live-voice guide and maintainer context,
  and synchronized GUI version/lock metadata. Installers/dependencies need no
  change for this feature. Earlier canceled setup/wake drafts remain separate;
  an isolated feature patch is provided to avoid committing them accidentally.
- Verification: pure text assembly tests, real Qt fake-engine streaming tests,
  provisional-before-final local/online worker fixtures and actual composer
  revision/cancellation/edit tests passed. The feature-only patch over clean HEAD passed 140 root tests discovered
  (137 passed, 3 Windows-only skips) and 117 Qt/process/QML tests. The current
  working tree also passed 121 Qt tests. Frozen lock and diff checks passed. No live microphone, real online latency test
  or authenticated model request was used; chunk delivery is subject to CPU,
  network and service limits. This does not promise word-by-word audio latency.

## 2026-10-17 — Windows-MCP and Tigo indicator coexistence

- Moved the Windows Tigo screen-control banner to the bottom center of each
  monitor's usable work area, above taskbars, leaving Windows-MCP's top-center
  ownership notice in its own area. The Tigo border is inset past the native
  56-physical-pixel edge glow plus a logical margin, using per-monitor DPI.
  Windows banners wrap text and stack the stop button on narrow displays.
- Refresh active native overlays on monitor geometry, work-area and logical-DPI
  changes. Closed overlays cannot reappear from later geometry notifications.
  X11 keeps its original edge border/top-center banner and Wayland is unchanged.
  No Windows-MCP settings, window stacking, ownership guards, native shortcuts,
  permissions or dependencies were changed. Return control still invokes the
  existing task cancellation path; edges remain input-transparent and windows
  do not request focus.
- Updated [screen-control documentation](docs/screen-control.md). Reviewed the
  upstream native overlay/artwork layout rather than disabling its indicator or
  repeatedly raising windows above it. The installed Windows-MCP version may
  differ from that source; native Windows coexistence still needs a live check.
- Verification: all 11 targeted Qt screen-control/hotkey/IPC tests passed,
  including real widget placement, negative monitor coordinates, 100/150/200%
  scale assumptions, bottom/top/left taskbars, narrow screens, stop callbacks,
  geometry/work-area/DPI refresh and close cleanup. The fix was also tested
  separately over an isolated clean HEAD, without the unfinished wake/setup
  drafts below. A synthetic two-indicator Qt layout preview was rendered and
  visually inspected; it is not a Windows desktop screenshot or a native
  z-order test. Syntax, English-only guide and diff checks pass.
- This fix changes only screen_overlay.py, its screen-control tests, the screen
  guide and this change report. Earlier canceled wake/setup drafts remain
  uncommitted and are not part of this fix; do not use git add -A to publish it.

## 2026-10-17 — Unfinished wake/setup work; user resolved the reported issue

Work stopped after the user reported repairing the issue themselves. The
following working-tree changes are drafts, not a ready release or an installed
repair. They were not committed, pushed or installed on the user's computers.
GUI source/lock version metadata was provisionally changed to 0.13.2; this is not
a published version. Review or explicitly discard these drafts before the next
commit/install; do not present the entire working tree as production-ready.

- Draft wake changes add default-on responsive detection (120 ms speech / 500 ms
  pause, with saved balanced opt-out), a shared two-second cooldown and native
  microphone format negotiation/conversion using existing PyAV. GUI dictation
  uses the same native-rate/stereo conversion. Missing wake audio callbacks
  produce an error. Added root/Qt audio, sensitivity and cooldown fixtures;
  updated Windows, wake, dictation and maintainer notes. Existing dependency
  manifests already include PyAV; no new dependency was installed.
- Wake-stage verification before setup work: 144 root tests discovered, 141
  passed and 3 Windows-only tests skipped; 115 Qt/process/QML tests passed.
  Real PyAV conversion was checked at 44.1/48 kHz mono/stereo with synthetic
  audio; local/online worker routing used simulated transcription services.
  No Windows microphone or user audio was captured. These results predate the
  additional setup drafts and are not validation of the final combined tree.
- Unfinished setup drafts add an install-state helper, live-owner checks, a
  version/path/commit receipt, canonical per-checkout GUI environments, Windows
  shortcut readback, downloaded-bootstrap cache avoidance and rejection of local
  commits ahead of fetched main. Root entry points, Linux/Windows GUI installers,
  launchers and full updaters were edited. Installer fixture adaptation, Update
  Center bundle compatibility, complete documentation and final combined checks
  were not completed. Default recognition-model preloading was discussed but
  has not been implemented. Do not claim it is present.
- Basic Bash/Python syntax and diff checks were run during setup editing; the
  modified setup paths have not passed complete isolated fixtures or native
  Windows validation. No system packages, startup entries, permissions, login,
  user settings or installed application were changed by this draft work.

## 2026-10-17 — Discover desktop MCP before denying browser access

- Updated the Tigo desktop Skill and managed AGENTS rules to inspect current and
  available deferred tools before claiming browser/computer control is missing.
  Browser integration, desktop MCP and shell PATH are independent: a missing
  browser connection or hypruse executable is not evidence that desktop MCP is
  absent. A suitable advertised read-only inventory precedes GUI actions;
  missing/disconnected integrations can use the authorized desktop route.
- Kept authentication, confinement, lock and human ownership refusals as stopping
  conditions. The discovery fallback cannot bypass these guards. Instructions
  require reporting actual tool evidence, distinguish opening a URL from viewing
  its images, and avoid substituting a link for a requested reversible GUI action.
- Updated the Skill discovery description, MCP/Skills guide and AI-maintainer
  context. Existing installers already deploy both instruction files; no runtime,
  dependency, launcher or permission change is needed. Applied the instructions
  to the local installed Skill and managed AGENTS with backups, preserving
  personal instructions. No confirmed-fix memory database was changed.
- Verification: Skill quick_validate passed; all 17 existing managed-instruction /
  X11 regression tests passed, including managed-block replacement, preservation,
  backup and idempotence fixtures. Installed Skill bytes and managed blocks were
  checked against the repository; English-only docs/scripts and diff checks pass.
  This instruction change is not a new model-behavior benchmark or proof of
  browser availability on every installation. Start a new Tigo conversation to
  load the revised instructions; no real browser action was requested/tested.

## 2026-10-17 — Short/quiet wake-name repair and diagnostics (GUI 0.13.1)

- Reproduced the common local/online failure before transcription: the fixed
  0.01 RMS gate discarded four quiet synthetic name samples entirely. Replaced
  it with the existing WebRTC VAD in 20 ms frames, a 160 ms speech minimum,
  660 ms ending pause, four-second cap and 240 ms pre-roll/cap overlap. Capture
  blocks are re-framed without losing partial frames. Separate short clicks do
  not accumulate into a qualifying phrase.
- Added bounded gain for speech-qualified PCM before either provider (maximum
  12x, peak-limited). Silence stays unchanged; existing queues, confidence
  checks, pause generations and eight-second wake cooldown remain in place.
- Exact names now handle mixed Latin/Cyrillic name letters emitted by ASR.
  Tolerant matching adds observed Tido/Tiga substitutions and Russian equivalents;
  no arbitrary edit-distance match is used. Similar ordinary words/substrings
  remain rejected. Tolerant variants can still cause false activations.
- Preferences > Wake now shows input level, speech activity, phrase count and
  content-free match/unclear results. Meter events are throttled to four per
  second and use a separate Qt notification signal. Pausing clears the meter;
  restart resets counters. Ordinary transcripts/audio are not exposed or saved.
  Invalid diagnostic payloads and diagnostics received while paused are ignored.
- Both voice dependency preflight checks now include the already locked
  webrtcvad import. No new package/model/system dependency was added; existing
  one-step installers, platform updaters and Update Center already install/check
  the voice extra. Updated version metadata/lock to 0.13.1, the installation and
  wake guides and readmeai. Existing settings/login/provider choices are retained.
- Verification: 137 root tests discovered, 134 passed and 3 Windows-only tests
  skipped; 111 Qt/process/QML tests passed, including new owned-process diagnostic
  validation. Relevant final wake tests also passed after matcher refinements.
  Existing isolated installer/update fixtures are included in the root suite.
  Production QML diagnostic preview was rendered and visually inspected without
  opening a microphone or contacting a transcription service.
- Real CPU WebRTC/Whisper checks used four synthetic Russian/English male/female
  name samples at normal and 0.03 gain. On the same four quiet samples, old/new
  capture produced 0/4 versus 4/4 phrases. Final small/ru tolerant recognition
  matched 8/8 positive cases; two ordinary-speech and three silence/noise/tone
  controls produced no wake. This small synthetic check is not an accuracy
  guarantee: base still misrecognized one synthetic name; other voices/noise may
  fail. Online normalization/dispatch was tested with a simulated service, not a
  live Google accuracy test. No user audio was recorded, Windows microphone tested
  or system package installed. The separately installed running app requires the
  normal update followed by Quit/relaunch to load the fix.

## 2026-10-17 — Wake transcription, hidden startup and hands-free voice (GUI 0.13.0)

- Recorded the user's explicitly deferred Claude Code / Antigravity / direct API
  provider plan in [roadmap](docs/roadmap.md), linked from README/readmeai. It is
  not implemented or permission to start that work during unrelated changes.
- Added an independent Local Whisper / Online Google Web Speech wake provider.
  Online uses the existing keyless HTTPS adapter with a selected language and
  bounded phrase queues; it does not load Whisper. Short wake phrases are padded
  to the existing adapter's one-second minimum input size. Nearby speech phrases, including those
  without the wake name, are uploaded only when online listening is explicitly
  enabled; UI/docs explain this. Ordinary transcripts remain discarded, with
  only wake/status IPC. Unintelligible speech is ignored; network/service errors
  stop listening. Pause generations discard late recognition/errors.
- Retained and clarified listener-only login startup: the owned per-user XDG
  entry / Windows HKCU Run uses --background. Startup no longer shows a minimized
  main window without a tray, or opens the window on listener errors. Normal
  launch/wake restores the existing instance. Minimal compositors still need
  XDG autostart support; no global desktop or login-screen service was added.
- Added separately saved Start recording a request after Tigo wakes. Opening
  the window precedes dictation start on the next event-loop tick. Existing
  pause acknowledgment/generation handling releases the wake microphone before
  recording. Listening now pauses during active tasks and shutdown as well as
  dictation/spoken output. Say Tigo, wait for the recording indicator, then speak;
  command audio before recording starts is not recovered from the wake phrase.
- Added an explicit, default-off Send voice requests automatically after a
  speech pause setting in Voice/Wake (saves immediately, shared by all dictation).
  Local WebRTC VAD processes 20 ms frames with 1.2/1.6/2.4/3.2-second pause choices;
  default 1.6 seconds. Eight seconds without detected speech cancels before
  dictation transcription/upload. Recording remains bounded to 60 seconds.
  Only a speech-ending pause can auto-submit via the existing normal Send path,
  once and after worker idle. Manual Stop, duration cap, existing/edited draft,
  attachments, cancellation, incomplete worker exit or invalid task state retain
  review behavior. Late results never submit after cancellation. These are
  opt-ins, not speaker identification or a promise against background voices.
- Locked webrtcvad-wheels 2.0.14.post1 in the voice extra (other existing locked
  versions retained). Updated Windows/Linux updater imports and installation,
  voice, startup, desktop, README and AI-maintainer guides. Root setup scripts
  and Update Center continue through the updated installers, preserving user
  settings/login; no new API key, audio driver or system service is needed.
- Verification: 132 root tests discovered, 129 passed and 3 Windows-only tests
  skipped; 110 Qt/process/QML tests passed. New coverage includes VAD framing,
  pauses/no-speech, online wake privacy/late-error generations, real owned-worker
  wake-to-record-to-single-request flow against a fixture app-server, opt-out /
  manual-stop / duration-cap review, draft edits/attachments, cancellation,
  incomplete worker exit, production QML settings and actual --background app
  startup with simulated wake error/no tray. Startup tests isolate registry/files,
  IPC and the unrelated overlay. Existing installer/update fixtures pass.
- A real native WebRTC detector recognized speech then the configured pause in
  synthetic Russian audio and rejected silence; no microphone was opened for
  that check. Production QML wake preview/smoke, Python/Bash syntax, frozen lock,
  English-only managed docs and local links pass. No live system-login event,
  Windows hardware/tray test, microphone/name accuracy benchmark, authenticated
  model task or system-package installation is claimed. New automatic-record/send settings remain
  off until configured; target-machine startup/audio verification is still needed.

## 2026-10-17 — Semantic interface targeting and keyless dictation (GUI 0.12.0)

- Added native-X11 `ui_elements` / `click_ui` tools backed by a bounded AT-SPI
  helper running in system Python. Queries are scoped to current PID/window
  title; action selection checks exact names/roles, ambiguity, path, focus and
  enabled/sensitive/showing state. Native click/press/activate actions do not
  guess coordinates, retry failed actions or enable read-only input grants.
  Incomplete or unsupported trees require a current scoped visual observation.
- Updated shipped AGENTS/Skill routing to prefer interface structure for named
  controls: existing Hypruse ui/click_ui, existing Windows-MCP UIA Snapshot
  without vision when supported, and new X11 tools. Windows input still uses
  the installed tool schema/guards; no second input backend was introduced.
  Runtime diagnostics report semantic tools actually advertised by MCPs;
  availability does not claim app accessibility or desktop ownership. Checked
  workflows can use ui_elements as a read-only condition.
- Added saved Local Whisper / Online Google Web Speech provider choice in
  Preferences > Voice. Online uses SpeechRecognition's public personal-use
  service configuration, explicit HTTPS, bounded in-memory PCM/FLAC/response,
  selected language and one request per completed recording. No personal API
  key/account, online preview, automatic retry/fallback upload or task submission.
  Errors are redacted; cancellation closes the owned worker and rejects late
  results. Wake listening and CLI dictation remain local. The public online
  service can be limited/unavailable and is not a Google Cloud API guarantee.
- New GUI settings default to local small for speech quality; existing model,
  language, output-voice, login and permission choices are preserved. Both
  providers reuse the worker, microphone selection and review-before-Send flow.
  Online mode does not load Whisper. Auto detect/preview/CUDA/beam controls are
  local-only; online selection exposes the language and audio-upload notice.
- Locked SpeechRecognition 3.17.0 in the voice extra, with Python >=3.13 audioop/
  aifc/chunk compatibility dependencies. Existing locked dependency versions
  remain. Updated Linux AT-SPI/GI packages, X11 helper/legacy-path installation,
  Windows/Linux updater import checks, CI syntax coverage, platform/setup/voice
  guides and readmeai. Root one-step setup and Update Center keep using the
  updated platform scripts; no extra API credentials or PyAudio are required.
- Verification: 123 root tests discovered, 120 passed and 3 Windows-only tests
  skipped; 102 Qt/process/QML tests passed after settling initial QML control
  synchronization in an existing test. New tests cover ambiguity/stale state,
  disabled/read-only controls, selected-window helper requests, HTTPS/error/
  redirect/size handling, cancellation without upload, worker reuse, provider
  persistence and production QML language/privacy controls. Isolated installer
  fixtures check new packages and helper copy; Bash/Python/Skill/lock checks pass.
- Live speech check: one synthetic Russian demo was recognized by the real
  Google HTTPS service without personal credentials, and by cached local small
  with HF_HUB_OFFLINE=1/local_files_only. Both returned text; proper-name errors
  remain, so this is not an accuracy or general performance benchmark. An
  attempted private-D-Bus/offscreen AT-SPI fixture could not export its GUI tree;
  native X11 and Windows hardware/input behavior remain unverified. No live
  desktop speedup, microphone hardware test, system-package installation or
  public CI result is claimed. Preview uses isolated production QML settings.

## 2026-10-17 — Update Center, simpler setup and quiet GUI motion (GUI 0.11.0)

- Added [Update Center](docs/updates.md) in the sidebar and Ctrl+U: running/main
  version, new commits, recent plain-text change reports, compare link and last
  installer result. Checks use an owned bounded worker, validate official origin,
  root/main/clean working tree and fetch Git objects without changing working
  files. Ahead/diverged histories and network errors remain explicit.
- Update and restart prepares bootstraps from the reviewed Git commit, rechecks
  that revision, opens a native terminal and waits for a readiness/approval
  handshake before closing Tigo. A copied stdlib-only runner outside the venv
  waits for the old process to exit, invokes the pinned dependency-aware setup
  and requests relaunch. Missing terminals, unfinished tasks, drafts or attached
  files prevent shutdown/installation. Failed installers keep their error in the
  terminal; a bounded result record excludes terminal output and credentials.
  No automatic reset, stash, rollback or silent elevation was added.
- Added root [install.sh](install.sh), [install.ps1](install.ps1) and
  [install.cmd](install.cmd), plus a common Linux bootstrap covering supported
  Debian/Ubuntu/Mint, Fedora and openSUSE paths and delegating Arch/CachyOS to
  its existing updater. Added optional official checksum-verified private Node
  22 setup when a compatible Node/npm is absent. The GUI launcher includes this
  private runtime; system Node and unmanaged user links are retained. The
  Windows/CachyOS bootstraps accept a reviewed commit and suppress their own
  launch when the detached runner owns restart. No new pip dependency was added;
  the lock changes only the app version. Updated setup/dependency instructions.
- Added restrained button press/hover/focus effects, popup fades/small scale
  transitions, preference-tab fades, new-message fades and three activity dots.
  These animate item properties, not the static grid or large image mask.
  Preferences > Runtime > Reduce interface motion persists and freezes core
  motion/disables the new effects. Added dismissible notices and compact sidebar
  spacing. Updated history-opening tests to wait for the new enter transition.
- Recorded the install-script/Update Center maintenance requirement in
  [AGENTS.md](AGENTS.md) and maintainer context, and extended CI syntax/policy
  checks to the root setup scripts. Added a synthetic screenshot of the actual
  Update Center; its future-version values are explicitly illustrative.
- Verification: root suite discovered 107 tests, 104 passed and three
  Windows-only tests skipped; all 97 Qt/process/QML tests passed. New fixtures
  use real local Git histories (dirty/current/ahead/diverged/changed remote),
  real detached runners with harmless installers and parent processes, terminal
  readiness/approval, cancellation, draft/motion/UI guards, package dispatch,
  a dependency-aware Debian fixture and valid/invalid Node checksums. Frozen
  lock, Bash/Python syntax, local links, English docs/scripts, whitespace and
  production-window smoke checks passed. No live package-manager installation,
  authenticated model request or new CI run was performed; Windows hardware
  and real distro package availability were not established by these fixtures.
- Started the installed 0.11.0 GUI on Linux/Hyprland and opened its actual Update
  Center with Ctrl+U. A later Check for updates pointer action was refused by the
  shared-seat guard after focus/cursor changed; no guard was bypassed. The
  check/install logic was exercised in isolated fixtures instead of modifying
  this uncommitted development checkout or launching a real system upgrade.

## 2026-10-16 — Screen activity frame and human task takeover (GUI 0.10.0)

- Added a cyan/violet screen-edge frame, nonactivating banner and Return control
  button for recognized desktop MCP calls from the GUI and saved workflows.
  Concurrent calls are tracked by ID with a short gap-hiding tail. Ordinary
  messages/shell/file work and ControlStatus do not imply screen ownership.
  Stale/foreign turn events are filtered by the existing backend scope checks.
- Added Ctrl+Alt+Shift+F10 emergency cancellation through Windows RegisterHotKey
  or a temporary Hyprland binding. Conflicting user bindings are retained, and
  unavailable shortcuts are not advertised. Same-user, fixed-message local IPC
  requests cancellation without starting a second GUI or a task. Return control
  cancels workflows, closes the owned app-server process tree, stops speech and
  clears the frame; tasks do not automatically resume or undo completed actions.
- Hyprland/layer-shell uses a separate system-Python GTK4 helper with four thin
  edge surfaces and a banner on each monitor/workspace. It takes no keyboard
  focus and destroys its surfaces on parent-pipe EOF. Windows/X11 use Qt tool
  windows with input-transparent edges. Existing Windows-MCP/Hypruse ownership,
  physical-input takeover, authentication and lock-screen guards are preserved.
  No full-screen input lock or input-suppression hooks were added. Windows text
  also names the native Ctrl+Alt+Shift+Backspace escape for its ownership gate.
- Added GTK4, gtk4-layer-shell and PyGObject distribution prerequisites to the
  CachyOS bootstrap and Arch installation recipe, plus a normal-installer check
  and [installation guidance](docs/install-desktop.md#screen-activity-indicator-prerequisites).
  No pip dependency changed; the frozen lock changes only the app version.
  Updated README, Windows guide and maintainer context; added
  [screen-control documentation](docs/screen-control.md) including capture,
  unsupported-compositor, external-process and native Windows escape limitations.
- Verification: 90 Qt/process/QML tests passed, including real fake-worker
  termination, scoped activity, overlap/tail cleanup, nonexclusive widgets,
  same-user IPC, mocked Windows hotkey dispatch and binding conflict/cleanup.
  Root suite: 93 tests discovered, 90 passed and three Windows-only skips.
  Installer/bootstrap fixtures passed. A real GTK4 layer-shell preview appeared
  above another Hyprland workspace; clicking Return control cleared every
  surface and ended the simulated task. This preview did not execute a model
  request or desktop automation. Windows hardware, multiple physical monitors
  and native global-key presses were not tested.
- Python/Bash syntax, frozen-lock consistency, local Markdown links, English
  docs/scripts policy, whitespace checks and the production-window smoke test
  passed. No authenticated model request, package-manager install or CI run was
  needed for these checks; the local GTK prerequisites were already available.
- The main installed GUI was not restarted: the shared-seat guard refused a
  pointer action after cursor/focus changed. No guard was bypassed. Quit Tigo
  and relaunch normally to load this version and register its shortcut.

## 2026-10-16 — Smoother core animation

- Replaced the 20/30 Hz timer in [Orb.qml](gui/tigo_gui/ui/Orb.qml) with Qt
  FrameAnimation. Motion and microphone smoothing now use elapsed frame time,
  speed changes ease over 420 ms, and long stalls have a bounded time step.
  Removed the 360-degree phase reset that snapped fractionally rotated artwork
  and filament bands back to different orientations.
- Cached the original woven-light artwork and radial mask in a small retained
  Canvas, transformed for rotation/breathing. The static dial is cached
  separately with batched tick paths; only the procedural overlay repaints on
  animation frames. Preserved all runtime/audio state effects, the original
  asset and software-renderer support. Hidden, minimized and stopped animation
  pauses, including windows hidden to the tray.
- Updated the [core guide](docs/desktop-app.md#animated-activity-core) and
  maintainer context. No new dependencies or installation steps are required.
- Verification: all 81 Qt/process/QML tests passed, including three new core
  regressions for continuous rotation, frame-rate-independent audio smoothing,
  cached-layer reuse, effect rendering and pause/resume. In an isolated visible
  Linux/Hyprland OpenGL window with a 360-pixel core and synthetic Acting state,
  measured overlay paints increased from about 30 to 165 per second; median
  paint gap fell from 33.08 to 6.06 ms (95th percentile 34.17 to 6.24 ms).
  Matching offscreen software checks increased from about 30 to 62 paints/sec.
  These short renderer checks exclude model/voice work and do not establish
  full-application, Windows or under-load frame rates. The user's reported
  apparent 5 FPS was not reproduced in this isolated baseline.
- The installed application's automatic restart was stopped by the shared-seat
  guard after focus/cursor changed. Its existing process has not loaded this
  patch; a normal Quit Tigo and relaunch is needed. No guard was bypassed.

## 2026-10-16 — Persistent change-report and installation documentation rules

- Added [AGENTS.md](AGENTS.md) to require a dated report for every implemented
  change and installation documentation updates whenever dependencies change.
  Mirrored the requirement in [maintainer context](readmeai.md).
- Made the 0.9.0 speech dependency changes explicit in the
  [installation instructions](docs/install-desktop.md#spoken-replies): edge-tts,
  PyAV, installer/update steps, Internet requirements and female model downloads.
- Verification: checked the edited local Markdown links, dependency requirements
  against `gui/pyproject.toml`, and `git diff --check`. Documentation only;
  application behavior and dependencies are unchanged by this entry.

## 2026-10-16 — Male/female local and online voices (GUI 0.9.0)

- Added local Russian Irina and English Lessac High female voices, with pinned
  official archive size/SHA-256, retained model cards and existing verified
  cache reuse. Dmitri, Denis and Joe remain compatible. Automatic male/female
  selects a voice for Russian/English; explicit voices remain available.
- Added explicit Online neural mode through locked edge-tts 7.3.1 and PyAV.
  The curated Microsoft catalog offers Andrew/Brian Multilingual for Russian
  male output, Svetlana for Russian female, Guy/Aria for English. Live probes
  of native Dmitry repeatedly returned no audio despite its being listed, so
  it is not offered as a working voice. Service changes/errors remain possible.
- Online speech sends only the cleaned speaking copy to Microsoft, in bounded
  requests/MP3/decoded PCM, with a small prefetch queue and in-memory playback.
  Short sentences are grouped into bounded phrases for continuous prosody.
  It never activates as a fallback from local mode, retries or replays audio.
  The existing owned-process cancellation, stale-event guards, wake pause,
  recording handoff and quiet-tail behavior are reused. Local stays the default.
- Saved voice choices are separate for each mode; auto off, chosen local voice,
  rate and volume survive upgrades. Natural neural pitch is retained. Updated
  Speech settings with male/female labels, privacy text, reachable preview/stop
  controls and both local/online screenshots. Fixed female-Automatic preview
  language and Russian pronunciation of Tigo without modifying displayed chat.
- Updated frozen extras, bootstrap import checks, public/security/speech guides,
  provenance and maintainer context. Existing dependency versions are retained;
  new online dependencies are locked. Voice models and generated user-facing
  demo audio are not committed as source assets.
- Verification: 93 root tests discovered, 90 passed and three Windows-only skips;
  78 Qt/process/QML tests passed. New fixtures exercise male/female selection,
  per-mode persistence, explicit online privacy/preview controls, bounded fake
  transport, actual MP3 decoding and worker cancellation before mic release.
  Real CPU synthesis produced non-silent Irina/Lessac High audio. All five
  offered online voices returned decodable audio; Russian male/female local and
  online demo WAVs were generated from synthetic text without speakers/mic.
  Speech smoke, Python/Bash syntax, frozen lock, local links, English docs/scripts
  and whitespace checks passed. Windows/audio hardware and subjective quality
  are not established by these fixtures or generated files. No GitHub CI run
  or authenticated model request was made for these tests.
- Restarted the installed Linux application and exercised Online / Automatic
  female / Test voice through the real GUI. The owned online worker completed
  playback and the UI reported Finished speaking. The existing wake listener
  paused during the test and returned to listening afterward. This is a Linux
  playback-path check, not a subjective voice-quality or Windows hardware claim.

## 2026-10-16 — Rename the assistant and application to Tigo (GUI 0.8.0)

- Renamed the Qt application, message authors, tray/preferences/wake text,
  monogram and SVG/Windows icons to Tigo. Renamed the Python package to
  `tigo_gui`, distribution to `tigo-desktop-ui`, CLI/GUI/full launchers to
  `tigo`/`tigo-gui`/`tigo-full`, Skill to `tigo-desktop`, managed instructions,
  installer assets, test imports, CI commands and documentation/image paths.
  The frozen dependency versions remain unchanged. Documentation screenshots
  and the animated preview were rendered again from the actual QML with
  isolated synthetic content rather than editing old screenshots.
- Wake recognition now accepts Tigo and its Russian spelling. Explicit
  tolerant aliases and split syllables are supported; arbitrary edit-distance
  matching was removed for this short name to avoid everyday-word triggers.
  The former product name no longer activates the listener. Review-before-send,
  local-only audio processing, cooldown and cancellation behavior are retained.
- Added one-time Qt preference migration, reuse of existing private history,
  absolute clipboard references, repair-memory and verified speech-cache paths,
  old environment-option fallback and existing desktop MCP/workflow IDs.
  Saved restricted access remains shared with CLI; login and desktop grants
  are not replaced. Managed old rules/memory guidance upgrade with a backup;
  owned old launchers forward to Tigo and owned menu/Skill/startup entries move
  to the new identity. Personal/unmanaged files are preserved. See
  [rename compatibility](docs/rename.md) for intentional legacy identifiers.
- Retained real GitHub clone/origin/commit/CI URLs and names of third-party
  projects. The remote repository itself was not renamed or published.
- Verification: 87 root tests discovered, 84 passed and three Windows-only
  tests skipped on Linux; 73 Qt/process/QML tests passed. Fixtures cover
  old/new settings precedence, private data/cache reuse, access persistence,
  managed-marker migration, old launcher backups/startup cleanup, Tigo/Russian
  wake tokens, rejecting the old name and common short-word false positives,
  and production-window title/monogram/message controls. Bash/Python syntax,
  frozen lock, English docs/scripts, local links and whitespace checks passed.
- Installed from this checkout on the user's Linux/Hyprland desktop. Quit the
  old application through its UI, launched the Tigo menu launcher and visually
  verified the new title, monogram and text. The saved model, font, voice/wake
  settings were retained and the new local wake worker is running. Real spoken
  wake accuracy and Windows installation/input were not tested; no authenticated
  model turn, new audio-model download or GitHub CI run was performed.

## 2026-10-16 — Local neural voices replace system speech (GUI 0.7.0)

Implementation: [speech controller](gui/tigo_gui/speech.py),
[worker](gui/tigo_gui/neural_worker.py),
[verified assets](gui/tigo_gui/speech_models.py) and
[update recipes](docs/install-desktop.md).

- Replaced default OS TTS with CPU Piper/VITS through locked sherpa-onnx and
  its native core: Dmitri Neural for Russian, Joe Neural for English, plus Denis
  Neural as another Russian choice. The first launch clears legacy voice IDs
  and resets rate/pitch to natural defaults while preserving Speech off/volume;
  subsequent engine/voice settings persist. No online TTS path was added.
- Added a warm owned worker for downloads, model loading, bounded-phrase
  synthesis and in-memory sounddevice playback. Successful output retains up to
  two models; interruption kills active synthesis/audio. Generation IDs ignore
  late events, and microphone callbacks also wait for worker exit.
- Added pinned-size/SHA-256 downloads from official sherpa-onnx GitHub assets,
  cross-platform cache locks, bounded path-safe extraction, atomic installation
  and interrupted-download replacement. Each voice is about 67 MB compressed;
  default Russian/English downloads total about 134 MB. Cards remain with models.
- Preferences > Speech now offers recommended neural or explicit legacy system
  mode, available neural voices, rate/volume, progress and natural pitch. Updated
  the frozen voice extra and added a smaller speech-only development extra.
- Full CachyOS/Windows updaters preload default voices. Removed Windows SAPI
  probing and Russian speech-capability/UAC installation; its old opt-out switch
  remains an accepted no-op. Ordinary GUI installers download voices on first
  speech use. Updated README, installation/speech docs, provenance notices and
  both AI handovers. GUI/client metadata is 0.7.0.
- Before the user's stop-testing instruction: 72 local Qt/process/QML tests
  passed, including migration, warm reuse, stale events, cancellation, errors,
  asset integrity and traversal/link rejection. Real Dmitri/Joe CPU inference
  produced finite non-silent 22,050 Hz audio. Example 4-second phrases generated
  in about 0.23-0.49 seconds after loading on this cloud CPU; this is not a
  latency guarantee or an audible-quality/hardware check. The lock was refreshed
  and speech dependencies imported successfully.
- The user explicitly chose local speech and asked to run no further tests.
  Later CLI/default-argument hardening, event validation, active-mode guard and
  final docs were not rerun. This publication skips CI. Windows hardware, actual
  speakers and subjective sound quality are left for the user's verification;
  no live installer/package-manager task ran in this cloud.




## 2026-10-16 — Dependency-aware CachyOS and Windows update commands

- Added downloadable `scripts/update-cachyos.sh` and `update-windows.ps1` for
  fresh or existing default/custom checkout paths. They check/install prerequisites,
  retain supported user-selected tools, use uv-managed Python 3.12 and frozen
  voice dependencies, run existing GUI/shared-profile installers, import-check
  Qt/CPU transcription and launch the app. Device login runs only if needed.
- CachyOS installs Qt/X11/Wayland/audio/speech packages through the normal full
  pacman rolling upgrade, and installs missing/unsupported Codex user-locally.
  Windows installs missing Git/Node LTS/uv/Visual C++ runtime via winget, refreshes PATH and reports
  unsupported custom native Codex/old shadowing Node selections. No credentials
  are copied and saved Full Access/MCP settings remain under ordinary installers.
- Windows checks Russian SAPI voices and can install the official Russian TTS
  OS capability through a separate UAC process. Failed/canceled optional voice
  setup warns; Tigo itself never runs elevated. Whisper/MCP package downloads
  can still occur on first use; CUDA/editor SDKs and OS/portal permission dialogs
  are outside the default CPU dependency setup.
- Checkouts are validated for expected origin/root/main and clean state; updates
  use ff-only, with no automatic resets, stash or deletion of user work. Package,
  Git, installer and import failures stop before later launch steps. Added
  guarded HTTPS bootstrap commands and detailed limits to installation docs,
  README and both AI handovers. GUI/runtime version remains 0.6.1.
- Verification: fixture tests cover package/update/installer ordering, paths with
  spaces, existing/missing/unknown-error authentication, dirty/wrong-origin/branch protection,
  package failure, old Node shadowing and Windows-native probe/checkout helpers.
  Local validation passed 77 root tests (three Windows-only skips), new updater
  fixtures, Bash/Python syntax, English docs/scripts, 140 local links/anchors,
  documented Bash syntax, frozen lock and diff checks. The bootstrap targets
  x86-64 desktops. CI now parses every Bash script and exercises Windows helpers without real
  package downloads/UAC. Initial [CI 38869298088](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38869298088)
  passed static/root and both GUI suites but failed the new Windows updater
  fixture step. Extended the existing child-test runner with a bootstrap option
  so its failure traceback appears in the public CI annotation for diagnosis.
  [Diagnostic CI 38869600351](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38869600351)
  confirmed a Windows checkout-root comparison failure from short/long path
  aliases. The updater now checks Git's empty root prefix instead of comparing
  differently normalized directory strings; the existing real-Git/path-spaces
  fixture covers the regression. Native PowerShell 5 error/login probes passed.
  Final [CI 38869795642](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38869795642)
  for [9782c67](https://github.com/ggnomer123s/Codex-jarvis/commit/9782c67) passed
  static/root, Ubuntu desktop and Windows desktop, including both native updater
  fixtures and the shared-profile probe. Public raw updater sources match the
  checked-out files; the Bash download wrapper syntax passed. This result-only
  documentation follow-up skips CI.
  No real pacman, winget, Windows capability install, sign-in or hardware task
  ran in this cloud.

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
  project purpose, Tigo mentor character, app-server/MCP architecture and
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

## 2026-10-15 — Tigo mentor character and local speech (GUI 0.6.0)

- Updated the installed `tigo-desktop` Skill and managed AGENTS instructions:
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
  for the GUI and regular `tigo` command, including sandbox selection across
  restarts. Explicit `tigo-full` aliases still request Full Access in the same
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

- Added original generated artwork in `gui/tigo_gui/ui/energy-core.png`.
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

- Added `gui/tigo_gui/app_server.py`: an owned, persistent local stdio
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
- Added [the source review](docs/related-projects.md) of tigo-codex,
  opencode-tigo, opencode-voice, qwen-audio-agent and stable-tigo, plus earlier
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
