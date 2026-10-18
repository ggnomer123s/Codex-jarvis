# Tigo GUI Operator: intent routing, visual grounding, region tools

Tigo uses the requested outcome to decide **when to actually control the desktop**. This avoids a common failure mode: a user asks the agent to operate a visible program, but it only explains how to do it. The `tigo-desktop` Skill and the managed `AGENTS.md` block now explicitly ask Codex to use an authorized GUI MCP when the request calls for visible app interaction.

## Three distinct region operations

| User request | Operation | Does it change the application? |
|---|---|---|
| "Select this rectangle in a video timeline" | Mouse press → drag → release across the editor | **Yes** (may change a selection or move content) |
| "Look closely at this rectangle on screen" | Region screenshot / screenshot crop | **No** |
| "Let me pick which part of the desktop you inspect" | Interactive, human-selected screenshot region | **No** |

### Hyprland / Hypruse

The upstream Hypruse MCP already implements these tools.

1. `desktop`: find target window, workspace, geometry and monitor.
2. `ui` and `click_ui`: choose named controls where possible. Electron apps, image canvases and timeline editors may not expose their controls.
3. `screenshot(window="ADDRESS", stable=True)`: inspect the app if accessibility is unavailable.
4. `pointer(action="drag", x=START_X, y=START_Y, to_x=END_X, to_y=END_Y, button="left")`: draw a selection or drag an item. The upstream tool checks BOTH endpoints against Hypruse confinement/authentication rules.
5. `screenshot(region="x,y,WxH")`: capture a rectangle for visual inspection. `zoom(x,y,window="ADDRESS")` crops and enlarges small targets. A screenshot **does not** affect a GUI selection.

