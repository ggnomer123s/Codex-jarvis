"""Qt bridge: asynchronous Codex sessions and isolated push-to-talk voice."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import sys

from PySide6.QtCore import QObject, Property, QProcess, QSettings, QTimer, Signal, Slot
from PySide6.QtWidgets import QFileDialog

from .core import build_arguments, find_codex, launch_command, parse_event
from .voice import dependencies_available


class Backend(QObject):
    changed = Signal()
    messagesChanged = Signal()
    transcriptReady = Signal(str)

    def __init__(self, settings: QSettings | None = None, *, codex_command=None, voice_command=None):
        super().__init__()
        self.settings = settings or QSettings("Jarvis", "Desktop")
        saved_folder = str(self.settings.value("folder", str(Path.home())))
        self._folder = saved_folder if Path(saved_folder).is_dir() else str(Path.home())
        self._effort = str(self.settings.value("effort", "low"))
        self._access = str(self.settings.value("access", "read-only"))
        if self._effort not in ("low", "default", "high"):
            self._effort = "low"
        if self._access not in ("read-only", "workspace-write"):
            self._access = "read-only"
        self._codex = os.environ.get("JARVIS_GUI_CODEX") or find_codex() or ""
        self._codex_command = codex_command
        worker_python = str(Path(sys.executable).with_name("python.exe")) if os.name == "nt" else sys.executable
        self._voice_command = voice_command or [worker_python, "-u", "-m", "jarvis_gui.voice"]
        if codex_command:
            self._codex = codex_command[0]
        self._busy = False
        self._voice_state = "idle"
        self._level = 0.0
        self._activity = "Ready when you are" if self._codex else "Install Codex CLI to connect"
        self._messages = []
        self._thread_id = ""
        self._cancelled = False
        self._failed = False
        self._got_answer = False
        self._voice_cancelled = False
        self._voice_result = False
        self._voice_stop_requested = False
        self._stdout = b""
        self._voice_buffer = b""
        self._stderr = b""
        self.process = QProcess(self)
        if os.name != "nt":
            self.process.setUnixProcessParameters(QProcess.UnixProcessFlag.CreateNewSession)
        self.process.started.connect(self._send_prompt)
        self.process.readyReadStandardOutput.connect(self._read_codex)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        self.voice = QProcess(self)
        self.voice.started.connect(self._voice_started)
        self.voice.readyReadStandardOutput.connect(self._read_voice)
        self.voice.readyReadStandardError.connect(lambda: self.voice.readAllStandardError())
        self.voice.finished.connect(self._voice_finished)
        self.voice.errorOccurred.connect(self._voice_error)
        self._kill_timer = QTimer(self)
        self._kill_timer.setSingleShot(True)
        self._kill_timer.timeout.connect(self._force_stop)

    @Property("QVariantList", notify=messagesChanged)
    def messages(self):
        return self._messages

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def activity(self):
        return self._activity

    @Property(str, notify=changed)
    def folder(self):
        return self._folder

    @Property(str, notify=changed)
    def effort(self):
        return self._effort

    @Property(str, notify=changed)
    def access(self):
        return self._access

    @Property(bool, notify=changed)
    def codexAvailable(self):
        return bool(self._codex)

    @Property(bool, notify=changed)
    def voiceAvailable(self):
        return dependencies_available()

    @Property(str, notify=changed)
    def voiceState(self):
        return self._voice_state

    @Property(float, notify=changed)
    def audioLevel(self):
        return self._level

    def _message(self, role, text):
        self._messages.append({"role": role, "text": text})
        self.messagesChanged.emit()

    @Slot(str)
    def send(self, prompt):
        prompt = prompt.strip()
        if not prompt or self._busy or self._voice_state != "idle":
            return
        if not self._codex:
            self._message("error", "Codex CLI was not found. Install @openai/codex, run codex login in a terminal, then reopen JARVIS.")
            return
        try:
            args = build_arguments(self._folder, self._effort, self._access, self._thread_id)
            if self._codex_command:
                program, args = self._codex_command[0], self._codex_command[1:] + args
            else:
                program, args = launch_command(self._codex, args)
        except ValueError as exc:
            self._message("error", str(exc))
            return
        self._prompt = prompt
        self._stdout = b""
        self._stderr = b""
        self._cancelled = self._failed = self._got_answer = False
        self._busy = True
        self._activity = "Connecting to Codex"
        self._message("user", prompt)
        self.changed.emit()
        self.process.setWorkingDirectory(self._folder)
        self.process.start(program, args)

    def _send_prompt(self):
        if self._cancelled:
            self._force_stop()
            return
        self.process.write(self._prompt.encode("utf-8"))
        self.process.closeWriteChannel()

    def _read_stderr(self):
        self._stderr = (self._stderr + bytes(self.process.readAllStandardError()))[-8000:]

    def _handle_codex(self, line):
        event = parse_event(line.decode("utf-8", errors="replace"))
        if not event:
            return
        if event.kind == "thread":
            self._thread_id = event.text
        elif event.kind == "answer" and event.text:
            self._got_answer = True
            self._message("assistant", event.text)
        elif event.kind == "activity":
            self._activity = event.text
            self.changed.emit()
        elif event.kind == "error":
            self._failed = True
            self._message("error", event.text)

    def _read_codex(self):
        self._stdout += bytes(self.process.readAllStandardOutput())
        while b"\n" in self._stdout:
            line, self._stdout = self._stdout.split(b"\n", 1)
            self._handle_codex(line)

    def _finished(self, code, status):
        self._kill_timer.stop()
        self._read_codex()
        self._read_stderr()
        if self._stdout.strip():
            self._handle_codex(self._stdout)
        self._stdout = b""
        if self._cancelled:
            self._message("system", "Task stopped. Actions already completed have not been undone.")
        elif code != 0 and not self._failed:
            detail = self._stderr.decode("utf-8", errors="replace").strip()
            self._message("error", detail[-2000:] or f"Codex exited with code {code}.")
        elif code == 0 and not self._failed and not self._got_answer:
            self._message("system", "Codex finished without a text response. Check the task result before continuing.")
        self._busy = False
        self._activity = "Task stopped" if self._cancelled else ("Request failed" if self._failed or code else "Ready when you are")
        self.changed.emit()

    def _process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._busy = False
            self._activity = "Could not start Codex"
            self._message("error", self.process.errorString())
            self.changed.emit()

    @Slot()
    def stop(self):
        if not self._busy:
            return
        self._cancelled = True
        self._activity = "Stopping task"
        pid = self.process.processId()
        if pid:
            if os.name == "nt":
                # Kill only the task process tree, including its MCP children.
                killer = QProcess(self)
                killer.finished.connect(killer.deleteLater)
                killer.start("taskkill", ["/PID", str(pid), "/T", "/F"])
            else:
                try:
                    os.killpg(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        self._kill_timer.start(1500)
        self.changed.emit()

    def _force_stop(self):
        pid = self.process.processId()
        if pid and os.name != "nt":
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.process.kill()

    @Slot()
    def newSession(self):
        if self._busy or self._voice_state != "idle":
            return
        self._thread_id = ""
        self._messages = []
        self._activity = "Ready when you are"
        self.messagesChanged.emit()
        self.changed.emit()

    @Slot()
    def chooseFolder(self):
        if self._busy or self._voice_state != "idle":
            return
        folder = QFileDialog.getExistingDirectory(None, "Choose your workspace", self._folder)
        if folder and folder != self._folder:
            self._folder = folder
            self.settings.setValue("folder", folder)
            self.newSession()

    @Slot(str, str)
    def configure(self, effort, access):
        if self._busy or self._voice_state != "idle":
            return
        try:
            build_arguments(self._folder, effort, access)
        except ValueError:
            return
        if access != self._access:
            # Start a fresh context when permissions change.
            self.newSession()
        self._effort, self._access = effort, access
        self.settings.setValue("effort", effort)
        self.settings.setValue("access", access)
        self.changed.emit()

    @Slot()
    def toggleVoice(self):
        if self._busy:
            return
        if self._voice_state in ("starting", "recording"):
            self._voice_stop_requested = True
            if self.voice.state() == QProcess.ProcessState.Running:
                self.voice.write(b"stop\n")
            self._voice_state = "transcribing"
            self._activity = "Transcribing locally"
        elif self._voice_state == "idle":
            if not self.voiceAvailable:
                self._message("error", "Voice packages are missing. Use the voice-enabled launcher described in docs/desktop-app.md.")
                return
            self._voice_buffer = b""
            self._voice_result = self._voice_cancelled = False
            self._voice_stop_requested = False
            self._voice_state = "starting"
            self._activity = "Opening microphone"
            self.voice.start(self._voice_command[0], self._voice_command[1:])
        self.changed.emit()

    def _voice_started(self):
        if self._voice_stop_requested:
            self.voice.write(b"stop\n")

    @Slot()
    def cancelVoice(self):
        self._voice_cancelled = True
        self.voice.kill()

    def _read_voice(self):
        self._voice_buffer += bytes(self.voice.readAllStandardOutput())
        while b"\n" in self._voice_buffer:
            line, self._voice_buffer = self._voice_buffer.split(b"\n", 1)
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if self._voice_cancelled:
                continue
            kind = event.get("type")
            if kind == "recording" and self._voice_state == "starting":
                self._voice_state = "recording"
                self._activity = "Listening - click microphone to finish"
            elif kind == "transcribing":
                self._voice_state = "transcribing"
                self._activity = "Transcribing locally - first use downloads a model"
            elif kind == "level":
                self._level = float(event.get("value", 0))
            elif kind == "transcript":
                self._voice_result = True
                self.transcriptReady.emit(str(event.get("text", "")))
                self._activity = "Review your transcript, then press Send"
            elif kind == "error":
                self._voice_result = True
                self._message("error", str(event.get("message", "Voice failed.")))
                self._activity = "Voice unavailable"
            self.changed.emit()

    def _voice_finished(self, code, status):
        self._read_voice()
        if self._voice_cancelled:
            self._activity = "Voice cancelled"
        elif not self._voice_result:
            self._activity = "Voice unavailable"
            self._message("error", "Voice worker stopped before producing a transcript.")
        self._voice_state = "idle"
        self._level = 0
        self.changed.emit()

    def _voice_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._voice_state = "idle"
            self._message("error", "Could not start the voice worker: " + self.voice.errorString())
            self.changed.emit()

    @Slot()
    def shutdown(self):
        if self._busy:
            self.stop()
            if not self.process.waitForFinished(1800):
                self._force_stop()
                self.process.waitForFinished(1000)
        if self.voice.state() != QProcess.ProcessState.NotRunning:
            self._voice_cancelled = True
            self.voice.kill()
            self.voice.waitForFinished(1000)
