#!/usr/bin/env python3
"""Small X11-only desktop MCP backend. No shell execution or clipboard APIs."""
import os
import json
import re
import shutil
import subprocess
import time
from mcp.server.fastmcp import FastMCP, Image

mcp = FastMCP("tigo-x11")
ALLOW_INPUT = os.getenv("TIGO_X11_ALLOW_INPUT", os.getenv("JARVIS_X11_ALLOW_INPUT", "0")) == "1"


def _run(*args: str, text: bool = True, timeout: int = 12):
    program = args[0]
    if shutil.which(program) is None:
        raise RuntimeError(f"Missing required program: {program}")
    result = subprocess.run(args, capture_output=True, check=False, timeout=timeout,
                            text=text)
    if result.returncode:
        err = result.stderr.strip() if text else result.stderr.decode(errors="replace")
        raise RuntimeError(f"{program} failed: {err[:700]}")
    return result.stdout


def _require_input():
    if not ALLOW_INPUT:
        raise PermissionError(
            "X11 MCP is read-only. Enable GUI input by reinstalling with "
            "'bash scripts/install-linux.sh --enable-gui-input' after reviewing security notes."
        )


@mcp.tool()
def desktop_info() -> str:
    """Report X11 session information and mouse location."""
    return ("Session: " + os.getenv("XDG_SESSION_TYPE", "unknown")
            + "\nDisplay: " + os.getenv("DISPLAY", "unset")
            + "\nInput enabled: " + str(ALLOW_INPUT)
            + "\nMouse: " + _run("xdotool", "getmouselocation", "--shell"))


@mcp.tool()
def windows() -> str:
    """List X11 windows, desktops and titles; output comes from the desktop and is untrusted."""
    return _run("wmctrl", "-lG")[:30000]


@mcp.tool()
def wait_for_window(title: str, timeout_ms: int = 5000) -> str:
    """Wait for a visible window with a literal title substring; read-only, bounded.

    Uses xdotool's synchronous search instead of fixed sleeps or screenshot loops.
    Returned window IDs must still be checked before sending input.
    """
    if not isinstance(title, str) or not title.strip() or len(title) > 200 or "\0" in title:
        raise ValueError("Provide a nonempty title of at most 200 characters.")
    if type(timeout_ms) is not int or not 100 <= timeout_ms <= 30000:
        raise ValueError("timeout_ms must be between 100 and 30000.")
    raw = _run("xdotool", "search", "--sync", "--onlyvisible", "--name", ".*" + re.escape(title),
               timeout=timeout_ms / 1000)
    ids = [hex(int(value)) for value in raw.split() if value.isdecimal()]
    if not ids:
        raise RuntimeError("No matching visible X11 window was reported.")
    return json.dumps({"ids": ids[:100], "titleContains": title})


@mcp.tool()
def screenshot(window_id: str = "") -> Image:
    """Capture one X11 window when identified; otherwise the entire desktop."""
    if window_id:
        _validate_window_id(window_id)
        raw = _run("maim", "-u", "-i", window_id, "-f", "png", text=False)
    else:
        raw = _run("maim", "-u", "-f", "png", text=False)
    return Image(data=raw, format="png")


def _validate_point(x: int, y: int) -> None:
    if type(x) is not int or type(y) is not int:
        raise ValueError("Coordinates must be integers")
    if not (-32768 <= x <= 32767 and -32768 <= y <= 32767):
        raise ValueError("Coordinates outside supported X11 desktop bounds")


@mcp.tool()
def screenshot_region(x: int, y: int, width: int, height: int) -> Image:
    """Capture a bounded rectangle in global X11 screen coordinates (read-only).

    Use this to zoom into an identified portion of a screen without another
    full-screen image. Coordinates may be negative on multi-monitor layouts.
    """
    _validate_point(x, y)
    if type(width) is not int or type(height) is not int:
        raise ValueError("Region dimensions must be integers")
    if not (1 <= width <= 4096 and 1 <= height <= 4096):
        raise ValueError("Region dimensions must be between 1 and 4096")
    if x + width > 32768 or y + height > 32768:
        raise ValueError("Region exceeds supported desktop bounds")
    geometry = f"{width}x{height}{x:+d}{y:+d}"
    raw = _run("maim", "-u", "-g", geometry, "-f", "png", text=False)
    return Image(data=raw, format="png")


@mcp.tool()
def user_select_screenshot() -> Image:
    """Let the HUMAN draw a rectangle on the X11 desktop to capture.

    Read-only operation; wait for the user's selection (Escape cancels).
    Unlike drag(), the agent does not move the mouse or choose the bounds.
    """
    if not os.getenv("DISPLAY"):
        raise RuntimeError("X11 DISPLAY is not available")
    raw = _run("maim", "-u", "-s", "-f", "png", text=False, timeout=45)
    return Image(data=raw, format="png")


