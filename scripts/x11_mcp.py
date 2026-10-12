#!/usr/bin/env python3
"""Small X11-only desktop MCP backend. No shell execution or clipboard APIs."""
import os
import re
import shutil
import subprocess
import time
from mcp.server.fastmcp import FastMCP, Image

mcp = FastMCP("jarvis-x11")
ALLOW_INPUT = os.getenv("JARVIS_X11_ALLOW_INPUT", "0") == "1"


def _run(*args: str, text: bool = True):
    program = args[0]
    if shutil.which(program) is None:
        raise RuntimeError(f"Missing required program: {program}")
    result = subprocess.run(args, capture_output=True, check=False, timeout=12,
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
def screenshot(window_id: str = "") -> Image:
    """Capture one X11 window when identified; otherwise the entire desktop."""
    if window_id:
        _validate_window_id(window_id)
        raw = _run("maim", "-u", "-i", window_id, "-f", "png", text=False)
    else:
        raw = _run("maim", "-u", "-f", "png", text=False)
    return Image(data=raw, format="png")


@mcp.tool()
def active_window() -> str:
    """Read active X11 window ID and title."""
    return _run("xdotool", "getactivewindow", "getwindowname")[:1000]


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
        raise SystemExit("jarvis-x11 only supports native X11, not XWayland")
    if not os.getenv("DISPLAY"):
        raise SystemExit("DISPLAY is missing")
    mcp.run()
