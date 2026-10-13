# JARVIS power-user installation

An optional advanced setup for complex development, media-editing and desktop workflows. It is **separate from regular JARVIS**, uses independent Codex configuration and sign-in, and can access more of the user's files and desktop. It does not provide administrator/root privileges.

## Installation

The desktop app can prepare and enable this same profile through
**Preferences > Access > Full Access**, after typing `ENABLE FULL ACCESS`.
It includes a separate device-login panel and a visible active-mode indicator.
The mode is scoped to the current window and returns to normal after restart.
See [Desktop app Full Access](desktop-app.md#full-access-from-the-gui).
The installers accept an explicit acknowledgement argument for this GUI flow;
ordinary terminal installation still prompts interactively by default.

On Linux, after completing the normal prerequisites:

```bash
git pull --ff-only
bash scripts/install-full-linux.sh
```

On Windows 11, in a non-elevated PowerShell window:

```powershell
git pull --ff-only
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-full-windows.ps1
```

Read the installer output before accepting its one-time confirmation. After installation, sign in once and choose a reasoning profile:

```text
jarvis-full login
jarvis-full fast
jarvis-full normal
jarvis-full deep
jarvis-full status
```

| Launch command | Reasoning effort | Shell/desktop privilege profile |
|---|---|---|
| `jarvis-full` or `jarvis-full normal` | Configured default | Full Access |
| `jarvis-full fast` | `low` | Full Access |
| `jarvis-full deep` | `high` | Full Access |

On supported normal JARVIS installers, `jarvis full fast`, `jarvis full normal`, and `jarvis full deep` are aliases to the **same independently installed full profile**. `jarvis full` selects its default profile.

The new launcher **does not auto-send a startup task**: Codex opens interactively, with the selected reasoning setting and its existing Full Access profile instructions. This removes an unnecessary model turn during startup; it does not guarantee a specific GUI-task execution speed.

## Behavior and limitations

The optional profile turns off Codex's command sandbox and ordinary per-command confirmation prompts. It can manipulate files available to the signed-in user and access existing GUI windows. It also has access to third-party MCP tools. Applications can still deny actions; operating-system authentication, permissions and screen locks are not bypassed.

Use it only on a device and projects you are comfortable delegating to software. Prefer backups or duplicate editing projects, review the tasks and keep a way to interrupt the session. Never make it a system/root administrator.

The agent's Skill still recommends asking before publishing messages, transferring private documents, spending money, permanently deleting important work, manipulating credentials or changing security settings. These textual instructions cannot reliably replace system-enforced permissions.

For a safer alternative, use the regular `jarvis normal` or `jarvis deep` with its sandbox/approval settings. The lower-trust regular launcher remains appropriate for interacting with unknown websites, downloads or chat content.

## Configuration separation

Linux Full Access profile: `~/.local/share/jarvis-codex/full-codex-home`.

Windows Full Access profile: `%LOCALAPPDATA%\jarvis-codex\full-codex-home`.

The separate profile typically requires signing in once independently. Codex discovers the shared desktop Skill from the user location `~/.agents/skills/jarvis-desktop` (or the Windows equivalent), not from a private `CODEX_HOME/skills` directory.

## Keyboard shortcuts

Hyprland uses Hypruse `keyboard` for application shortcuts (e.g. Ctrl+S) and `use_bind` for compositor shortcuts, after inspecting `binds`. X11 supports targeted `key` actions with an optional window ID. Windows uses its GUI MCP's keyboard tools. See [GUI navigation](gui-navigation.md).

## Safety reminder

An unrestricted agent can make unintended changes to data or settings. The project doesn't claim the separate profile is safe for confidential accounts. There is no built-in undo for arbitrary shell or GUI operations, and neither a Skill nor a prompt is a replacement for real security controls.
