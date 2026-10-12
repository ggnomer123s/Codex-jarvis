# High-accuracy GUI navigation (desktop computer use)

This guide describes how to get **reliable clicks and navigation**, not merely faster mouse automation. JARVIS prefers native window state and accessibility semantics to guessed screenshot coordinates. The [JARVIS Skill](../skills/jarvis-desktop/SKILL.md) encodes this workflow for Codex.

## Pointer animation versus actual accuracy

**Hypruse's normal pointer move is an immediate compositor cursor move**, not a human-style animation. Its built-in drag has 12 intermediate position steps with short pauses. This is implemented in the [Hypruse input code](https://github.com/IlyasKhallouki/hypruse/blob/main/src/hypruse/input.py). Neither JARVIS nor this repository currently patches Hypruse to animate all moves.

Artificial mouse smoothing is **not necessary** for accuracy; indiscriminately generating extra cursor moves may trigger Hyprland focus-follows-mouse or conflict with safety guards. Do not implement a smoothing workaround outside the MCP authorization/confinement layer.

## The correct navigation order on Hyprland

| Priority | Hypruse tool | Why |
|---|---|---|
| 1 | `desktop` | Find the real window address, active workspace, monitor, geometry and occluding layer surfaces |
| 2 | `hypr` / `launch` | Switch/focus/open windows deterministically through compositor IPC |
| 3 | `ui` and `click_ui` | Read named accessible controls and click them by semantic identity instead of estimating pixels |
| 4 | `marks` | View numbered accessible controls and select the correct mark |
| 5 | `screenshot(window=..., stable=true)` | Capture exact window context when the accessibility tree is missing/incomplete |
| 6 | `zoom` → `pointer` | Refine a visual coordinate for small controls before clicking |
| 7 | `then='ui'`, `then='desktop'`, `then='screenshot'` / `wait_for` | Verify effects and wait for real events |

### Why accessibility beats guessed pixels

GTK/Qt applications often expose an AT-SPI accessibility tree with labeled buttons, text fields and current values. Hypruse can extract these via D-Bus using system tools such as `busctl`. The agent can click the **named** control with `click_ui` rather than guessing its position.

For ambiguous controls, `marks` overlays numbers on a captured app window and returns a legend, allowing the agent to choose the correct target explicitly. It needs ImageMagick for drawing the overlay; without it, the accessible-element list still works.

Native screens with canvas UIs, terminals, some Electron apps and games may expose little or no accessibility tree. The fallback is **screenshot → zoom → pointer**, not random clicking.

### Hyprland prerequisites (optional accuracy upgrade)

Check:

~~~bash
command -v busctl
command -v magick
uvx hypruse doctor
~~~

If `magick` is missing, install **ImageMagick** using your distribution's package manager:

~~~bash
# Arch / CachyOS / Manjaro / EndeavourOS
sudo pacman -S --needed imagemagick

# Ubuntu / Debian / Linux Mint
sudo apt install imagemagick

# Fedora
sudo dnf install ImageMagick

# openSUSE
sudo zypper install ImageMagick
~~~

**Note:** some distributions still package ImageMagick 6, whose CLI uses `convert` rather than `magick`. The exact Hypruse `marks` overlay support depends on upstream requirements; the semantic `ui` tool and `click_ui` may work without it. Installing ImageMagick does not magically expose accessibility trees for every app.

For a full test, start a normal GTK/Qt app such as a file manager and ask Codex to list its controls via `ui`. Don't assume AT-SPI works merely because `busctl` is installed.

### Example prompt for an orientation test

> Discover my GUI MCP. Run the semantic desktop snapshot first. Identify the active window and workspace. Read available accessibility controls and show me a few named actions. If the accessibility tree is unavailable, take an exact window screenshot, zoom onto a small non-sensitive control, and describe its position. Do not click, type or change anything.

Only after that succeeds:

> Open a disposable text editor window through the desktop MCP. Identify its text-entry area, type JARVIS_GUI_TEST using that window's GUI controls, and verify the visible or accessible result. No files saved.

## Other desktop environments

**X11:** The bundled `jarvis-x11` backend uses `wmctrl` for window lists, `maim` for screenshots and `xdotool` for pointer/keyboard. It does **not** yet provide Hypruse-equivalent `ui` / `click_ui` semantics; input is disabled by default. Use per-window metadata and current screenshots, verify every input, and avoid fragile hardcoded coordinates.

**GNOME, KDE Plasma and other Wayland:** The generic Wayland MCP is experimental. Ask for `describe_environment` to confirm whether screenshots and portal-mediated remote input are actually available. Compositor-specific extensions may offer better native accessibility on compatible versions; see the [MCP backend guide](mcp-and-skills.md).

**Windows 11:** Windows-MCP can use Windows UI Automation where supported, combined with screenshots when necessary. Its actual tool names and accessible elements vary by app and server version. Never assume a GUI tool is present without checking.

## Safety and reliability requirements

- Ask the user before changing settings, closing unsaved work, sending a message or running destructive actions.
- Do not bypass Hypruse restrictions, authentication guards, password fields or session locks.
- If focus or a window's position changes unexpectedly, re-read the desktop state.
- Never infer success from a successful click delivery alone: inspect actual postconditions.
- After two failures, stop and explain the evidence instead of repeating clicks.

## FAST MODE: fewer screenshots, quicker UI decisions

JARVIS ships with an updated `jarvis-desktop` Skill that favors **semantic-first, event-driven navigation**.

For simple reversible actions:
1. Query `desktop` once to identify the window and workspace.
2. Use `ui` + `click_ui` if the element is accessible; otherwise make **one window-specific screenshot**, then `zoom` only if the target is small or ambiguous.
3. Prefer `sequence` for a few already-grounded safe actions.
4. Check the **final state once** using `then='ui'` or `then='desktop'`. Use `wait_for` for delayed changes.
5. Stop after two unsuccessful observation attempts instead of capturing the screen repeatedly.

**Do not trade away safety to gain speed.** An authorization/confinement refusal is final; messaging, deletion, purchases, privilege changes and editing sensitive state still require explicit confirmation.

### Example

> Fast mode. Open the already permitted Telegram window, choose one visible chat and stop. Do not send anything. Use desktop + accessibility UI before screenshots, avoid repeated screen captures, and verify selection once. If confinement refuses, stop and report it.

The actual speed also depends on network latency, model reasoning effort and whether the application exposes AT-SPI controls. This Skill changes agent behavior; it does not make the MCP server itself faster or guarantee a fixed latency.
