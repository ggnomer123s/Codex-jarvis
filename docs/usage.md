# Using Tigo

Tigo provides a **single `tigo` launcher** for Codex CLI with desktop-context instructions. Desktop MCPs and installed Skills are discovered in the Codex session.

## Launch speed modes

- `tigo` and `tigo fast`: **low reasoning effort** and no auto-executed screen-inspection prompt. Recommended for short GUI tasks.
- `tigo normal`: use your ordinary Codex model/reasoning defaults.
- `tigo deep`: **high reasoning effort**, useful for complicated troubleshooting.

These per-launch settings do not overwrite your Codex config file. Reasoning support varies by model. See [Performance](performance.md).

## Main commands

| Command | Linux | Windows 11 |
|---|---|---|
| `tigo` / `tigo fast` | Low-reasoning responsive GUI mode | Low-reasoning responsive GUI mode |
| `tigo normal` / `tigo deep` | Default / high reasoning modes | Default / high reasoning modes |
| `tigo status` | GUI backend & monitor | Windows-MCP & monitor |
| `tigo reports` | Saved diagnostics | Saved diagnostics |
| `tigo gui-check` | Inspect backend, optional AT-SPI/marks helpers | Check registered Windows-MCP |
| `tigo monitor on/off` | Start/stop systemd user watcher (when available) | Toggle optional Scheduled Task |
| `tigo test` | Trigger synthetic failed user service | Not available |
| `tigo stop` | Hyprland: stops Hypruse; other desktops: exit Codex | Exit Codex with Ctrl+C or /exit |

## Suggested prompts

**Observe only:** “Discover the configured GUI MCP. Tell me which desktop/session and application are active, and show a screenshot. Do not click or type.”

**Diagnose a problem:** “My application behaves incorrectly. Observe the UI, collect non-destructive diagnostics, explain the most likely cause, and ask permission before making changes.”

**Hyprland GUI test:** “Launch a fresh terminal with Hypruse, type `echo TIGO_ONLINE` via GUI, execute it and verify the output.”

**X11 GUI test:** Once explicitly enabled: “Open a text editor manually, then click its editable area, type `TIGO_ONLINE` via tigo-x11 and verify the result with a screenshot. Do not save.”

**GNOME/KDE/general Wayland test:** “Use the GUI MCP's `describe_environment` first. Confirm screenshot and input availability. If a portal permission is requested, let me authorize it manually. Do not act if input is unavailable.”

**Windows test:** “Use Windows-MCP to open Notepad, type `TIGO_ONLINE` and verify with a screenshot. Do not save.”

## Memory and voice

- `tigo memory add` — interactively record a user-confirmed fix; nothing is written until you type YES.
- `tigo memory search <keyword>` and `tigo memory list` — inspect your private, local repair history.
- `tigo memory forget <id>` — delete an entry after confirming DELETE.
- `tigo voice` — push-to-talk mic capture, local faster-whisper speech recognition, transcript review, then YES to send text to Codex.

Audio is not sent to Codex, but the accepted transcript is. Voice requires PortAudio and downloads the Whisper model on first use. Memory is not synced to ChatGPT or GitHub. Detailed steps: [Memory & Voice](memory-and-voice.md).

## Monitoring scope

- Linux (with systemd --user): checks failed **user services**, roughly every two minutes, and optionally asks Codex for a read-only diagnostic report.
- Windows (opt in): watches **Application Error** events. It does not observe every application exception.
- The GUI agent does not run in the background unless you have an active Codex session. Screenshots are not captured continuously by these watchers.
- Monitoring never authorizes automatic fixes.

## Troubleshooting checklist

1. Run `tigo status` and `codex mcp list`.
2. Confirm your **actual** desktop session: `echo "$XDG_SESSION_TYPE"` and `echo "$XDG_CURRENT_DESKTOP"`.
3. On Wayland, ask the MCP for backend capability diagnostics; check screenshot vs input independently.
4. On X11, ensure `xdotool`, `wmctrl`, `maim` are installed; input is disabled until explicit opt-in.
5. Restart Codex after changing registrations or Skills.
6. Check reports and user journal for monitor-specific issues. Do not paste private logs/tokens into public issues.

## Accurate GUI navigation

Run `tigo gui-check` before the first full GUI test. On Hyprland the assistant should start with `desktop`, then prefer `ui` / `click_ui` or `marks`; when accessibility isn't available, use `screenshot` + `zoom` before `pointer`. After acting, use `then='ui'`, `then='desktop'` or `then='screenshot'` (when supported) to verify the outcome. These tools are not guaranteed on all backends.

Hypruse normal cursor movements are immediate, not animated. Built-in dragging already interpolates; avoid bypassing the MCP's guardrails solely for visual smoothing.

See [GUI Navigation](gui-navigation.md) for exact workflow and compositor limitations.

## Safety

Desktop automation can read on-screen private information or cause unintended GUI changes. Observe first; ask permission before changes. Read [Security](security.md).
