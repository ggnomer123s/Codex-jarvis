"""Sign into the existing shared Codex account; access is a runtime setting."""
import os
from pathlib import Path
import re
import signal

from PySide6.QtCore import QObject, Property, QProcess, QProcessEnvironment, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .access import codex_home


class FullProfile(QObject):
    changed = Signal()
    error = Signal(str)

    def __init__(self, command_factory, parent=None, home=None):
        super().__init__(parent)
        self.home = Path(home) if home else codex_home()
        self.command_factory = command_factory
        self._busy = False
        self._operation = ""
        self._output = ""
        self.process = QProcess(self)
        if os.name != "nt":
            self.process.setUnixProcessParameters(QProcess.UnixProcessFlag.CreateNewSession)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.readyReadStandardError.connect(self._read)
        self.process.finished.connect(self._finish)
        self.process.errorOccurred.connect(self._failed)

    @Property(bool, notify=changed)
    def ready(self):
        return True

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def output(self):
        return self._output

    @Property(str, notify=changed)
    def loginUrl(self):
        match = re.search(r"https://auth\.openai\.com/[A-Za-z0-9_/?=.&%-]+", self._output)
        return match.group(0) if match else ""

    @Slot()
    def openLoginPage(self):
        if self.loginUrl:
            QDesktopServices.openUrl(QUrl(self.loginUrl))

    @Slot()
    def login(self):
        if self._busy:
            return
        try:
            program, args = self.command_factory(["login", "--device-auth"])
        except ValueError as exc:
            self.error.emit(str(exc))
            return
        self._start("login", program, args)

    def _start(self, operation, program, args):
        self._operation = operation
        self._busy = True
        self._output = "Starting Codex device sign-in..."
        environment = QProcessEnvironment.systemEnvironment()
        if operation == "login":
            environment.insert("CODEX_HOME", str(self.home))
        self.process.setProcessEnvironment(environment)
        self.changed.emit()
        self.process.start(program, args)

    def _read(self):
        data = bytes(self.process.readAllStandardOutput()) + bytes(self.process.readAllStandardError())
        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", data.decode("utf-8", errors="replace"))
        self._output = (self._output + "\n" + text)[-5000:]
        self.changed.emit()

    def _finish(self, code, status):
        self._read()
        self._busy = False
        operation = self._operation
        self._operation = ""
        if operation and code != 0:
            self.error.emit(f"Codex {operation} failed. Check the account log in Preferences.")
        elif operation == "login":
            self._output += "\nCodex sign-in completed."
        self.changed.emit()

    def _failed(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self._busy = False
            self._operation = ""
            self._output = self.process.errorString()
            self.error.emit(self._output)
            self.changed.emit()

    @Slot()
    def cancel(self):
        if not self._busy:
            return
        self._operation = ""
        pid = self.process.processId()
        if pid and os.name != "nt":
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif pid:
            killer = QProcess(self)
            killer.finished.connect(killer.deleteLater)
            killer.start("taskkill", ["/PID", str(pid), "/T", "/F"])
        self.process.kill()
        self._output += "\nSign-in cancelled."

    def shutdown(self):
        if self._busy:
            self.cancel()
            self.process.waitForFinished(1200)
