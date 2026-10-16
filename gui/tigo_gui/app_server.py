"""Owned, persistent Codex app-server transport over local newline JSON-RPC.

No shared daemon, HTTP port, shell interpolation or exec fallback. Callbacks are
invalidated at process boundaries; thread/turn scoping is handled by the owner.
"""
from __future__ import annotations

import json
import os
import signal
import time

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

MAX_RECORD = 8 * 1024 * 1024
MAX_PENDING = 64


def terminate_tree(process):
    pid = process.processId()
    if not pid:
        return
    if os.name == "nt":
        # Retain this helper until taskkill has exited; target only our PID tree.
        killer = QProcess(process)
        killer.finished.connect(killer.deleteLater)
        killer.start("taskkill", ["/PID", str(pid), "/T", "/F"])
        killer.waitForFinished(1000)
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.kill()


class AppServer(QObject):
    ready = Signal()
    notification = Signal(str, dict)
    failed = Signal(str)
    disconnected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        if os.name != "nt":
            self.process.setUnixProcessParameters(QProcess.UnixProcessFlag.CreateNewSession)
        self.process.started.connect(self._initialize)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.readyReadStandardError.connect(self._read_error)
        self.process.finished.connect(self._exited)
        self.process.errorOccurred.connect(self._process_error)
        self.connected = False
        self._closing = False
        self._buffer = b""
        self._stderr = b""
        self._next_id = 0
        self._pending = {}
        self._generation = 0
        self._failure_reported = False
        self._expiry = QTimer(self)
        self._expiry.setInterval(250)
        self._expiry.timeout.connect(self._expire)

    def start(self, program, arguments, environment, cwd):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        self._closing = False
        self._failure_reported = False
        self.connected = False
        self._buffer = self._stderr = b""
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(cwd)
        self.process.start(program, arguments)
        self._expiry.start()

    def _initialize(self):
        if self._closing:
            return
        self.request("initialize", {"clientInfo": {"name": "tigo_desktop", "title": "Tigo", "version": "0.10.0"},
                                    "capabilities": {"experimentalApi": False}}, self._initialized)

    def _initialized(self, result, error):
        if error:
            self._fatal("Codex app-server initialization failed: " + error)
            return
        self.notify("initialized", {})
        self.connected = True
        self.ready.emit()

    def _write(self, value):
        data = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
        if len(data) > MAX_RECORD or self.process.bytesToWrite() + len(data) > MAX_RECORD:
            raise ValueError("Codex request queue is full or the request is too large.")
        if self.process.write(data) < 0:
            raise ValueError("Codex app-server is disconnected.")

    def request(self, method, params, callback, timeout_ms=30000):
        if self._closing or self.process.state() != QProcess.ProcessState.Running:
            callback(None, "Codex app-server is not running.")
            return None
        if len(self._pending) >= MAX_PENDING:
            callback(None, "Too many pending Codex requests.")
            return None
        self._next_id += 1
        request_id = self._next_id
        self._pending[request_id] = (time.monotonic() + timeout_ms / 1000, callback)
        try:
            self._write({"id": request_id, "method": method, "params": params})
        except ValueError as exc:
            self._pending.pop(request_id, None)
            callback(None, str(exc))
        return request_id

    def notify(self, method, params):
        self._write({"method": method, "params": params})

    def _read_error(self):
        self._stderr = (self._stderr + bytes(self.process.readAllStandardError()))[-4000:]

    def _read(self):
        self._buffer += bytes(self.process.readAllStandardOutput())
        if len(self._buffer) > MAX_RECORD and b"\n" not in self._buffer:
            self._fatal("Codex app-server sent an oversized JSON record.")
            return
        while b"\n" in self._buffer:
            line, self._buffer = self._buffer.split(b"\n", 1)
            if len(line) > MAX_RECORD:
                self._fatal("Codex app-server sent an oversized JSON record.")
                return
            try:
                value = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(value, dict):
                continue
            if "method" in value:
                if "id" in value:
                    self._server_request(value)
                elif isinstance(value.get("params", {}), dict):
                    self.notification.emit(value["method"], value.get("params", {}))
            elif type(value.get("id")) in (int, str):
                entry = self._pending.pop(value["id"], None)
                if entry:
                    error = value.get("error")
                    message = str(error.get("message", "Codex request failed.")) if isinstance(error, dict) else None
                    entry[1](value.get("result"), message)

    def _server_request(self, value):
        # GUI access policies are never: no invisible prompt and no implicit grant.
        method = value["method"]
        responses = {
            "item/commandExecution/requestApproval": {"decision": "decline"},
            "item/fileChange/requestApproval": {"decision": "decline"},
            "mcpServer/elicitation/request": {"action": "decline", "content": None},
            "item/permissions/requestApproval": {"permissions": {}, "scope": "turn"},
            "item/tool/requestUserInput": {"answers": {}},
        }
        result = responses.get(method)
        response = {"id": value["id"]}
        if result is None:
            response["error"] = {"code": -32601, "message": "This request is not supported by Tigo."}
        else:
            response["result"] = result
        self._write(response)
        self.notification.emit("tigo/requestDeclined", {"method": method})

    def _expire(self):
        now = time.monotonic()
        expired = [key for key, (deadline, _) in self._pending.items() if deadline <= now]
        for key in expired:
            entry = self._pending.pop(key, None)
            if entry:
                entry[1](None, "Codex request timed out. Its outcome may be unknown; check before retrying.")

    def _fatal(self, message):
        self.close()
        self._report_failure(message)

    def _report_failure(self, message):
        if not self._failure_reported:
            self._failure_reported = True
            self.failed.emit(message)

    def _exited(self, code, status):
        self._read_error()
        was_closing = self._closing
        self.connected = False
        self._expiry.stop()
        self.disconnected.emit()
        pending, self._pending = self._pending, {}
        for _, callback in pending.values():
            callback(None, "Codex app-server disconnected.")
        if not was_closing:
            detail = self._stderr.decode("utf-8", errors="replace").strip()[-1500:]
            self._report_failure(detail or f"Codex app-server exited ({code}). Update Codex if app-server is unavailable.")

    def _process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._fatal("Could not start Codex app-server: " + self.process.errorString())

    def close(self):
        self._closing = True
        self._generation += 1
        self.connected = False
        self._expiry.stop()
        self._pending.clear()
        self._buffer = b""
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.closeWriteChannel()
            if not self.process.waitForFinished(300):
                terminate_tree(self.process)
                self.process.waitForFinished(1000)
