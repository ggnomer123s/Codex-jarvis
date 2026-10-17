"""Exact aliases and short checked desktop-MCP sequences on the active profile.

Definitions come only from the user's settings editor. No model output, file in
a workspace or tool result can register a workflow. One desktop action at a time.
"""
from __future__ import annotations

import json
import math
import time

from PySide6.QtCore import QObject, QTimer, Signal

SERVERS = {"hypruse", "tigo-x11", "windows-mcp", "tigo-wayland",
           "jarvis-x11", "jarvis-wayland"}  # Existing MCP grants/workflows remain valid.
OBSERVATIONS = {"desktop", "ui", "windows", "snapshot", "state", "screenshot", "screenshot_region",
                "describe_environment", "displayinventory", "wait_for", "waitfor", "wait_for_window",
                "active_window", "desktop_info", "ui_elements"}
DESKTOP_TOOLS = OBSERVATIONS | {"launch", "hypr", "focus_window", "click_ui", "sequence", "pointer",
                               "keyboard", "key", "click", "drag", "scroll", "type", "type_text", "app", "move",
                               "shortcut", "multiselect", "use_bind", "binds", "marks"}


def validate_workflows(text):
    if len(text) > 100000:
        raise ValueError("Workflow definitions are limited to 100 KB.")
    try:
        value = json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
    except ValueError as exc:
        raise ValueError("Enter a JSON array of workflows.") from exc
    if not isinstance(value, list) or len(value) > 30:
        raise ValueError("Use at most 30 workflows in a JSON array.")
    aliases = set()

    def call_valid(call, observation=False):
        if not isinstance(call, dict) or set(call) - {"server", "tool", "arguments"}:
            raise ValueError("A call needs server, tool and arguments only.")
        if call.get("server") not in SERVERS or not isinstance(call.get("tool"), str):
            raise ValueError("Use a configured Tigo desktop MCP server.")
        tool = call["tool"].casefold().removesuffix("-tool")
        if tool not in (OBSERVATIONS if observation else DESKTOP_TOOLS):
            raise ValueError("Workflows support desktop tools only; checks must use observation tools.")
        if not isinstance(call.get("arguments", {}), dict):
            raise ValueError("Tool arguments must be a JSON object.")

    def check_valid(check):
        if not isinstance(check, dict) or set(check) not in ({"call", "contains"}, {"call", "path", "equals"}):
            raise ValueError("A check needs an observation call and either contains or path + equals.")
        call_valid(check["call"], True)
        if "contains" in check:
            if not isinstance(check["contains"], str) or not 1 <= len(check["contains"]) <= 500:
                raise ValueError("Check text must contain 1 to 500 characters.")
        else:
            path = check["path"]
            if not isinstance(path, list) or not 1 <= len(path) <= 8 or any(
                    not (isinstance(key, str) and 1 <= len(key) <= 100) and not (type(key) is int and 0 <= key <= 10000) for key in path):
                raise ValueError("A structured check path has 1 to 8 object keys or array indices.")
            expected = check["equals"]
            if isinstance(expected, (dict, list)) or (isinstance(expected, str) and len(expected) > 500) or (type(expected) is float and not math.isfinite(expected)):
                raise ValueError("Structured checks compare one JSON scalar.")

    for item in value:
        if not isinstance(item, dict) or set(item) - {"name", "aliases", "steps"}:
            raise ValueError("A workflow needs name, aliases and steps.")
        if not isinstance(item.get("name"), str) or not 1 <= len(item["name"]) <= 80:
            raise ValueError("Choose a workflow name of 1 to 80 characters.")
        names = item.get("aliases")
        if not isinstance(names, list) or not 1 <= len(names) <= 10:
            raise ValueError("Add 1 to 10 exact aliases per workflow.")
        for name in names:
            if not isinstance(name, str) or not name.strip() or len(name) > 128:
                raise ValueError("Aliases must be nonempty strings of at most 128 characters.")
            normalized = name.strip().casefold()
            if normalized in aliases or normalized.startswith("/"):
                raise ValueError("Aliases must be unique and must not start with /.")
            aliases.add(normalized)
        steps = item.get("steps")
        if not isinstance(steps, list) or not 1 <= len(steps) <= 5:
            raise ValueError("A workflow has 1 to 5 checked steps.")
        for step in steps:
            if not isinstance(step, dict) or set(step) - {"call", "before", "after", "timeoutMs"}:
                raise ValueError("A step needs call, after, optional before and timeoutMs.")
            call_valid(step.get("call"))
            check_valid(step.get("after"))
            if "before" in step:
                check_valid(step["before"])
            timeout = step.get("timeoutMs", 5000)
            if type(timeout) is not int or not 500 <= timeout <= 30000:
                raise ValueError("Step timeoutMs must be 500 to 30000.")
    return value


