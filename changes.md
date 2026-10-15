# JARVIS change report

This tracked report records implemented changes, their source commits and the
verification actually performed. Add a dated entry for every subsequent change,
including documentation and CI fixes. Keep the newest entry first, link the
relevant commits or files, and distinguish automated checks from live hardware
validation. Do not record user conversations, recordings, credentials or local
machine configuration here. Dates below are report dates; Git history remains
the source of commit timestamps.

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
  documentation links and whitespace checks passed. CI outcome will be recorded
  after publication. Tests also cover Stop/Cancel before microphone handoff.
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
