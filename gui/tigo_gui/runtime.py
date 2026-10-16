"""Content-free timings and workspace/profile-scoped conversation checkpoints."""
from __future__ import annotations

import hashlib
import json
import time
import uuid


class Profiler:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.history = []
        self.current = None
        self._tools = {}
        self.voice = {}

    def begin(self, kind):
        self.current = {"id": str(uuid.uuid4()), "kind": kind, "status": "running",
                        "stagesMs": {}, "toolCount": 0, "screenshotCount": 0,
                        "tools": [], "startedAt": int(time.time())}
        self._started = self.clock()
        self._tools = {}

    def mark(self, name):
        if self.current and name not in self.current["stagesMs"]:
            self.current["stagesMs"][name] = round((self.clock() - self._started) * 1000, 1)

    def tool_start(self, item_id, name):
        if not self.current or item_id in self._tools:
            return
        self._tools[item_id] = (self.clock(), name[:100])
        self.current["toolCount"] += 1
        if any(word in name.casefold() for word in ("screenshot", "snapshot", "zoom")):
            self.current["screenshotCount"] += 1

    def tool_end(self, item_id):
        entry = self._tools.pop(item_id, None)
        if entry and self.current and len(self.current["tools"]) < 100:
            self.current["tools"].append({"name": entry[1], "durationMs": round((self.clock() - entry[0]) * 1000, 1)})

    def finish(self, status):
        if not self.current:
            return
        self.current["status"] = status
        self.current["durationMs"] = round((self.clock() - self._started) * 1000, 1)
        self.history.append(self.current)
        self.history = self.history[-30:]
        self.current = None
        self._tools = {}

    def summary(self):
        value = self.current or (self.history[-1] if self.history else None)
        if not value:
            return "No tasks measured yet"
        duration = (self.clock() - self._started) * 1000 if self.current else value["durationMs"]
        first = value["stagesMs"].get("firstText")
        extra = f" / first text {first / 1000:.1f}s" if first is not None else ""
        return f"{value['kind']} / {duration / 1000:.1f}s / {value['toolCount']} tools{extra}"

    def export(self):
        # No prompts, responses, arguments, screenshots, recordings or credentials.
        return {"version": 1, "tasks": self.history, "voice": self.voice}


class Checkpoints:
    def __init__(self, settings):
        self.settings = settings
        try:
            value = json.loads(str(settings.value("threadCheckpoints", "{}")))
        except (ValueError, TypeError):
            value = {}
        self.entries = value if isinstance(value, dict) else {}

    @staticmethod
    def key(home, folder, access, model):
        return hashlib.sha256(json.dumps([str(home.resolve()), str(folder.resolve()), access, model]).encode()).hexdigest()

    def get(self, key):
        value = self.entries.get(key, {})
        return value if isinstance(value, dict) and isinstance(value.get("threadId"), str) else {}

    def save(self, key, thread_id, status, completed_steps=0):
        if not thread_id:
            return
        self.entries.pop(key, None)
        self.entries[key] = {"threadId": thread_id, "status": status, "completedSteps": completed_steps,
                             "updatedAt": int(time.time())}
        self.entries = dict(list(self.entries.items())[-30:])
        self.settings.setValue("threadCheckpoints", json.dumps(self.entries))

    def forget(self, key):
        self.entries.pop(key, None)
        self.settings.setValue("threadCheckpoints", json.dumps(self.entries))
