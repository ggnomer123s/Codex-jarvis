# JARVIS — AI MAINTAINER HANDOFF
_Last reconciled on 2026-10-15; see the newest entry for current behavior._

**JARVIS character and speech update — 2026-10-15 (GUI 0.6.0):** the user
requested a mentor-oriented JARVIS character and spoken answers. The installed
Skill and managed AGENTS block carry the persona; updates require reinstalling
the managed instructions and starting a new conversation. `speech.py` uses local
Qt native engines only, lazily, with auto reading on by default. Read/Stop and
Preferences > Speech expose voices/rate/pitch/volume. Enumerate Qt voices across
all installed locales; automatic matches Russian/English and prefers an adult
male voice if present. Missing Russian is visible, never silently substituted.
Only the current successful final reply is auto-read; opened history, explicit
commentary and failed/canceled turns are silent. No cloud TTS, actor clone or
new model backend is included. Code/URLs are omitted and speech is bounded.
Wake pause acknowledgment precedes playback; a 300 ms cooldown precedes resumed
capture. PTT interrupts speech and waits for quiet, with stale callback guards.
See [speech setup](speech-output.md) and [change report](../changes.md). Automated
adapters/test-plugin checks do not establish physical speaker/microphone quality.
Cross-platform CI outcomes are recorded in the newest change-report entry.

**Conversation workspace update — 2026-10-15 (GUI 0.5.0):** the user explicitly
approved all six proposed GUI conveniences and deferred other model providers.
Main.qml now has a saved SplitView layout/full-chat/core visibility and one
composer below the chat. MessageCard/presentation render inert Markdown and
copyable code; message editing restores a draft for a new manually sent turn.
Attachments support reviewed local files, image previews, clipboard captures,
change detection and native app-server localImage/text inputs. History uses
a private local SQLite database, Unicode search, titles/pins/deletion and local
transcript reopening with scoped next-Send thread resume. This supersedes older
claims that the GUI retains no conversation text: QSettings checkpoints and
metrics remain content-free, but the separate history stores message text and
attachment metadata. Status now exposes phase/time/error/Stop. Existing shared
Codex home, default/saved access, app-server-only transport and wake/voice remain.
See [GUI controls/storage](gui-conveniences.md) and the newest
[change-report entry](../changes.md) for behavior, tests and limits. Local checks
passed 65 root tests (one native Windows skip) and 48 Qt tests. Initial CI
passed static/root and Ubuntu but found Windows clipboard-cache removal did not
match a noncanonical settings path to the resolved attachment path. Cleanup now
resolves both parents, with a noncanonical-path regression. Final
[CI run 38747237298](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38747237298)
for `eb34751` passed static/root and both Ubuntu/Windows desktop jobs. This
result-only follow-up skips CI. Real user-machine model/clipboard/file/desktop
permissions still require target-environment verification.