For fullscreen games or continuously animated video, use
`screenshot(window="ADDRESS", stable=False)` to observe the current frame;
waiting for identical frames can reach the tool's settling timeout each time.
Keep fullscreen mode, use current capture geometry/scale and try accessibility
only once if it reports no tree. This reduces avoidable observation waits, not
model inference time or a game's own input latency. Native seat/auth/lock guards
remain in force. See [fullscreen diagnostics](screen-control.md#fullscreen-input-and-diagnostics-on-hyprland).

These are example **MCP arguments**, not executable Python code. The live tool schema is authoritative. Global Hyprland logical coordinates must be derived from the screenshot's `geometry` and `scale`: `global = origin + image_pixel / scale`. The source of the request is never permission to bypass a seat or authentication refusal.

### Native X11 / bundled tigo-x11

The bundled X11 MCP now includes these independent tools:

```text
drag(x1=300, y1=180, x2=900, y2=480, button=1, steps=12,
     window_id="0x03400001")

screenshot_region(x=300, y=180, width=600, height=300)

user_select_screenshot()
```

- `drag` presses, interpolates movement and releases the mouse in a `finally` block. Use a `window_id` when possible to activate and verify the intended application. It requires opt-in `TIGO_X11_ALLOW_INPUT=1`.
- `screenshot_region` uses the documented `maim -g WxH+X+Y` geometry syntax, with numeric bounds and a maximum 4096-by-4096 region. Supports negative monitor coordinates.
- `user_select_screenshot` uses `maim -s` and waits up to 45 seconds for the **human** to draw the rectangle on an X11 display. It is a read-only operation; press Escape to cancel. This may require the system's `slop` support used by `maim`.
- `key(...,window_id=...)` uses the existing focus verification before sending app shortcuts.

**Important:** these tools cannot provide equivalent gestures on Wayland sessions through XWayland. Use the native Wayland/Hyprland tools there. In full-user desktop mode, X11 input events can alter user data; keep backups and avoid unintended drag-and-drop.

### Windows 11 / Windows-MCP

The existing Windows-MCP exposes the following capabilities in recent versions; no fork is necessary:

- `Move` with `drag=True`, `from_loc=[x1,y1]`, `loc=[x2,y2]` for point-to-point dragging. `MultiSelect` for multiple recognized controls.
- `Screenshot` or `Snapshot` with `region=[left,top,right,bottom]` for fast cropped observation.
- `Shortcut` for app keyboard combinations; `App` for window launch/switch.
- `DisplayInventory` for effective display bounds and scaling.

Tool schemas and permissions depend on the installed Windows-MCP release; inspect the available tool list rather than assuming every tool is present.

### Other Wayland compositors

The generic Wayland backend is experimental. Examine its advertised capabilities before attempting selection or drag. Access to the shell does not confer Wayland virtual-pointer permissions and must not be used as a backdoor around portal/MCP restrictions.

## How to test without altering valuable documents

**Visual route selection:** ask Tigo to open a disposable text editor, identify its document area through its GUI MCP and type `GUI_ROUTE_TEST`, without saving.

**Drag test:** open an empty drawing canvas or select an otherwise disposable rectangular area. Ask it to identify two on-screen points, use the platform-native `drag` to draw a selection and confirm the selected bounds. Don't try this first on a production Premiere timeline.

**Region test:** ask it to capture only the top-right 500x250 area of the active app and summarize visible controls. It should call a *region screenshot*, **not** a drag action.

**Multi-app route:** ask Tigo to focus one existing app, perform a reversible visual action, switch to another app and confirm the final focus. During this scenario, watch which tool it chose.

No code-path test alone proves live drag accuracy on a Hyprland or Windows machine. Success depends on monitor layouts, compositor rules, application focus and upstream MCP versions.

## Design review of related open-source projects

We examined their current public source/documentation as inspiration, but **did not copy their source or claim better benchmark results**.

| Project | Approach | Tigo design decision |
|---|---|---|
| [Microsoft UFO](https://github.com/microsoft/UFO) | HostAgent chooses the app; AppAgent handles target; native API + UI Automation and batched actions | Use a lightweight task router in the Skill rather than adding a costly second agent for every tiny task |
| [Agent-S](https://github.com/simular-ai/Agent-S) | Visual grounding agent and action reasoning, with a bounded visual trajectory | Separate reasoning from reliable target coordinates; zoom/crop only when accessibility can't resolve controls |
| [E2B Desktop](https://github.com/e2b-dev/desktop) | Primitive drag, mouse, keyboard, screenshots in a desktop sandbox | Expose uniform region/drag concepts without inventing another input layer for Hyprland |
| [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) | UI Automation and screenshot-first tools, window inventory, region captures and deterministic drags | Prefer upstream native abilities; don't reinstall redundant MCPs or patch them just to add instructions |
| [Hypruse](https://github.com/IlyasKhallouki/hypruse) | Semantic window state, AT-SPI, zoom, pointer with confinement and seat guards | Use native MCP safe actions rather than bypassing guarded actions via raw input scripts |

A measurable "better than" statement requires real **task-completion benchmarks**, including failures and latency, on the user's desktop or a reproducible fixture. We can evaluate visual selection, multi-app navigation, editing tasks, and auth-refusal behavior separately in later experiments.

## Performance checklist

- Identify the target application once; retain valid window handles.
- Prefer an accessibility name/ID over estimated pixels.
- Capture one app or a small rectangle, not the whole desktop, when visual information is enough.
- Use a native API for repetitive bulk editing, but GUI tools for visible user interactions.
- Keep drag start/end points grounded, release buttons on failure, and verify the final selection.
- Do not perform arbitrary shell inputs after a GUI MCP refuses scope or auth.
- Continue a long task by checkpoints rather than restarting its entire sequence.

## Semantic interface targeting

For labeled buttons, fields and menus, use the target window's accessibility
structure first. It returns names/roles/state without interpreting a screenshot.
Canvas/unsupported applications still need one scoped image. Do not repeat
empty tree queries or switch input backends after a guard refusal.

| Session | Semantic observation/action |
|---|---|
| Hyprland | Existing Hypruse `ui` scoped to the window and `click_ui` |
| Windows | Existing Windows-MCP `Snapshot`, with `use_vision=False` when supported; use current returned control target/geometry with native input tools |
| Native X11 | New `ui_elements` and `click_ui` using the bundled AT-SPI adapter |

Tool versions differ: inspect the current schema. Windows Click is not assumed
to accept a name. DOM extraction may be available through Snapshot's use_dom
option or a configured browser MCP; this change does not install a new browser
extension or replace browser authentication. Runtime diagnostics distinguish
advertised semantic tools from actual app accessibility/input ownership.

X11 examples, using a window ID obtained from `windows`:

```json
{"tool":"ui_elements","arguments":{"window_id":"0x1234","name":"Save","role":"push button"}}
{"tool":"click_ui","arguments":{"window_id":"0x1234","name":"Save","role":"push button","path":"0/2"}}
```

Use the returned path, not the illustrative path above. Names/roles match exactly
(case-insensitive); duplicate labels require a fresh role/path. The helper binds
queries to the window PID and exact title, caps tree traversal at 1200 nodes /
24 levels and returns at most 100 matches. It never reads text-field values.
Incomplete trees cannot establish a unique action target. An action rechecks
identity, focus, name/role, enabled/sensitive/showing state and invokes one
native click/press/activate action. A delivered action still needs application
result verification. No coordinate fallback, cached control replay or automatic
action retry occurs. An uncertain timeout requires observation before another
action. Existing read-only X11 registrations remain read-only.

The helper runs in `/usr/bin/python3` so the uv MCP can use distribution GI
without building PyGObject. Install system Python GI + AT-SPI typelibs as listed
in [installation](install-desktop.md#dictation-and-semantic-controls-012).
The lightweight installer copies both helper files, including the retained
legacy backend location, and warns if system GI/Atspi is missing. The full
Linux updater installs these prerequisites. A native X11 session, session
accessibility bus and an application exporting a useful tree are required.
Nothing enables global accessibility settings, weakens ownership guards or
makes a Wayland session an X11 session. Restart Tigo/Codex after installation.
