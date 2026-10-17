#!/usr/bin/env python3
"""Bounded AT-SPI adapter for the X11 MCP; system Python supplies GI.

Window PID + exact title bind each request. No whole-desktop text collection,
no coordinate fallback, no keyboard injection. Invocations require fresh
identity, enabled/showing state, one exact match and active X11 focus.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

MAX_NODES = 1200
MAX_DEPTH = 24


def _name(node):
    name = node.get_name() or ""
    return name if len(name) <= 500 else ""


def _role(node):
    return (node.get_role_name() or "").casefold()


def _children(node):
    for i in range(min(node.get_child_count(), MAX_NODES)):
        child = node.get_child_at_index(i)
        if child is not None:
            yield i, child


def find_window(desktop, pid, title):
    found = []
    for _, app in _children(desktop):
        try:
            if app.get_process_id() != pid:
                continue
            for _, window in _children(app):
                if _name(window) == title:
                    found.append(window)
        except Exception:
            continue
    if len(found) != 1:
        raise RuntimeError("AT-SPI could not uniquely identify this PID and window title. Use the current window screenshot instead.")
    return found[0]


def walk(window, atspi, *, name="", role="", limit=40, deadline=None):
    rows, nodes, visited = [], {}, 0
    stack = [(window, "", 0)]
    truncated = False
    while stack:
        if visited >= MAX_NODES or (deadline is not None and time.monotonic() >= deadline):
            truncated = True
            break
        node, path, depth = stack.pop()
        visited += 1
        try:
            label, kind = _name(node), _role(node)
            if path and (not name or label.casefold() == name.casefold()) and (not role or kind == role.casefold()):
                states = node.get_state_set()
                showing = states.contains(atspi.StateType.SHOWING)
                enabled = states.contains(atspi.StateType.ENABLED) and states.contains(atspi.StateType.SENSITIVE)
                actions = []
                try:
                    iface = node.get_action_iface()
                    if iface:
                        actions = [(iface.get_action_name(i) or "")[:80] for i in range(min(iface.get_n_actions(), 20))]
                except Exception:
                    pass
                if label or actions:
                    if len(rows) >= limit:
                        truncated = True
                        break
                    row = {"path": path, "name": label, "role": kind, "enabled": bool(enabled),
                           "showing": bool(showing), "actions": actions}
                    rows.append(row)
                    nodes[path] = node
            if depth < MAX_DEPTH:
                children = list(_children(node))
                stack.extend((child, f"{path}/{i}".lstrip("/"), depth + 1) for i, child in reversed(children))
            elif node.get_child_count():
                truncated = True
        except Exception:
            # A disappearing subtree cannot be safely invoked; incomplete scans
            # never establish uniqueness for a later action.
            truncated = True
    return rows, nodes, truncated


def execute(request, atspi, *, focus_check=None):
    window = find_window(atspi.get_desktop(0), request["pid"], request["title"])
    rows, nodes, truncated = walk(window, atspi, name=request.get("name", ""),
                                  role=request.get("role", ""), limit=request.get("limit", 40),
                                  deadline=time.monotonic() + 4)
    if request["action"] == "find":
        return {"elements": rows, "truncated": truncated, "windowTitle": request["title"], "pid": request["pid"]}
    path = request.get("path", "")
    matches = [row for row in rows if not path or row["path"] == path]
    if truncated or len(matches) != 1:
        raise RuntimeError("Element search is incomplete or ambiguous. Use an exact name, role and fresh path from ui_elements.")
    selected = matches[0]
    node = nodes[selected["path"]]
    if not selected["enabled"] or not selected["showing"]:
        raise RuntimeError("The selected element is disabled or not showing; no action was sent.")
    if focus_check:
        focus_check()
    # Resolve again after focus validation. Do not invoke a stale cached object
    # whose name, role or state changed while the interface was being inspected.
    if _name(node) != selected["name"] or _role(node) != selected["role"]:
        raise RuntimeError("Element changed; inspect the interface again.")
    states = node.get_state_set()
    if not all(states.contains(state) for state in (atspi.StateType.ENABLED, atspi.StateType.SENSITIVE, atspi.StateType.SHOWING)):
        raise RuntimeError("Element state changed; no action was sent.")
    iface = node.get_action_iface()
    if iface is None:
        raise RuntimeError("Element has no native action. Use a fresh visual observation instead.")
    candidates = [i for i in range(min(iface.get_n_actions(), 20))
                  if iface.get_action_name(i).casefold() in ("click", "press", "activate")]
    if len(candidates) != 1:
        raise RuntimeError("Element has no unique click/press/activate action. Use a fresh visual observation instead.")
    if not iface.do_action(candidates[0]):
        raise RuntimeError("Application did not accept the accessibility action. Do not blindly repeat it; verify state.")
    return {"invoked": selected, "verificationRequired": True}


def main():
    try:
        if os.environ.get("XDG_SESSION_TYPE") != "x11" or not os.environ.get("DISPLAY"):
            raise RuntimeError("This adapter requires a native X11 session.")
        request = json.loads(sys.stdin.read(20001))
        if request.get("action") not in ("find", "invoke"):
            raise ValueError("Unsupported accessibility operation.")
        if request["action"] == "invoke" and os.environ.get("TIGO_X11_ALLOW_INPUT", os.environ.get("JARVIS_X11_ALLOW_INPUT", "0")) != "1":
            raise PermissionError("X11 input is disabled.")
        import gi
        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi
        Atspi.set_timeout(800, 3000)

        def focus():
            active = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True, check=True, timeout=2).stdout.strip()
            pid = subprocess.run(["xdotool", "getwindowpid", request["window_id"]], capture_output=True, text=True, check=True, timeout=2).stdout.strip()
            title = subprocess.run(["xdotool", "getwindowname", request["window_id"]], capture_output=True, text=True, check=True, timeout=2).stdout.strip()
            if not active.isdecimal() or int(active) != int(request["window_id"], 16) or pid != str(request["pid"]) or title != request["title"]:
                raise RuntimeError("Window identity or focus changed; no action was sent.")
        result = execute(request, Atspi, focus_check=focus)
        print(json.dumps(result))
        return 0
    except Exception as exc:
        if isinstance(exc, (ImportError, ValueError)):
            message = "AT-SPI is unavailable or the request is invalid. Install system Python GI and AT-SPI introspection; see docs/gui-operator.md."
        else:
            message = str(exc)[:700]
        print(json.dumps({"error": message}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