**Conversation readability update — 2026-10-15 (GUI 0.4.1):** A- / A+ controls
in the right panel header change all message text between 12 and 28 px (default
14), including existing and streamed messages. Backend `conversationFontSize`
has its own notification and saved QSettings value; changing it does not reset
runtime, thread or draft and is available while busy. The actual-window test
checks controls, rendered message fonts, saved size and compact bounds. See
[the desktop guide](desktop-app.md#conversation-text-size) and the newest
[change-report entry](../changes.md) for verification. All 43 local Qt tests
passed; [CI run 38742059923](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38742059923)
for `03ef8fe` passed static/root and both desktop OS jobs. The result-only
follow-up skips CI.

**Shared account/access update — 2026-10-15 (GUI 0.4.0):** the user's latest
request supersedes all older separate-profile, second-login, acknowledgement
and off-by-default Full Access instructions below. GUI, normal CLI and legacy
Full Access aliases now reuse `CODEX_HOME` or the ordinary `~/.codex`. No auth is
copied and existing MCP registrations are retained. Full Access defaults on;
Preferences > Access saves a shared `access-mode` file for GUI and regular CLI.
Explicit `jarvis-full`/`jarvis full` commands still request Full Access. Switching
access restarts the owned app-server and clears its conversation context while
keeping the same Codex account. Old private home directories are left unused.
Installers prepare the ordinary home, and legacy full installers delegate to
those installers. Windows PowerShell 5 treats a missing native MCP probe as an
expected result, so installation continues to registration. New registrations
allow X11 input, omit Hypruse confinement and omit Windows tool exclusions;
pre-existing registrations retain their flags and OS/auth guards remain.
The input composer has editable model and advertised reasoning selectors at
bottom left; settings retain the same controls. Model changes reset the thread,
reasoning changes retain it, and unsupported advertised effort is reset to the
model default. See [full-access.md](full-access.md) and [changes.md](../changes.md).
Local verification passed 62 root tests and 43 Qt tests, with one native Windows
probe skipped locally. Final CI [run 38740007768](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38740007768)
for `0510971` passed static/root, Ubuntu desktop and Windows desktop, including
the Windows PowerShell 5 probe. The result-only follow-up skips CI; real
microphone/desktop permissions remain target-machine checks.

**Voice activation update — 2026-10-15:** the user explicitly requested
continuous local transcription for English/Russian wake-name activation. This
authorizes this feature beyond the earlier declined roadmap; other declined
features and specialized bots remain outside scope. GUI 0.3.0 adds opt-in
`wake.py` (bounded speech segmentation, CPU Whisper, tolerant/exact name matching,
cooldown, pause generations), `wake_control.py` (owned process and acknowledged
manual-mic handoff), `autostart.py` (XDG autostart / HKCU Run), and `activation.py`
(same-user single-instance local IPC). `app.py` manages tray/background/restore;
`Main.qml` has Wake settings and mic status. Ordinary transcripts/audio are
transient RAM, not persisted or sent to Codex; wake opens the window only.
Closing keeps opted-in listening in the tray/minimized, whereas Quit stops it.
Disable stops capture even if startup cleanup fails. Normal mic pause retains
the wake model; a stalled pause kills only that worker, then reloads after manual
voice completes. See [voice-activation.md](voice-activation.md) for limits and
target-machine checks; older "no wake listener" descriptions are superseded.
After a Windows activation-delivery regression, local IPC now waits for an owner
acknowledgement and is tested between real separate processes. Public CI error
annotations include the child exit code and final traceback. Final
[run 38704976904](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38704976904)
for `2496dfe` passed all static/root, Ubuntu and Windows jobs. Local suites passed
60 root plus 44 Qt tests (104 total). Real microphone accuracy, sign-in startup
and native tray/focus behavior remain target-machine checks.

**Activity artwork and scope update — 2026-10-15:** `Orb.qml` replaces the
central J with an original generated `energy-core.png` and procedural Canvas
filaments, particles, audio response and distinct effects for preparation,
thinking, acting, verification, completion, failure and stop. The existing
runtime/voice states drive the art; profile preparation maps to connecting.
Animations pause while minimized and freeze when stopped. `Main.qml` scales
the core with window height so the input remains visible in short windows.
See [the state guide and preview](desktop-app.md#animated-activity-core).
The implementation is `7cd7a76`; [run 38700213462](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38700213462)
passed static/root checks and both desktop OS jobs. Locally, all 13 state inputs,
audio smoothing and pause/resume were rendered in the real QML window; composer
and Send bounds were checked at 1060x760, 1440x760 and 1440x900. No new live
microphone or desktop-automation validation is implied.

The user declined the remaining unimplemented proposals from the earlier
roadmap. Those older sections are historical ideas, not approved work to add.
Multiple specialized bots were discussed as a design option only; this update
does not implement them. A potential design should preserve Codex app-server,
separate role contexts and serialize shared desktop input. Keep that discussion
separate from the implemented single-assistant artwork change.

**Verification/reporting update — 2026-10-15:** existing
[run 38629351827](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38629351827)
for `8abce2e` completed successfully: static checks and both Ubuntu/Windows
desktop jobs passed. The Ubuntu Qt runtime dependency fix is verified in CI.
No additional platform runs were requested for this check. This remains
automated/simulated coverage rather than live desktop or microphone validation.
Maintain [changes.md](../changes.md) for every subsequent modification, recording
files/behavior, verification evidence and unresolved limits. Its initial entries
also backfill the persistent-runtime and preceding GUI/install changes.

**Fresh CI result — 2026-10-15:** after a subsequent request to run both
platforms, [run 38698094096](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38698094096)
for `c9e7b2d` passed all three jobs: static/root checks, Ubuntu desktop and
Windows desktop. Individual process/QML, protocol/simulated-audio and window
smoke-test steps succeeded on both platforms. This supersedes the earlier pause
on additional runs. The result-only documentation update skips another CI run;
hardware-validation limits remain unchanged. See [changes.md](../changes.md).

**Persistent runtime update — 2026-10-14:** the GUI now uses an owned Codex
app-server stdio JSON-RPC process as its only model transport. This supersedes
earlier descriptions of per-message `codex exec`, completed-only chat and
one-shot GUI voice workers. `app_server.py` owns initialization, bounded RPCs,
timeouts, protocol interruption and process cleanup; `messages.py` updates chat
rows incrementally. Profile/access changes close the process and clear runtime
context. Model/profile/workspace-scoped thread pointers support explicit
conversation resume, without replaying actions. Extra approvals are declined
under the existing never policy; the newer shared-access update above supersedes the original separate Full profile.

`voice.py --worker` retains one multilingual model, opens the mic only for an
explicit recording and handles bounded PCM queues outside the audio callback.
The model unloads after five idle minutes. CPU/CUDA, beam, microphone and optional
chunk-preview settings are in the GUI. Preview is energy-pause/chunk processing,
not true online decoding; final text still requires review and manual Send.
`runtime.py` records content-free timing history and checkpoints. `workflows.py`
implements user-saved exact aliases and 1–5 desktop MCP steps with pre/postchecks,
stop-on-refusal and bounded observation retries. X11 now returns structured
active-window identity and offers bounded synchronous window waiting.

The optional local reasoning heuristic adds no classifier model request.
Runtime/Automation tabs, state-driven orb colors, smoothed audio response and
live provisional-text presentation are implemented. See [runtime.md](runtime.md)
and [related-projects.md](related-projects.md) for behavior, checked external
sources and limits. A real Codex CLI 0.159.2 initialize/config-read probe passed
on Linux. Qt/audio/MCP tests use simulated counterparts; authenticated requests,
live Windows, CUDA and desktop workflows still need target-machine validation.
This update implements the earlier warm-worker/profiler proposals; general
task replay, Doctor auto-repair, editor bridges and always-listening voice remain
future work. No measured end-to-end speedup is claimed.

**CI environment fix — 2026-10-14:** the Linux runner lacked `libEGL.so.1`,
which prevented importing Qt even in offscreen tests. The desktop job now
installs its Linux Qt runtime libraries explicitly. Both OS jobs run independently
(`fail-fast: false`), and `scripts/check_desktop_ui.py` publishes fixture-test
failures/crashes as GitHub annotations so failures are visible without API log
access. This is CI observability and environment setup, not live desktop proof.

**Desktop frontend addition — 2026-10-13:** `gui/` now contains a native
PySide6/Qt Quick application for Linux and Windows 11, with an animated JARVIS
core, Codex JSON subprocess chat, session resume, cancellation, workspace and
reasoning preferences, and isolated local push-to-talk transcription. Separate
launch scripts and user-level menu installers are under `scripts/*gui*`.
See [desktop-app.md](desktop-app.md) for the exact workflow and current limits.
The app runs from source with `gui/uv.lock`; signed EXE/AppImage packages are not
provided. The UI is implemented, while live Windows/microphone/authenticated
Codex/desktop-MCP behavior still needs target-machine validation. Codex chat
resume is distinct from the roadmap's task checkpoints.

`docs/install-desktop.md` provides fresh-install and update commands for
Arch/CachyOS, Debian/Ubuntu/Mint, Fedora, openSUSE and Windows 11. README links
each platform directly. These recipes do not establish validation on every OS;
the x86-64 Qt lock requires glibc 2.34+ on Linux.

**GUI preferences update — 2026-10-13:** the desktop app now supports explicit
Full Access enablement through the existing separate-profile installers, device
sign-in, per-window enablement and return to the normal profile. Installation
and login execute in child processes; the normal process environment and
authentication are retained. The GUI also reads safe model IDs from the active
profile's local catalog, accepts custom IDs, and has 15 voice language presets
including Russian plus automatic detection. Whisper size/local folder and
language settings persist. Model/profile changes clear the conversation context.
The dark preferences tabs, status badges and approximately 30 FPS/minimized
animation behavior are implemented. Persistent Codex/Whisper workers, automatic
reasoning selection and Doctor/checkpoints remain proposals. Tests simulate
processes/audio; actual Full Access installation/login and microphone/model
execution still need validation on a target machine.

**Installation/checkbox update — 2026-10-14:** GUI installers now prepare the
included Full Access profile automatically; the GUI enables/disables it with a
single checkbox and no typed acknowledgement. The profile remains separate and
off by default, with independent login and per-window activation. On Windows,
preparation runs in a child PowerShell to retain the parent's normal environment.
The copy-ready installation instructions use explicit checkout paths and
clone/update selection so they work from a user directory, not just a Git root.
Linux installer integration is tested from an unrelated directory containing
spaces with isolated fixture tools; native Windows installation still needs
target-machine validation. This update supersedes the earlier GUI text-entry flow.

> **Start here if you are another AI or a developer continuing this project.** Read this file, `README.md`, and the specific source files you intend to edit. This handoff is a snapshot, not permission to invent past accomplishments or disregard newer code, the user's current request, tests, or security boundaries. **The repository source is authoritative if the handoff becomes stale.**

## 1. Mission and actual product

**Repository:** [ggnomer123s/Codex-jarvis](https://github.com/ggnomer123s/Codex-jarvis); default branch: `main`.

JARVIS is a cross-platform **computer assistant with terminal and native desktop interfaces** built around the **OpenAI Codex CLI**. It connects Codex to the user's desktop through MCP and augments it with reusable agent instructions, local confirmed-repair memory, push-to-talk speech transcription, and optional error monitoring. This is an independently developed community project, **not an official OpenAI product**.

The intended experience: say/type a real computer task, have Codex select the correct **GUI, compositor API, application scripting API, or shell route**, perform the permitted actions, and confirm the result. The goal encompasses **video editing, Linux diagnostics, programming, file management, browser workflows and other demanding tasks**—not merely taking screenshots and pressing buttons.

The original active setup was reported as **CachyOS / Hyprland / fish**, with interest in **Windows 11 and Adobe Premiere Pro** support. This does not mean all platforms have been tested. Do not commit personal data, authentication secrets, screen captures, chat histories or machine-specific configuration.

**Do not misrepresent implementation:** There is no separately trained JARVIS model, no autonomous visual video editor, and no guaranteed always-on background operator. Codex provides the reasoning; the repo provides a desktop frontend, launchers, backends, instructions, and utilities.

## 2. Architecture (as implemented)

```text
                     user: task / optional push-to-talk
                                   |
                                   v
           jarvis / jarvis-full command-line launchers
                                   |
                                   v
                  OpenAI Codex CLI (LLM/planner)
                     |         |          |
              AGENTS.md     Skills       Codex shell/tools
                     |         |          |
                     +---------+----------+
                                   |
                              desktop MCP
           +-----------------------+----------------------+
           |                       |                      |
      Hyprland / Hypruse       Linux X11 MCP       Windows-MCP
           |                 (own Python code)       (upstream)
           +-----------------------+----------------------+
                                   |
                  GUI windows, apps, keyboard, pointer

  Other Wayland -> experimental wayland-mcp-kurojs/desktop portals
  Optional user monitor -> logs -> read-only Codex report (not auto-fix)
  Optional memory -> local confirmed-fixes.json (not automatic memory)
```

Installed **Skills** live under `~/.agents/skills/jarvis-desktop/SKILL.md` (Windows counterpart under `%USERPROFILE%`). The installer synchronizes a **JARVIS-owned block** in `CODEX_HOME/AGENTS.md` (default `~/.codex/AGENTS.md`) from `config/jarvis-agents.md`; it preserves other user text, makes backups, refuses malformed managed markers, and avoids overwriting a symlinked target.

### Platform-specific backend registration

| Platform | Backend / configuration | Actual status |
|---|---|---|
| Hyprland on Wayland | Upstream `uvx hypruse` MCP. On a **new registration**: no confinement filter, `HYPRUSE_STRICT=1`, `HYPRUSE_AUTH_GUARD=strict`, `HYPRUSE_JOURNAL=1`, `HYPRUSE_MARK=0`. | User-reported working desktop, but individual apps may not expose accessibility data. |
| Native Linux X11 | Bundled `scripts/x11_mcp.py` via `uv run --no-project --with mcp python`. `xdotool`, `wmctrl`, `maim`; GUI input enabled on **new registrations**; existing flags retained. | Code/tests implemented; not broadly hardware validated. |
| GNOME/KDE/other Wayland | Upstream `uvx wayland-mcp-kurojs`, `WAYLAND_MCP_NO_PERSIST=1`; actual remote-control permission depends on compositor/portal. | Experimental, potentially observation-only. |
| Windows 11 | Upstream `uvx windows-mcp serve`; new registrations use available tools with no installer exclusions. | Installer implemented; user hardware support still needs verification. |

**Critical behavior:** Installers generally **preserve existing MCP registrations** rather than force-replacing them. Re-running an installer may update the Skill/launcher but **does not necessarily change existing GUI confinement or input permission**. Check `codex mcp get hypruse` / `jarvis status` before making claims. Restart interactive Codex after MCP/Skill changes.

## 3. Commands — source-of-truth: launcher scripts

```sh
jarvis                     # same as fast: Codex low reasoning, interactive
jarvis fast                # low reasoning
jarvis normal              # default reasoning from Codex config/model
jarvis deep                # high reasoning
jarvis full                # explicit unsandboxed mode in the same profile
jarvis full fast           # Full Access, low reasoning
jarvis full normal         # Full Access, default reasoning
jarvis full deep           # Full Access, high reasoning

jarvis-full                # Full Access, default reasoning
jarvis-full fast|normal|deep
jarvis-full login          # sign into the shared CODEX_HOME
jarvis-full status         # shared profile / MCP status
jarvis-full help

jarvis status              # configured backend and watcher
jarvis gui-check           # desktop prerequisites & diagnostics
jarvis reports             # list optional watcher reports
jarvis voice               # one-shot local Whisper transcription; user reviews
jarvis memory add          # opt-in confirmed fix
jarvis memory list
jarvis memory search QUERY
jarvis memory forget ID    # explicit deletion confirmation
jarvis monitor on|off      # installed optional user watcher
jarvis stop                # on Hyprland, stop Hypruse; other OS: guidance
jarvis test                # Linux only: synthetic failed user service
jarvis help

# Hyprland-only, regular Codex profile:
jarvis access status
jarvis access restricted   # HYPRUSE_CONFINE=launched
jarvis access telegram     # class:org.telegram.desktop,kitty
jarvis access allow firefox Spotify   # window classes, case-sensitive
jarvis access all          # remove HYPRUSE_CONFINE; all desktop windows
```

`jarvis access` prompts for `APPLY`, backs up the current `CODEX_HOME/config.toml` (default `~/.codex/config.toml`), replaces the Hypruse MCP registration, keeps strict/authorization/journaling, sets `HYPRUSE_MARK=0`, and optionally asks for `RELOAD` to run `hyprctl reload` to clear old runtime red border rules. The profile helper requires an existing config file and can drop nonstandard MCP flags: **review and improve this before claiming it preserves everything.**

`jarvis full ...` delegates to `jarvis-full ...`, installed alongside `jarvis`.
All commands use the current Codex home/login/MCPs. Regular commands read the
saved GUI access preference (missing means Full Access); the explicit full
aliases always bypass the Codex shell sandbox and ordinary approvals under the
current user account. They do not elevate or bypass OS/auth guards.

Reasoning effort is not a separate model or guaranteed performance target. `low` / `high` are per-launch Codex config overrides; unsupported levels vary by selected model.

## 4. GUI: automatic task routing and gestures

User-requested **visible application tasks** should actually use the GUI MCP when available. The code does not implement a formal separate intent classifier: routing is currently **an instruction in the Skill and managed AGENTS.md**, with discretion exercised by Codex. Shell or native application APIs are better for deterministic batch edits; GUI is appropriate for visual controls and app-specific workflows; complex video editing may require both.

`skills/jarvis-desktop/SKILL.md` is the authoritative behavioral implementation. Current priorities:

1. Identify app/window using semantic window inventory once.
2. Prefer compositor IPC or a native app API, then accessibility tree / named controls; use image grounding only when necessary.
3. If the app is Electron/canvas/Spotify or another tree-poor UI, use **a window screenshot** then `zoom`/crop; don't repeatedly call `ui` when the app has no tree.
4. Convert image positions using capture geometry/scale and support negative multi-monitor coordinates.
5. Batch **short, grounded, reversible** steps via Hypruse `sequence` / action `then='ui'|'desktop'` and use `wait_for` instead of screenshot polling where supported.
6. Verify final state once for trivial navigation; verify meaningful checkpoints for long or consequential editing.

**Two separate rectangle operations:** `pointer drag` changes GUI selection; `screenshot(region=...)` only captures an area. On Hyprland, upstream Hypruse already implements drag and crop. X11 MCP has `drag(x1,y1,x2,y2,button,steps,window_id)`, `screenshot_region(x,y,width,height)`, and `user_select_screenshot()` (human draws screenshot region using maim). X11 drag attempts button release in `finally` even on error. Windows-MCP may offer native `Move(drag=True,...)` / `Screenshot(region=...)`; inspect current MCP schema.

**Shortcuts:** Hypruse `keyboard` for *application shortcuts* (Ctrl+S), and `binds`/`use_bind` or `hypr` for *compositor binds* (Super+...). A synthetic app shortcut need not activate a Hyprland bind. X11 `key(key_sequence, window_id)` checks focus before sending. Never switch to unguarded shell input after a Hypruse refusal.

Read [gui-operator.md](gui-operator.md), [gui-navigation.md](gui-navigation.md), and [shortcuts.md](shortcuts.md) for details.

## 5. The important historical bugs (and current fixes)

1. **Spotify/Firefox out of scope:** the user had `HYPRUSE_CONFINE=class:org.telegram.desktop,kitty`; screenshots worked but clicks/focus on Spotify or Firefox failed with `outside the agent's confinement scope`. The `jarvis access all` helper is an *explicit user-driven* way to change this, not a global default or hidden workaround. Correct GUI window visibility or workspace alone does **not** remove confinement.
2. **Red borders:** `HYPRUSE_MARK=1` tagged agent-opened windows and installed red outlines. Fresh registrations and access helper now use `HYPRUSE_MARK=0`. Previously installed runtime rules may remain until user-approved Hyprland config reload. `docs/security.md` and other older docs may need consistency checks after future changes.
3. **Excessive screenshots / reasoning loops:** Skill was consolidated to prefer semantic UI, window crops, action batching, event waits and appropriate reasoning effort. The GUI now adds actual task/tool/voice timing records, but no measured end-to-end speedup is claimed; instructions alone cannot promise one.
4. **Wrong X11 keyboard focus:** `key(...,window_id=...)` now verifies activated window before typing; refusal is better than typing into a different app.
5. **Limited X11 region capabilities:** added bounded region screenshots, selection drag with interpolated mouse motion/cleanup, interactive human region capture and support for negative monitor coordinates.
6. **Stale AGENTS instructions:** Linux and Windows installers now use `scripts/sync_agents.py` and `config/jarvis-agents.md` to refresh the managed block while preserving custom text with backup.
7. **Full profile Skill misplaced:** fixed to install the shared Skill under `~/.agents/skills/jarvis-desktop`, a recognized Codex location, not an unsupported `CODEX_HOME/skills` folder.
8. **Full modes missing:** separate Linux and Windows launchers now accept `fast|normal|deep` and `login|status|help`; `jarvis full ...` passes those arguments along. They start interactive Codex **without auto-sending a task**.
9. **Deep was only medium:** `jarvis deep` now uses `model_reasoning_effort=high`, as does `jarvis-full deep`.

These are **code changes and test outcomes**, not proof of full end-to-end success on a real Hyprland/Windows installation.

## 6. File map — read the relevant paths before editing

| Path | Role |
|---|---|
| `README.md` | Public overview, install quick starts, commands and AI handoff entry point |
| `changes.md` | Dated implementation and verification report; update for every change |
| `gui/jarvis_gui/` | Qt Quick frontend, owned persistent app-server transport, incremental messages, warm voice, metrics/checkpoints and checked workflows |
| `gui/pyproject.toml`, `gui/uv.lock` | Desktop app and optional voice dependencies, locked for Linux/Windows |
| `scripts/*gui*` | Separate Linux/Windows launchers and current-user application menu installers |
| `gui/tests/`, `tests/test_desktop_*.py` | Protocol, simulated audio, Qt process and actual QML-window tests |
| `docs/desktop-app.md` | Desktop app setup, voice, access modes and test limitations |
| `docs/AI_HANDOFF.md` | This detailed technical history/status/continuation plan |
| `scripts/install-linux.sh` | Installs regular Linux launchers, MCP, Skill, managed rules and optional systemd watcher |
| `scripts/install-windows.ps1` | Regular Windows launcher, Windows-MCP, Skill, managed rules and optional Windows watcher |
| `scripts/install-full-linux.sh` | Compatibility entry point for the shared Linux installer |
| `scripts/install-full-windows.ps1` | Compatibility entry point for the shared Windows installer |
| `scripts/jarvis-full-launcher.sh`, `.ps1` | Explicit Full Access CLI presets in the shared home; **source**, copied by installers |
| `scripts/hypruse-access.sh` | Regular Hyprland confinement profiles and backups |
| `scripts/x11_mcp.py` | Bundled native X11 GUI MCP implementation |
| `skills/jarvis-desktop/SKILL.md` | GUI intent detection, selection, screenshot crops, shortcuts and efficient task execution instructions |
| `config/jarvis-agents.md` | Managed JARVIS agent rules template |
| `scripts/sync_agents.py` | Safe replacement of managed rules in `AGENTS.md` |
| `scripts/jarvis_memory.py` | Local confirmed-fixes JSON memory CLI; user confirms saves/deletions |
| `scripts/jarvis_voice.py` | Microphone push-to-talk, faster-whisper offline transcription |
| `scripts/watch-linux.sh` | Optional read-only systemd user-service incident diagnosis |
| `scripts/watch-windows.ps1` | Optional read-only Windows Application Error diagnosis |
| `docs/*.md` | Installation, backend, security, performance, GUI, voice, memory and shortcuts guides |
| `tests/test_memory.py` | Local confirmed-repair memory tests |
| `tests/test_gui_regressions.py` | Agent-rule sync and X11 focus, drag, region, cleanup tests |
| `tests/test_full_launcher.py` | Fake-Codex CLI tests for Full Access modes, shared home, invalid arguments |
| `.github/workflows/validate.yml` | GitHub Actions static and Python unit-test verification |

**Not in repository:** user config, independent Codex auth, stored memory, logs, user screenshots, project media, secrets or any deployed editor API bridge.

## 7. Install and update safely

### Regular Linux

```bash
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
bash scripts/install-linux.sh
# Open a new shell
jarvis
```

Existing checkout:

```bash
git pull --ff-only
bash scripts/install-linux.sh
```

Full Access is on by default in the shared profile. `install-full-linux.sh`
is a compatibility entry point for the ordinary installer; no acknowledgement
or second login is needed. The GUI installer also prepares this same profile.
Disable Full Access in Preferences > Access to persist a sandbox mode for GUI
and normal CLI. See [the installation guide](install-desktop.md).

### Regular Windows 11

Use native PowerShell, not WSL. Install Git, Node.js, uv and Codex CLI (details in [windows11.md](windows11.md)), then:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
# Compatibility entry point for the same shared-profile installation:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-full-windows.ps1
```

Do not make global execution-policy changes for convenience, run installers elevated or manually copy Codex authentication files between profiles.

## 8. Tests, verification and known limitations

The repository has GitHub Actions to check Bash syntax, PowerShell parsing, Python syntax, unittest discovery, and an English-only rule for repository docs/scripts. As of the handoff date, the latest examined workflow prior to this documentation change was **successful**: [run 38287292897](https://github.com/ggnomer123s/Codex-jarvis/actions/runs/38287292897). **Always check the latest run after making changes**; never cite this historic run as evidence for a future commit.

CI is **not** real desktop validation. Explicitly unverified/partially verified: Windows GUI behaviors, many distros/compositors, video editing inside Premiere Pro, drag accuracy on complex timelines, generic Wayland portal input, full workflow duration, and privacy boundaries of third-party MCP servers.

Some commands may depend on Codex versions, chosen model, installed GUI tools, and local portal permissions. There are **no measured benchmarks proving JARVIS outperforms Microsoft UFO, Agent-S or E2B Desktop**. The existing [gui-operator.md](gui-operator.md) documents architecture inspiration; no competitor code was imported.

## 9. Roadmap — ideas, NOT already implemented

**Priority 1 — real reliability and observability:** The GUI timing/connection
controls now implement the initial profiler scope. Expand measurements and
target-machine coverage rather than treating the older proposal as unimplemented.
- **JARVIS Profiler**: capture real per-tool latency and reasoning/tool-turn counts; compare same end-to-end task before/after tuning. Avoid speculative "x times faster" claims.
- **JARVIS Doctor**: one diagnostic overview of Codex, MCP, Hypruse configuration, desktop session, Skills, dependencies and conflicting installed profiles; provide evidence-first repair guidance.
- **GUI end-to-end tests**: reproducible disposable text editor/browser/window/rectangle tasks with screenshots, timings and an authorization-refusal test. Avoid destructive production tests.
- **Documentation consistency**: ensure README, `docs/security.md`, launcher help and actual new/default MCP env flags all agree. Pay special attention to `HYPRUSE_MARK=0` and pre-existing registrations.

**Priority 2 — complex workflows:**
- **Task Checkpoints**: GUI conversation pointers and completed-step counts are implemented; general action replay and app-specific continuation remain future work.
- **Native editing bridges** (e.g., Premiere UXP where supported, DaVinci scripting, FFmpeg for media transformations). These do not exist yet. Need host OS/editor version and local verification before claiming timeline or render control.
- **Application-specific Skills** for browser, file manager, editor, terminal. Keep them small and testable; avoid flooding Codex context.
- **Adaptive reasoning/auto task router**: an optional local GUI reasoning heuristic and exact checked-workflow aliases are implemented. Broader semantic task classification and app-specific routing remain future work.

**Priority 3 — advanced features:**
- Robust retry after interrupted MCP operations, a deterministic emergency stop, carefully scoped rollback/undo, and safer Full Access usability. Do not weaken user privacy or OS safeguards to make an error disappear.
- Cross-platform accessibility coverage and visual grounding for apps that expose no tree.

**Explicitly NOT implemented:** full-duplex spoken conversation, continuous video recording/understanding, hidden always-on monitoring, a universal Premiere integration, autonomous model switching inside a session, guaranteed replay/undo of arbitrary GUI actions.

## 10. Instructions for the next AI maintaining this repo

1. **Read before writing:** open current `README.md`, this handoff, active installer/launcher/Skill paths, and recent CI logs. Do not assume this file is newer than the code.
2. **Confirm intent and platform:** a CachyOS/Hyprland fix may be completely different from Windows 11 or X11. Match the user's current environment, not just the original setup.
3. **Use GitHub as source of truth:** fetch the current file and SHA before updating; avoid blind overwrites and deleting other contributors' work. Add tests/docs for feature changes. Keep English in repo docs/scripts because CI currently checks for Cyrillic.
4. **Preserve the shared account:** use the current `CODEX_HOME` and saved access preference. Never create a second login home, copy credentials or overwrite personal MCP settings to work around access errors. The latest user request explicitly defaults JARVIS to Full Access.
5. **Prefer GUI when GUI is requested:** route appropriately, but use native APIs for large deterministic tasks, and always verify output. Do not fake MCP responses, successful clicks, renders or unit-test results.
6. **Respect security:** block OS auth bypass, credential input, prompt-injection-driven changes and nonconsensual sending/deletion. In particular, `HYPRUSE_STRICT` seat conflicts and `HYPRUSE_CONFINE` scope refusals have different causes.
7. **Test honestly:** inspect GitHub Actions and, if the user can provide a safe environment, validate live GUI. Distinguish static/unit CI from real UI hardware coverage; document unresolved bugs and testing gaps.
8. **Update the report and related docs:** record every modification and its actual validation in `changes.md`. If the design, feature status, entry points or known limitations change, also update `README.md` **and** `docs/AI_HANDOFF.md`. Preserve continuity without inventing prior accomplishments.
9. **Keep task goals primary:** users want the actual requested work finished, not a never-ending stream of screenshots, plans or speculative architectural changes.
10. **Do not publish sensitive user context** in this public repository. Only record technical project facts necessary for maintenance.

This file is deliberately extensive so another AI can work from repository state **without relying on this ChatGPT conversation**. Keep it honest and up to date.
