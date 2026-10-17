"""On-demand Update Center. Checking never installs or closes the application."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

from PySide6.QtCore import QObject, Property, QProcess, QStandardPaths, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from . import __version__
from .app_server import terminate_tree


def terminal_command(command, which=shutil.which):
    for name, arguments in [('x-terminal-emulator', ['-e']), ('kitty', ['-e']),
                            ('konsole', ['-e']), ('gnome-terminal', ['--']),
                            ('xfce4-terminal', ['-x']), ('alacritty', ['-e']), ('foot', ['-e'])]:
        program = which(name)
        if program:
            return [program, *arguments, *command]
    raise ValueError('No supported terminal found. Run install.sh from a terminal; Tigo stays open.')


class Updates(QObject):
    changed = Signal()
    quitRequested = Signal()

    def __init__(self, parent=None, *, repo=None, storage=None):
        super().__init__(parent)
        self.repo = Path(repo) if repo else Path(__file__).resolve().parents[2]
        self.storage = Path(storage) if storage else Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)) / 'updates'
        self._state = 'idle'
        self._message = 'Check when you are ready. Updates are never installed automatically.'
        self._latest, self._notes, self._revision, self._local = '', '', '', ''
        self._commits = 0
        self._last = ''
        self._buffer = bytearray()
        self._action = ''
        self._bundle = None
        self._launcher = None
        self._deadline = 0
        self.process = QProcess(self)
        if sys.platform != 'win32':
            self.process.setUnixProcessParameters(QProcess.UnixProcessFlag.CreateNewSession)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.readyReadStandardError.connect(lambda: self.process.readAllStandardError())
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self._handshake = QTimer(self)
        self._handshake.setInterval(100)
        self._handshake.timeout.connect(self._ready)
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._expired)
        try:
            data = json.loads((self.storage / 'last-result.json').read_text(encoding='utf-8'))
            if isinstance(data, dict):
                self._last = str(data.get('message', ''))[:500]
        except (OSError, ValueError):
            pass

    @Property(str, constant=True)
    def currentVersion(self): return __version__
    @Property(str, notify=changed)
    def state(self): return self._state
    @Property(str, notify=changed)
    def message(self): return self._message
    @Property(str, notify=changed)
    def latestVersion(self): return self._latest
    @Property(str, notify=changed)
    def notes(self): return self._notes
    @Property(str, notify=changed)
    def revision(self): return self._revision[:12]
    @Property(int, notify=changed)
    def commits(self): return self._commits
    @Property(str, notify=changed)
    def lastResult(self): return self._last
    @Property(bool, notify=changed)
    def busy(self): return self._state in ('checking', 'preparing', 'launching')
    @Property(bool, notify=changed)
    def installing(self): return self._state in ('preparing', 'launching')

    def _set(self, state, message):
        self._state, self._message = state, message
        self.changed.emit()

    @Slot()
    def check(self):
        if not self.busy:
            self._set('checking', 'Checking the official main branch...')
            self._start('check')

    def _start(self, action, extra=()):
        self._action = action
        self._buffer.clear()
        self.process.start(sys.executable, ['-u', '-m', 'tigo_gui.update_worker', action,
                                           '--repo', str(self.repo), *extra])
        self._timeout.start(180_000)

    def _read(self):
        self._buffer.extend(bytes(self.process.readAllStandardOutput()))
        if len(self._buffer) > 64_000:
            self._action = ''
            self.process.kill()
            self._set('error', 'The update response was too large.')

    def _finished(self, code, status):
        self._timeout.stop()
        self._read()
        action, self._action = self._action, ''
        if not action:
            return
        try:
            data = json.loads(self._buffer)
            if not isinstance(data, dict) or not data.get('ok') or code != 0:
                raise ValueError(str(data.get('message', 'Update inspection failed.')) if isinstance(data, dict) else 'Invalid update response.')
            if action == 'check':
                self._latest, self._notes = data['version'], data['notes']
                self._revision, self._local, self._commits = data['revision'], data['local'], data['commits']
                self._set(data['state'], data['message'])
            else:
                self._launch(Path(data['bundle']))
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
            self._set('error', str(exc)[:500])

    def _error(self, error):
        if error == QProcess.FailedToStart:
            self._timeout.stop()
            self._action = ''
            self._set('error', 'Could not start the update checker.')

    def _expired(self):
        self._action = ''
        self._stop_worker()
        self._set('error', 'Update check timed out. No installation was started.')

    @Slot()
    def cancel(self):
        if self._state in ('checking', 'preparing'):
            self._action = ''
            self._timeout.stop()
            self._stop_worker()
            self._set('idle', 'Check cancelled. No installation was started.')

    def install(self):
        if self._state != 'available' or not self._revision:
            return
        self._set('preparing', 'Preparing the reviewed installer. Tigo is still open.')
        try:
            self.storage.mkdir(parents=True, exist_ok=True, mode=0o700)
            self._bundle = self.storage / str(uuid.uuid4())
            self._start('prepare', ['--revision', self._revision, '--bundle', str(self._bundle)])
        except OSError as exc:
            self._set('error', 'Could not prepare the updater: ' + str(exc)[:250])

    def _launch(self, bundle):
        manifest = bundle / 'manifest.json'
        manifest.write_text(json.dumps({'repo': str(self.repo.resolve()), 'revision': self._revision,
                                        'parent': os.getpid(), 'result': str(self.storage / 'last-result.json')}), encoding='utf-8')
        # A base interpreter can survive replacing/locking the Qt venv on Windows.
        python = getattr(sys, '_base_executable', None) or str(Path(sys.executable).resolve())
        command = [python, str(bundle / 'runner.py'), '--manifest', str(manifest)]
        if sys.platform == 'win32':
            self._launcher = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=bundle)
        else:
            self._launcher = subprocess.Popen(terminal_command(command), start_new_session=True, cwd=bundle)
        self._bundle = bundle
        self._deadline = time.monotonic() + 12
        self._set('launching', 'Opening the installer terminal. Tigo will close after it is ready.')
        self._handshake.start()

    def _ready(self):
        if self._bundle and (self._bundle / 'ready').is_file():
            self._handshake.stop()
            try:
                (self._bundle / 'approved').write_text('approved', encoding='ascii')
            except OSError:
                self._set('error', 'Could not approve the installer. Tigo stays open; check free space and permissions.')
                return
            self._set('launching', 'Installer ready. Closing Tigo to release its files.')
            self.quitRequested.emit()
        elif time.monotonic() > self._deadline:
            self._handshake.stop()
            self._set('error', 'The installer terminal did not become ready. Tigo stays open; close the failed terminal and retry.')

    @Slot()
    def openHistory(self):
        if self._local and self._revision:
            QDesktopServices.openUrl(QUrl('https://github.com/ggnomer123s/Codex-jarvis/compare/' + self._local + '...' + self._revision))

    def close(self):
        self._action = ''
        self._handshake.stop()
        self._timeout.stop()
        self._stop_worker()

    def _stop_worker(self):
        if self.process.state() == QProcess.NotRunning:
            return
        if sys.platform != 'win32' and self.process.processId():
            try:
                os.killpg(self.process.processId(), signal.SIGTERM)
            except ProcessLookupError:
                pass
        if not self.process.waitForFinished(500):
            terminate_tree(self.process)
            self.process.waitForFinished(1000)
