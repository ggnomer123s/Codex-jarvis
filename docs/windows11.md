# Windows 11 installation guide

This guide configures **Codex CLI + Windows-MCP + JARVIS Skill + one-command launcher** on native Windows 11. It does **not** use WSL, Hypruse, or Linux display protocols.

> Windows support is currently **not hardware-tested by this repository**. It integrates the independently maintained [Windows-MCP](https://github.com/CursorTouch/Windows-MCP). Check upstream compatibility and permissions.

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

JARVIS uses `jarvis.cmd` to avoid this common problem.

## 3. Install JARVIS

~~~powershell
git clone https://github.com/ggnomer123s/Codex-jarvis.git
cd Codex-jarvis
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
~~~

The `ExecutionPolicy Bypass` flag applies to this one **child PowerShell process**; it does not permanently change the machine's policy. Inspect the script before executing.

The installer:
1. Preserves an existing `windows-mcp` Codex registration. If none exists, it registers [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) using `uvx windows-mcp serve`, excluding the extra `PowerShell`, `Registry`, `Process`, `FileSystem` and `Clipboard` MCP tool categories.
2. Installs `%USERPROFILE%\.local\bin\jarvis.cmd` and `jarvis.ps1`, adding the directory to the user PATH.
3. Adds desktop safety instructions to `%USERPROFILE%\.codex\AGENTS.md`, backing up any previously existing instructions.
4. Copies `skills/jarvis-desktop/SKILL.md` to `%USERPROFILE%\.agents\skills\jarvis-desktop`.
5. Leaves background monitoring **disabled** by default.

**Close and reopen PowerShell**. Launch:

~~~powershell
jarvis
~~~

## 4. Verify MCP, Skill and GUI

~~~powershell
codex.cmd mcp list
codex.cmd mcp get windows-mcp
jarvis status
~~~

Start `jarvis` and ask:

> Discover installed GUI MCP tools. Identify the active window and take a screenshot without making changes.

After verifying the capability, use a harmless test:

> Use Windows-MCP to open Notepad, type JARVIS_ONLINE, verify the text with another screenshot, and do not save files or change settings.

Screenshot access and input tools may be restricted by Windows desktop, security or session permissions. Review the actual tool list rather than assuming that registration equals success.

## 5. Optional Windows Application Error monitoring

This is **not** full screen monitoring, malware detection or a general auto-repair system. It queries recent **Application Error** Windows events and may send the event text to Codex for read-only diagnostic reports. Logs can contain private information.

To explicitly enable the monitoring Scheduled Task, rerun the installer from your cloned project directory:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1 -EnableMonitor
~~~

The task `JARVIS-Codex-Watch` polls roughly every five minutes. Reports are written to `%LOCALAPPDATA%\jarvis-codex\reports`.

~~~powershell
jarvis reports
jarvis monitor off
jarvis monitor on
~~~

Managed/corporate PCs may prevent creation of user tasks; normal GUI assistance does not depend on the monitor.

## 6. Troubleshooting

**`jarvis` is not recognized**: open a new PowerShell window. Verify `%USERPROFILE%\.local\bin\jarvis.cmd` exists and that directory is on the user PATH.

**`codex.ps1` is blocked**: use `codex.cmd`. Do not globally set the PowerShell Execution Policy to `Unrestricted`.

**MCP server disconnects**: inspect `codex.cmd mcp get windows-mcp`, verify `uvx --version`, and check upstream Windows-MCP requirements. Python installation and environment paths may be required by the upstream project.

**MCP registered but cannot click**: check permissions, tool exclusions and Windows UI Automation support. Do not disable Windows Defender or User Account Control (UAC) to bypass the problem.

**Skill missing**: start a new Codex session, inspect `%USERPROFILE%\.agents\skills\jarvis-desktop\SKILL.md` and `/skills`.

**Emergency stop**: Ctrl+C or `/exit` in Codex. Windows-MCP is a local stdio process launched by Codex, not a network daemon.

## 7. Security notes

- Do not run JARVIS as Administrator.
- The shell's `read-only` sandbox **does not block all GUI actions** through MCP.
- A screen capture may contain confidential material; hide private windows before the test.
- Obtain human confirmation before state-changing input, upgrades, process termination or file edits.
- Avoid pasting Windows event logs into public GitHub issues without removing secrets.

Further reading: [MCP & Skills](mcp-and-skills.md) · [Usage](usage.md) · [Security](security.md) · [Upstream Windows-MCP](https://github.com/CursorTouch/Windows-MCP).
