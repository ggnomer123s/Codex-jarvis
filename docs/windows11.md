# Windows 11 installation guide

This guide configures **Codex CLI + Windows-MCP + Tigo Skill + one-command launcher** on native Windows 11. It does **not** use WSL, Hypruse, or Linux display protocols.

> Windows support is currently **not hardware-tested by this repository**. It integrates the independently maintained [Windows-MCP](https://github.com/CursorTouch/Windows-MCP). Check upstream compatibility and permissions.

The GUI also provides a screen-activity banner with a Return control button and
its own task-stop shortcut. Windows-MCP retains its native ownership indicator
and takeover shortcut; see [screen control](screen-control.md#windows-11-ownership-remains-with-windows-mcp).

## 1. Prepare Windows Terminal / PowerShell

Open a normal, non-administrator PowerShell window. Install Microsoft App Installer if WinGet is unavailable.

Install required tools:

~~~powershell
winget install -e --id Git.Git
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id astral-sh.uv
~~~

**Close and reopen PowerShell** so the PATH is refreshed.

Verify:

~~~powershell
git --version
node --version
npm.cmd --version
uvx --version
~~~

If any command is missing, check its official installation instructions and the PATH environment variable.

## 2. Install and sign in to Codex CLI

~~~powershell
npm.cmd install -g @openai/codex
codex.cmd --version
codex.cmd
~~~

Follow the authentication flow offered by Codex. Supported ChatGPT sign-in can be used without manually creating a separate OpenAI API key.

### Windows PowerShell: blocked codex.ps1

If invoking `codex` produces an error like `codex.ps1 cannot be loaded because running scripts is disabled`, use **`codex.cmd`**. You do **not** need to globally weaken PowerShell Execution Policy.

Tigo uses `tigo.cmd` to avoid this common problem.

## 3. Install Tigo

~~~powershell
git clone https://github.com/ggnomer123s/Codex-jarvis.git Tigo
cd Tigo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
~~~

The `ExecutionPolicy Bypass` flag applies to this one **child PowerShell process**; it does not permanently change the machine's policy. Inspect the script before executing.

The installer:
1. Preserves an existing `windows-mcp` Codex registration. If none exists, it registers [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) using `uvx windows-mcp serve` with its available tool surface. An expected missing-server response does not stop Windows PowerShell 5 installation.
2. Installs `%USERPROFILE%\.local\bin\tigo.cmd` and `tigo.ps1`, adding the directory to the user PATH.
3. Adds desktop safety instructions to `CODEX_HOME\AGENTS.md` (default `%USERPROFILE%\.codex\AGENTS.md`), backing up any previously existing instructions.
4. Copies `skills/tigo-desktop/SKILL.md` to `%USERPROFILE%\.agents\skills\tigo-desktop`.
5. Leaves background monitoring **disabled** by default.

GUI and CLI reuse the same `CODEX_HOME` or `%USERPROFILE%\.codex`, existing
login and MCP settings. No separate Full Access profile is created. Full Access
defaults on; disable it in GUI Preferences > Access to save a sandbox mode for
both the GUI and regular CLI. Old `install-full-windows.ps1` is a compatibility
entry point for the same installer.

**Close and reopen PowerShell**. Launch:

~~~powershell
tigo
~~~

## 4. Voice and confirmed-fix memory

After installation, run `tigo voice` in a new PowerShell window. Press Enter to start recording and again to stop; faster-whisper runs locally and shows the recognized text. Review it, then type YES to send the transcript to a Codex interactive session. The first use downloads Python packages and a Whisper model. On Windows, allow microphone access for desktop apps if necessary.

`tigo memory add` saves a user-confirmed fix to a private JSON file only after typing YES. `tigo memory search <keyword>`, `tigo memory list` and `tigo memory forget <id>` allow search, review and deletion. Notes never automatically sync to GitHub or ChatGPT.

For model settings, supported languages and detailed privacy constraints, see [Memory & Voice](memory-and-voice.md).

## 5. Verify MCP, Skill and GUI

~~~powershell
codex.cmd mcp list
codex.cmd mcp get windows-mcp
tigo status
~~~

Start `tigo` and ask:

> Discover installed GUI MCP tools. Identify the active window and take a screenshot without making changes.

After verifying the capability, use a harmless test:

> Use Windows-MCP to open Notepad, type TIGO_ONLINE, verify the text with another screenshot, and do not save files or change settings.

Screenshot access and input tools may be restricted by Windows desktop, security or session permissions. Review the actual tool list rather than assuming that registration equals success.

## 6. Optional Windows Application Error monitoring

This is **not** full screen monitoring, malware detection or a general auto-repair system. It queries recent **Application Error** Windows events and may send the event text to Codex for read-only diagnostic reports. Logs can contain private information.

To explicitly enable the monitoring Scheduled Task, rerun the installer from your cloned project directory:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1 -EnableMonitor
~~~

The task `TIGO-Codex-Watch` polls roughly every five minutes. Reports are written to `%LOCALAPPDATA%\tigo-codex\reports`.

~~~powershell
tigo reports
tigo monitor off
tigo monitor on
~~~

Managed/corporate PCs may prevent creation of user tasks; normal GUI assistance does not depend on the monitor.

## 7. Troubleshooting

**`tigo` is not recognized**: open a new PowerShell window. Verify `%USERPROFILE%\.local\bin\tigo.cmd` exists and that directory is on the user PATH.

**`codex.ps1` is blocked**: use `codex.cmd`. Do not globally set the PowerShell Execution Policy to `Unrestricted`.

**MCP server disconnects**: inspect `codex.cmd mcp get windows-mcp`, verify `uvx --version`, and check upstream Windows-MCP requirements. Python installation and environment paths may be required by the upstream project.

**"User owns control" / temporary screen-control refusal**: Full Access and
Windows-MCP ownership are separate. Leave physical input idle for the configured
interval (normally 10 seconds), then use **Preferences > Access > Check desktop
control** or `/desktop-status`. The result is a read-only snapshot, not an
automatic lease. See [ownership recovery](full-access.md#windows-desktop-ownership).

**MCP registered but cannot click**: check permissions, tool exclusions and Windows UI Automation support. Do not disable Windows Defender or User Account Control (UAC) to bypass the problem.

**Skill missing**: start a new Codex session, inspect `%USERPROFILE%\.agents\skills\tigo-desktop\SKILL.md` and `/skills`.

**Emergency stop**: Ctrl+C or `/exit` in Codex. Windows-MCP is a local stdio process launched by Codex, not a network daemon.

## 8. Security notes

- Do not run Tigo as Administrator.
- The shell's `read-only` sandbox **does not block all GUI actions** through MCP.
- A screen capture may contain confidential material; hide private windows before the test.
- Carry out authorized tasks; confirm consequential or irreversible actions that were not already authorized.
- Avoid pasting Windows event logs into public GitHub issues without removing secrets.

Further reading: [MCP & Skills](mcp-and-skills.md) · [Usage](usage.md) · [Security](security.md) · [Upstream Windows-MCP](https://github.com/CursorTouch/Windows-MCP).

## Spoken replies in the GUI

Spoken final answers are on by default. Use **Preferences > Speech** to select
an installed Windows voice, change rate/pitch/volume and test it. For Russian,
open **Settings > Time & language > Speech > Add voices**, install Russian and
restart Tigo, then Refresh voices. Choose a voice that appears in Tigo's
list: voices available only to Narrator may not be exposed to Qt's speech
engine. Speech on/off and Stop speech are available directly beside the chat.
See [speech output](speech-output.md) for microphone coordination and limits.


### GUI online and offline dictation

In Preferences > Voice choose Local Whisper or Online Google Web Speech (no API
key). Select Russian or another spoken language for online mode; Auto detect is
local-only. Local models download once and then work offline. Online recordings
are sent to Google over HTTPS and are subject to public-service availability.
The normal Windows updater installs the locked SpeechRecognition dependency.
See [voice input](voice-input.md). Windows desktop targeting uses the existing
Windows-MCP UI Automation `Snapshot`; screenshot recognition remains available
for applications without a useful accessibility tree. Native ownership guards
remain active.


### Listener-only startup and hands-free requests

Preferences > Wake offers Start listener when I sign in (keep window hidden),
Start recording a request after Tigo wakes, and an independent wake provider.
Automatic sending after a locally detected speech pause is a separate saved
checkbox in Wake/Voice. It is off by default; existing/edited drafts and
attachments retain review behavior. Startup uses the current user's owned HKCU
Run entry with --background, never opens/minimizes the main window automatically
and requires no Administrator rights. The normal updater includes the new
webrtcvad-wheels dependency. See [voice activation](voice-activation.md).