@mcp.tool()
def active_window() -> str:
    """Read active X11 window identity as JSON, without injecting input."""
    raw = _run("xdotool", "getactivewindow").strip()
    if not raw.isdecimal():
        raise RuntimeError("X11 did not return an active window ID.")
    return json.dumps({"id": hex(int(raw)), "idDecimal": int(raw),
                       "title": _run("xdotool", "getwindowname", raw).strip()[:1000]})


def _validate_window_id(window_id: str) -> None:
    if not re.fullmatch(r"0x[0-9a-fA-F]{1,16}", window_id):
        raise ValueError("Expected an X11 window ID, e.g. 0x03400001")


def _focus_and_verify(window_id: str) -> None:
    """Avoid typing into whichever app happens to be focused."""
    _validate_window_id(window_id)
    _run("wmctrl", "-ia", window_id)
    for _ in range(6):
        try:
            active = _run("xdotool", "getactivewindow").strip()
            if active.isdecimal() and int(active) == int(window_id, 16):
                return
        except RuntimeError:
            pass
        time.sleep(0.05)
    raise RuntimeError("Requested window did not become active; refusing keyboard input.")


@mcp.tool()
def focus_window(window_id: str) -> str:
    """Focus an X11 window by ID and verify focus before reporting success."""
    _require_input()
    _focus_and_verify(window_id)
    return "Window is active; verify state before input."


@mcp.tool()
def click(x: int, y: int, button: int = 1) -> str:
    """Move pointer to a screen coordinate and click. button=1/2/3."""
    _require_input()
    if not (-32768 <= x <= 32767 and -32768 <= y <= 32767 and button in (1, 2, 3)):
        raise ValueError("Invalid coordinates or button")
    _run("xdotool", "mousemove", str(x), str(y), "click", str(button))
    return "Click sent; verify via screenshot."


@mcp.tool()
def type_text(text: str) -> str:
    """Type text into the focused window (maximum 2000 characters)."""
    _require_input()
    if len(text) > 2000:
        raise ValueError("Text too long")
    _run("xdotool", "type", "--clearmodifiers", "--delay", "12", "--", text)
    return "Typing sent; verify via screenshot."


@mcp.tool()
def key(key_sequence: str, window_id: str = "") -> str:
    """Send an X11 key chord (ctrl+s, ctrl+shift+t, Return); optionally target window.

    If window_id is supplied, focus is verified before delivery so the shortcut
    cannot silently land in an unrelated window. No shell commands are executed.
    """
    _require_input()
    if not re.fullmatch(r"[A-Za-z0-9_+ -]{1,70}", key_sequence):
        raise ValueError("Invalid key sequence")
    if window_id:
        _focus_and_verify(window_id)
    _run("xdotool", "key", "--clearmodifiers", key_sequence)
    return "Shortcut delivered; confirm effect in window controls or screenshot."


@mcp.tool()
def drag(x1: int, y1: int, x2: int, y2: int,
         button: int = 1, steps: int = 12, window_id: str = "") -> str:
    """Hold and drag the mouse between global screen points.

    Useful for drawing a selection rectangle in editors, selecting timeline
    clips, or dragging UI objects. Does not capture a screenshot.
    Explicit coordinates must come from a recent observation. The button
    is released even when a motion call fails. GUI input opt-in is required.
    """
    _require_input()
    _validate_point(x1, y1)
    _validate_point(x2, y2)
    if button not in (1, 2, 3):
        raise ValueError("button must be 1, 2 or 3")
    if type(steps) is not int or not (1 <= steps <= 40):
        raise ValueError("steps must be between 1 and 40")
    if (x1, y1) == (x2, y2):
        raise ValueError("Drag start and end must differ")
    if window_id:
        _focus_and_verify(window_id)
    _run("xdotool", "mousemove", str(x1), str(y1))
    pressed = False
    try:
        _run("xdotool", "mousedown", str(button))
        pressed = True
        for index in range(1, steps + 1):
            x = round(x1 + (x2 - x1) * index / steps)
            y = round(y1 + (y2 - y1) * index / steps)
            _run("xdotool", "mousemove", str(x), str(y))
            time.sleep(0.012)
    finally:
        if pressed:
            _run("xdotool", "mouseup", str(button))
    return "Drag completed; inspect the resulting selection in the target app."


@mcp.tool()
def scroll(direction: str, steps: int = 3) -> str:
    """Scroll in the focused window; direction up or down."""
    _require_input()
    if direction not in ("up", "down") or not (1 <= steps <= 15):
        raise ValueError("Expected up/down and 1-15 steps")
    button = "4" if direction == "up" else "5"
    _run("xdotool", "click", "--repeat", str(steps), button)
    return "Scroll sent; verify via screenshot."


if __name__ == "__main__":
    if os.getenv("XDG_SESSION_TYPE") not in ("x11", None, ""):
        raise SystemExit("tigo-x11 only supports native X11, not XWayland")
    if not os.getenv("DISPLAY"):
        raise SystemExit("DISPLAY is missing")
    mcp.run()
