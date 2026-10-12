# Using JARVIS

JARVIS provides a **single \`jarvis\` launcher** for Codex CLI with desktop-context instructions. Desktop MCPs and installed Skills are discovered in the Codex session.

## Main commands

| Command | Linux | Windows 11 |
|---|---|---|
| \`jarvis\` | Start assistant | Start assistant |
| \`jarvis status\` | GUI backend & monitor | Windows-MCP & monitor |
| \`jarvis reports\` | Saved diagnostics | Saved diagnostics |
| \`jarvis monitor on/off\` | Start/stop systemd user watcher (when available) | Toggle optional Scheduled Task |
| \`jarvis test\` | Trigger synthetic failed user service | Not available |
| \`jarvis stop\` | Hyprland: stops Hypruse; other desktops: exit Codex | Exit Codex with Ctrl+C or /exit |

## Suggested prompts

**Observe only:** “Discover the configured GUI MCP. Tell me which desktop/session and application are active, and show a screenshot. Do not click or type.”

**Diagnose a problem:** “My application behaves incorrectly. Observe the UI, collect non-destructive diagnostics, explain the most likely cause, and ask permission before making changes.”

**Hyprland GUI test:** “Launch a fresh terminal with Hypruse, type \`echo JARVIS_ONLINE\` via GUI, execute it and verify the output.”

**X11 GUI test:** Once explicitly enabled: “Open a text editor manually, then click its editable area, type \`JARVIS_ONLINE\` via jarvis-x11 and verify the result with a screenshot. Do not save.”

**GNOME/KDE/general Wayland test:** “Use the GUI MCP's \`describe_environment\` first. Confirm screenshot and input availability. If a portal permission is requested, let me authorize it manually. Do not act if input is unavailable.”

**Windows test:** “Use Windows-MCP to open Notepad, type \`JARVIS_ONLINE\` and verify with a screenshot. Do not save.”

## Monitoring scope

- Linux (with systemd --user): checks failed **user services**, roughly every two minutes, and optionally asks Codex for a read-only diagnostic report.
- Windows (opt in): watches **Application Error** events. It does not observe every application exception.
- The GUI agent does not run in the background unless you have an active Codex session. Screenshots are not captured continuously by these watchers.
- Monitoring never authorizes automatic fixes.

## Troubleshooting checklist

1. Run \`jarvis status\` and \`codex mcp list\`.
2. Confirm your **actual** desktop session: \`echo "$XDG_SESSION_TYPE"\` and \`echo "$XDG_CURRENT_DESKTOP"\`.
3. On Wayland, ask the MCP for backend capability diagnostics; check screenshot vs input independently.
4. On X11, ensure \`xdotool\`, \`wmctrl\`, \`maim\` are installed; input is disabled until explicit opt-in.
5. Restart Codex after changing registrations or Skills.
6. Check reports and user journal for monitor-specific issues. Do not paste private logs/tokens into public issues.

## Safety

Desktop automation can read on-screen private information or cause unintended GUI changes. Observe first; ask permission before changes. Read [Security](security.md).
