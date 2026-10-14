"""Prepare and sign into the existing separate Full Access profile."""
import os
from pathlib import Path
import re
import signal

from PySide6.QtCore import QObject, Property, QProcess, QProcessEnvironment, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .preferences import FULL_ACKNOWLEDGEMENT, full_profile_home


class FullProfile(QObject):
    changed = Signal()
    prepared = Signal()
    error = Signal(str)

    def __init__(self, command_factory, parent=None, home=None):
        super().__init__(parent)
        self.home = Path(home) if home else full_profile_home()
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
        return (self.home / "AGENTS.md").is_file() and any(
            (self.home / name).is_file() for name in ("backend.txt", "config.toml"))

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

    def install(self):
        if self._busy:
            return
        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / ("install-full-windows.ps1" if os.name == "nt" else "install-full-linux.sh")
        if not script.is_file():
            self.error.emit("Full Access setup requires the source checkout. Install jarvis-full using docs/full-access.md, then reopen the app.")
            return
        args = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Acknowledgement", FULL_ACKNOWLEDGEMENT] if os.name == "nt" else [str(script), "--acknowledgement", FULL_ACKNOWLEDGEMENT]
        self._start("install", "powershell.exe" if os.name == "nt" else "bash", args)

    @Slot()
    def login(self):
        if self._busy:
            return
        if not self.ready:
            self.error.emit("Prepare the Full Access profile before signing in.")
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
        self._output = "Preparing separate profile..." if operation == "install" else "Starting separate device sign-in..."
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
            self.error.emit(f"Full Access {operation} failed. Check the profile log in Preferences.")
        elif operation == "install":
            if self.ready:
                self._output += "\nProfile prepared. Use Sign in if this profile is not authenticated."
                self.prepared.emit()
            else:
                self.error.emit("Installer finished without a complete Full Access profile.")
        elif operation == "login":
            self._output += "\nSeparate profile sign-in completed."
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
        self._output += "\nOperation cancelled. Any installed files remain in place."

    def shutdown(self):
        if self._busy:
            self.cancel()
            self.process.waitForFinished(1200)
