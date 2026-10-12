#!/usr/bin/env python3
"""Small X11-only desktop MCP backend. No shell execution or clipboard APIs."""
import os
import re
import shutil
import subprocess
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
def screenshot() -> Image:
    """Capture the current X11 desktop as an image. May include sensitive information."""
    raw = _run("maim", "-u", "-f", "png", text=False)
    return Image(data=raw, format="png")


@mcp.tool()
def active_window() -> str:
    """Read active X11 window ID and title."""
    return _run("xdotool", "getactivewindow", "getwindowname")[:1000]


@mcp.tool()
def focus_window(window_id: str) -> str:
    """Focus an X11 window by its hexadecimal ID, after user approval."""
    _require_input()
    if not re.fullmatch(r"0x[0-9a-fA-F]+", window_id):
        raise ValueError("Expected an X11 window ID like 0x03400001")
    _run("wmctrl", "-ia", window_id)
    return "Focus requested; verify via active_window or screenshot."


@mcp.tool()
def click(x: int, y: int, button: int = 1) -> str:
    """Move pointer to a screen coordinate and click. button=1/2/3."""
    _require_input()
    if not (0 <= x <= 32767 and 0 <= y <= 32767 and button in (1, 2, 3)):
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
def key(key_sequence: str) -> str:
    """Press an X11 key chord, e.g. ctrl+l, Return, super+e."""
    _require_input()
    if not re.fullmatch(r"[A-Za-z0-9_+ -]{1,70}", key_sequence):
        raise ValueError("Invalid key sequence")
    _run("xdotool", "key", "--clearmodifiers", key_sequence)
    return "Key sent; verify via screenshot."


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
