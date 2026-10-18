# Screen activity and returning control

The Tigo GUI shows a cyan/violet border and a **Tigo uses the screen** banner
while recognized desktop MCP calls are running. The banner uses Russian unless
the voice language is explicitly English. A brief 1.2-second tail between calls
reduces flashing. Normal messages, shell/file operations and the read-only
Windows ControlStatus check do not activate it. Both model-driven MCP calls and
saved desktop workflows are covered. Calls must expose a known desktop server
or a namespaced desktop tool in app-server events; opaque wrappers and other
clients/terminal sessions cannot be observed by this GUI.

## Stop the Tigo task

- Click **Return control** in the banner, or press **Ctrl+Alt+Shift+F10** when
  the banner advertises that shortcut.
- This cancels the workflow and closes the GUI's owned Codex app-server process
  tree, clears the indicator and stops speech. The task does not resume
  automatically. Start a new request when ready. Completed actions are not undone;
  detached/external applications may continue independently.
- The stop IPC accepts only a fixed message from the same local user. It never
  starts a task, elevates privileges or grants desktop permissions.

The global shortcut uses Windows RegisterHotKey or a temporary Hyprland binding.
Existing bindings are not overwritten. Hyprland config reloads are checked before
showing the shortcut again; Tigo removes only its own unmodified binding on exit.
Forced termination can leave the temporary Hyprland binding until a compositor
config reload or the next Tigo launch; it only sends stop IPC and never starts a GUI.
Other Linux desktops use the clickable button. If registration fails, the
banner offers the button without claiming a working global shortcut.

## Windows 11 ownership remains with Windows-MCP

Windows-MCP also supplies its own ownership indicator and physical-input gate.
Its documented takeover combination is **Ctrl+Alt+Shift+Backspace**; substantial
physical mouse movement also requests takeover. Use that native escape first
if the service's input gate prevents the Tigo button/shortcut from receiving
input, then use Tigo's Return control to cancel the task. Native takeover holds
desktop actions until the configured idle interval, whereas Tigo's stop ends
the current task. See the [upstream ownership documentation](https://github.com/CursorTouch/Windows-MCP#-mcp-tools).

On Windows, the Tigo banner sits at the bottom center of each monitor's usable
work area, above the taskbar. Windows-MCP keeps its own top-center ownership
notice. Tigo's thin border is inset past the native 56-physical-pixel edge glow,
with an extra logical-pixel margin; the offset accounts for each screen's device
pixel ratio. This avoids placing the two notices in the same area. The layout
wraps text and stacks the button on narrow displays. Monitor/work-area/DPI
changes refresh an active overlay without activating an application window.
Linux X11 retains the original edge border/top-center banner; Wayland uses
the output geometry and input regions described below. No MCP window is hidden, reconfigured or repeatedly sent behind
Tigo. Both takeover shortcuts and the Return control button keep their behavior.
The native layout was reviewed in [Windows-MCP's ownership overlay source](https://github.com/CursorTouch/Windows-MCP/blob/main/src/windows_mcp/desktop/control_overlay.py)
and [artwork dimensions](https://github.com/CursorTouch/Windows-MCP/blob/main/src/windows_mcp/desktop/control_overlay_art.py);
third-party versions can change their appearance.

Tigo's banner indicates observed tool activity, not proof of exclusive OS
ownership. It does not disable Windows-MCP/Hypruse takeover guards, install
input-blocking hooks, lock the session or prevent the human from interrupting.
Keep the mouse/keyboard idle while automation is active to avoid conflicting
input. Full Access is a separate Codex sandbox setting.

## Linux display support and installation

Hyprland and other layer-shell compositors use a small GTK4 helper with a banner
and four thin edge surfaces. It spans the full output, including fullscreen
windows, rather than the smaller panel-reserved work area. The layer-shell
[exclusive-zone setting](https://wayland.app/protocols/wlr-layer-shell-unstable-v1#zwlr_layer_surface_v1:request:set_exclusive_zone)
is -1: no space is reserved, and panel exclusion zones do not inset the frame.
The compositor handles output position/scale without manual physical-pixel math.

Edges have empty [GDK input regions](https://docs.gtk.org/gdk4/method.Surface.set_input_region.html);
banner text/background also pass clicks through. Only Return control has a mouse
input region. It is computed after GTK allocation, clipped to the surface and
refreshed after layout/remapping, including translated button sizes. There is no
continuous polling or keyboard focus grab. Its stdin pipe closes with the parent;
EOF destroys the surfaces. Monitor changes rebuild the surfaces. Install the
[system prerequisites](install-desktop.md#screen-activity-indicator-prerequisites).
GTK bindings come from the system Python, separate from uv.

Windows and Linux X11 use nonactivating Qt tool windows, with input-transparent
edges and a clickable banner. Other Wayland compositors need layer-shell;
unsupported/missing helpers produce a visible Tigo notice. No elevated or
full-screen input blocker is used as a fallback. OS secure desktops, lock screens
and exclusive full-screen applications can prevent normal overlays from showing.

The GUI cannot remove its overlay synchronously from third-party screenshots:
the banner/border can appear in captures and cover a small area (bottom center
on Windows, top center on Linux).
Windows-MCP hides its own native indicator during capture independently. No
screenshots, screen recordings or user-input history are collected by this feature.

Verification on Linux used a simulated task to show the real layer-shell border
over another workspace and click Return control. Windows registration/dispatch,
IPC and cancellation are covered by fixtures; Windows hardware behavior remains
unverified.


The Windows coexistence layout has also been exercised with actual Qt widgets
in offscreen fixtures: mixed 100/150/200% scale assumptions, negative monitor
coordinates, bottom/top/left taskbars, a narrow display, input transparency,
stop clicks and live geometry/work-area/DPI notifications. These checks validate
placement and callbacks; they do not establish native Windows z-order behavior
with a particular installed Windows-MCP version.

## Fullscreen input and diagnostics on Hyprland

Fullscreen alone does not require changing access profiles or toggling the app
back to windowed mode. Tigo's own indicator must not swallow clicks aimed at app
controls. Prefer a named control once when the app exposes accessibility; when
it exposes no tree (common for games/canvases), use a current window capture and
its geometry/scale, then one grounded input action or a short supported sequence.
Do not repeatedly probe an empty tree or recapture the full desktop for each click.
See [GUI targeting](gui-operator.md#hyprland--hypruse).

Hypruse still owns input delivery and seat/auth/lock guards. A cursor/focus change
by another participant can refuse input; do not disable STRICT or retry blindly.
A successful transport call is not proof that a game accepted a click. Games with
locked/relative pointers can require an application-specific route; ordinary
absolute menu clicks do not establish continuous camera/game control. No such
new input backend or game-latency guarantee is introduced by the frame fix.

For an explicit live helper regression check on Hyprland (quit Tigo first):

```bash
TIGO_TEST_WAYLAND_OVERLAY=1 python3 -m unittest discover -s tests -p test_layer_overlay.py -v
```

This briefly displays only the test indicator and reads its own Wayland protocol
and monitor/layer metadata. It checks full-output edges, input regions, translated
button layout, hide/show and EOF cleanup; it does not click user applications or
measure model/game latency. System GTK/Pycairo dependencies are required.