def match_workflow(workflows, prompt):
    normalized = prompt.strip().casefold()
    return next((item for item in workflows if any(alias.strip().casefold() == normalized for alias in item["aliases"])), None)


class WorkflowRunner(QObject):
    progress = Signal(str, int)
    finished = Signal(str, int)
    desktopEvent = Signal(str, dict)

    def __init__(self, server, profiler, parent=None):
        super().__init__(parent)
        self.server = server
        self.profiler = profiler
        self.running = False
        self._generation = 0
        self._poll = QTimer(self)
        self._poll.setSingleShot(True)
        self._poll.timeout.connect(self._poll_again)

    def start(self, definition, thread_id):
        self._generation += 1
        self.definition, self.thread_id = definition, thread_id
        self.index = 0
        self.running = True
        self._step()

    def cancel(self):
        self._generation += 1
        self._poll.stop()
        self.running = False

    def _finish(self, error=""):
        self.running = False
        self._poll.stop()
        self.finished.emit(error, self.index)

    def _call(self, call, callback, timeout_ms=30000):
        generation = self._generation
        item_id = f"workflow-{generation}-{time.monotonic_ns()}"
        self.profiler.tool_start(item_id, call["tool"])
        item = {'type': 'mcpToolCall', 'id': item_id, **call}
        self.desktopEvent.emit('item/started', item)

        def returned(result, error):
            if generation != self._generation or not self.running:
                return
            self.desktopEvent.emit('item/completed', item)
            self.profiler.tool_end(item_id)
            if not error and isinstance(result, dict) and result.get("isError"):
                detail = "\n".join(str(x.get("text", "")) for x in (result.get("content") or [])
                                   if isinstance(x, dict) and x.get("type") == "text")[:1000]
                error = "Desktop MCP refused or failed the action: " + (detail or "Check permissions and current state.")
            if error:
                if "timed out" in error:
                    # Direct MCP calls have no per-call interrupt in this protocol.
                    # End the owned connection before allowing another task's input.
                    self.server.close()
                self._finish(error)
                return
            callback(result)

        self.server.request("mcpServer/tool/call", {"threadId": self.thread_id, **call}, returned, timeout_ms)

    def _step(self):
        if self.index == len(self.definition["steps"]):
            self._finish()
            return
        step = self.definition["steps"][self.index]
        self.progress.emit(f"{self.definition['name']} / step {self.index + 1}", self.index)
        if "before" in step:
            self._call(step["before"]["call"], lambda result: self._before(result, step))
        else:
            self._act(step)

    @staticmethod
    def _matches(result, check):
        if not isinstance(result, dict):
            return False
        # Images and opaque metadata are excluded: only structured data/text.
        content = [item.get("text", "") for item in (result.get("content") or [])
                   if isinstance(item, dict) and item.get("type") == "text"]
        structured = result.get("structuredContent")
        if "contains" in check:
            text = "\n".join(content) + (json.dumps(structured, ensure_ascii=False) if structured is not None else "")
            return check["contains"] in text
        if structured is None and len(content) == 1:
            try:
                structured = json.loads(content[0])
            except ValueError:
                return False
        try:
            for key in check["path"]:
                structured = structured[key]
        except (TypeError, KeyError, IndexError):
            return False
        return type(structured) is type(check["equals"]) and structured == check["equals"]

    def _before(self, result, step):
        if not self._matches(result, step["before"]):
            self._finish("Precondition changed. Remaining steps were not executed.")
            return
        self._act(step)

    def _act(self, step):
        self._call(step["call"], lambda result: self._verify_start(step))

    def _verify_start(self, step):
        self._deadline = time.monotonic() + step.get("timeoutMs", 5000) / 1000
        self._check = step["after"]
        self._poll_again()

    def _poll_again(self):
        if self.running:
            remaining = int((self._deadline - time.monotonic()) * 1000)
            if remaining <= 0:
                self._finish("Result was not verified before the deadline. Inspect before retrying; completed actions are not undone.")
            else:
                self._call(self._check["call"], self._verified, remaining)

    def _verified(self, result):
        if self._matches(result, self._check):
            self.index += 1
            self.progress.emit("Verified step " + str(self.index), self.index)
            self._step()
        elif time.monotonic() >= self._deadline:
            self._finish("Result was not verified before the deadline. Inspect before retrying; completed actions are not undone.")
        else:
            self._poll.start(250)
