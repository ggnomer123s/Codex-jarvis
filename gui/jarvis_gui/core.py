"""Dependency-free CLI protocol helpers, shared by the UI and its tests."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil


@dataclass(frozen=True)
class Event:
    kind: str
    text: str = ""


def find_codex() -> str | None:
    # On Windows prefer the native executable, then npm's cmd shim.
    names = ("codex.exe", "codex.cmd") if os.name == "nt" else ("codex",)
    return next((path for name in names if (path := shutil.which(name))), None)


def launch_command(executable: str, arguments: list[str], *, windows: bool | None = None) -> tuple[str, list[str]]:
    """Launch npm's Windows shim through Node, without cmd.exe interpolation."""
    windows = os.name == "nt" if windows is None else windows
    if windows and executable.lower().endswith(".cmd"):
        script = Path(executable).parent / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        node = shutil.which("node.exe") or shutil.which("node")
        if not node or not script.is_file():
            raise ValueError("Could not locate Node and the Codex npm entry point. Reinstall @openai/codex or put codex.exe on PATH.")
        return node, [str(script), *arguments]
    return executable, arguments


def build_arguments(folder: str, effort: str = "low", access: str = "read-only",
                    thread_id: str = "") -> list[str]:
    if not Path(folder).is_dir():
        raise ValueError("Choose an existing workspace folder.")
    if effort not in ("low", "default", "high"):
        raise ValueError("Unknown reasoning mode.")
    if access not in ("read-only", "workspace-write"):
        raise ValueError("Unknown workspace access mode.")
    # Prompt is sent through stdin, never interpreted as a command-line option.
    # exec is noninteractive; explicitly keep approvals at never so operations
    # outside the selected sandbox fail instead of waiting for an invisible UI.
    args = ["exec", "--json", "--sandbox", access, "--config", "approval_policy=\"never\"",
            "--skip-git-repo-check", "-C", str(Path(folder).resolve())]
    if effort != "default":
        args += ["--config", f"model_reasoning_effort={effort}"]
    if thread_id:
        args += ["resume", thread_id]
    return args + ["-"]


def parse_event(line: str) -> Event | None:
    try:
        data = json.loads(line)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    kind = data.get("type", "")
    if kind == "thread.started":
        return Event("thread", str(data.get("thread_id", "")))
    if kind in ("error", "turn.failed"):
        error = data.get("error", data.get("message", "Codex request failed."))
        if isinstance(error, dict):
            error = error.get("message", "Codex request failed.")
        return Event("error", str(error))
    if kind == "turn.completed":
        return Event("complete")
    if kind == "turn.started":
        return Event("activity", "Understanding your request")
    item = data.get("item")
    if not isinstance(item, dict):
        return None
    item_kind = item.get("type")
    if item_kind == "agent_message" and kind == "item.completed":
        return Event("answer", str(item.get("text", "")))
    if kind in ("item.started", "item.updated"):
        if item_kind == "command_execution":
            return Event("activity", "Running: " + str(item.get("command", ""))[:180])
        if item_kind == "mcp_tool_call":
            return Event("activity", "Using " + str(item.get("server", "MCP")) +
                         " / " + str(item.get("tool", "tool")))
        if item_kind == "web_search":
            return Event("activity", "Searching the web")
        if item_kind == "file_change":
            return Event("activity", "Updating workspace files")
        if item_kind == "reasoning":
            return Event("activity", "Planning the next step")
    return None
