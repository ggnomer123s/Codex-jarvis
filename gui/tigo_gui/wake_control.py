"""Qt owner for the opt-in background microphone worker."""
import json
from pathlib import Path
import sys
import time
import uuid

from PySide6.QtCore import QObject, Property, QProcess, QTimer, Signal, Slot

from .autostart import set_autostart
from .preferences import LANGUAGES, valid_voice_model
from .voice import dependencies_available


def saved_bool(settings, key, default=False):
    return str(settings.value(key, default)).lower() == 'true'


class WakeControl(QObject):
    changed = Signal()
    activated = Signal()

    def __init__(self, settings, parent=None, *, command=None, register=None):
        super().__init__(parent)
        self.settings = settings
        python = Path(sys.executable)
        if sys.platform == 'win32' and python.with_name('python.exe').is_file():
            python = python.with_name('python.exe')
        self.command = command or [str(python), '-u', '-m', 'tigo_gui.wake']
        self.register = register or set_autostart
        self._enabled = saved_bool(settings, 'wake/enabled')
        self._autostart = saved_bool(settings, 'wake/autostart', True)
        self._fuzzy = saved_bool(settings, 'wake/fuzzy', True)
        self._provider = str(settings.value('wake/provider', 'local'))
        if self._provider not in ('local','online'):
            self._provider = 'local'
        self._record_after = saved_bool(settings, 'wake/recordAfterWake')
        self._model = str(settings.value('wake/model', 'base'))
        self._language = str(settings.value('wake/language', settings.value('language', 'auto')))
        self._microphone = str(settings.value('wake/microphone', settings.value('microphone', '')))
        self._off_message = 'Voice activation is off. Microphone is not listening.'
        self._state, self._status = 'off', self._off_message
        self._suspended = self._closing = self._restart = False
        self._pause_token = ''
        self._callbacks = []
        self._buffer = b''
        self._last_wake = -8.0
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.readyReadStandardError.connect(lambda: self.process.readAllStandardError())
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.pause_timer = QTimer(self)
        self.pause_timer.setSingleShot(True)
        self.pause_timer.setInterval(1500)
        self.pause_timer.timeout.connect(self._pause_timeout)

    @Property(bool, notify=changed)
    def enabled(self): return self._enabled

    @Property(bool, notify=changed)
    def autostart(self): return self._autostart

    @Property(bool, notify=changed)
    def fuzzy(self): return self._fuzzy

    @Property(str, notify=changed)
    def provider(self): return self._provider

    @Property(bool, notify=changed)
    def recordAfterWake(self): return self._record_after

    @Property(str, notify=changed)
    def model(self): return self._model

    @Property(str, notify=changed)
    def language(self): return self._language

    @Property(str, notify=changed)
    def microphone(self): return self._microphone

    @Property(str, notify=changed)
    def state(self): return self._state

    @Property(str, notify=changed)
    def status(self): return self._status

    def _set_status(self, state, text):
        self._state, self._status = state, text
        self.changed.emit()

    @Slot(bool, bool, str, str, str, bool, str, bool, result=bool)
    @Slot(bool, bool, str, str, str, bool, result=bool)
    def configure(self, enabled, autostart, model, language, microphone, fuzzy, provider=None, record_after=None):
        removal_error = ''
        provider = self._provider if provider is None else provider
        record_after = self._record_after if record_after is None else record_after
        try:
            if provider not in ('local','online') or type(record_after) is not bool:
                raise ValueError('Choose a supported wake provider.')
            if enabled and provider == 'online' and language == 'auto':
                raise ValueError('Select a wake language for online listening. Auto detect is local-only.')
            if enabled and (not valid_voice_model(model) or language not in dict(LANGUAGES) or len(microphone) > 200):
                raise ValueError('Choose a multilingual model, supported language and microphone.')
            if enabled and not (dependencies_available() if provider == "local" else dependencies_available("online")):
                raise ValueError('Install voice dependencies using the voice-enabled Tigo launcher.')
            self.register(enabled and autostart)
        except (OSError, ValueError, ImportError) as exc:
            if enabled:
                self._set_status('error', str(exc))
                return False
            # Turning the mic off must succeed even if startup cleanup fails.
            removal_error = ' Startup cleanup needs attention: ' + str(exc)
        self._off_message = 'Voice activation is off. Microphone is not listening.' + removal_error
        self._enabled, self._autostart, self._fuzzy = enabled, autostart, fuzzy
        self._provider, self._record_after = provider, record_after
        self._model, self._language, self._microphone = model, language, microphone
        for key, value in dict(enabled=enabled, autostart=autostart, fuzzy=fuzzy, model=model,
                               language=language, microphone=microphone, provider=provider, recordAfterWake=record_after).items():
            self.settings.setValue('wake/' + key, value)
        self.settings.sync()
        self._restart = enabled and not self._suspended
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
        elif enabled:
            self.start()
        else:
            self._set_status('off', self._off_message)
        self.changed.emit()
        return True

    @Slot()
    def disable(self):
        self.configure(False, self._autostart, self._model, self._language, self._microphone, self._fuzzy)

    def start(self):
        if not self._enabled or self._closing or self._suspended or self.process.state() != QProcess.NotRunning:
            return
        if not valid_voice_model(self._model) or self._language not in dict(LANGUAGES) or (self._provider == 'online' and self._language == 'auto'):
            self._set_status('error', 'Saved voice activation settings are invalid. Apply settings again.')
            return
        self._buffer = b''
        self._restart = False
        self._set_status('loading', 'Preparing local wake model; first use may download model files.' if self._provider == 'local' else 'Preparing online wake listener; speech phrases will be sent to Google.')
        args = [*self.command[1:], '--model', self._model, '--language', self._language,
                '--microphone', self._microphone, '--provider', self._provider]
        if not self._fuzzy:
            args.append('--exact')
        self.process.start(self.command[0], args)

    def _write(self, command, **values):
        if self.process.state() == QProcess.Running:
            self.process.write((json.dumps({'command': command, **values}) + '\n').encode())

    def reserve_microphone(self, callback):
        self._suspended = True
        if self.process.state() == QProcess.NotRunning or self._state == 'paused':
            callback()
            return
        if callback not in self._callbacks:
            self._callbacks.append(callback)
        if not self._pause_token:
            self._pause_token = str(uuid.uuid4())
            self._write('pause', token=self._pause_token)
            self.pause_timer.start()

    def set_suspended(self, value):
        if value == self._suspended:
            return
        self._suspended = value
        if value:
            self.reserve_microphone(lambda: None)
        else:
            self.pause_timer.stop()
            self._pause_token = ''
            self._callbacks.clear()
            if self._enabled and not self._closing:
                if self.process.state() == QProcess.Running:
                    self._write('resume')
                elif self.process.state() == QProcess.NotRunning:
                    self.start()

    def _release(self):
        self.pause_timer.stop()
        callbacks, self._callbacks = self._callbacks, []
        for callback in callbacks:
            callback()

    def _pause_timeout(self):
        # A stalled model load must not keep the manual microphone blocked.
        # Process exit is the release acknowledgement in this fallback.
        self._restart = self._enabled
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
        else:
            self._set_status('paused', 'Wake microphone paused for voice interaction.')
            self._release()

    def _read(self):
        self._buffer += bytes(self.process.readAllStandardOutput())
        if len(self._buffer) > 65536:
            self._set_status('error', 'Wake worker sent an oversized event.')
            self.process.kill()
            return
        while b'\n' in self._buffer:
            line, self._buffer = self._buffer.split(b'\n', 1)
            try:
                value = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(value, dict) or self._closing or not self._enabled:
                continue
            kind = value.get('type')
            if kind == 'wake' and not self._suspended and self._state == 'listening':
                now = time.monotonic()
                if now - self._last_wake >= 8:
                    self._last_wake = now
                    self.activated.emit()
            elif kind == 'listening':
                if not self._suspended:
                    self._set_status('listening', 'Microphone on: listening locally for the Tigo name.' if self._provider == 'local' else 'Microphone on: speech phrases sent to Google to recognize Tigo.')
                elif self._pause_token:
                    self._write('pause', token=self._pause_token)
            elif kind == 'paused' and value.get('token') == self._pause_token:
                self._set_status('paused', 'Wake microphone paused for voice interaction.')
                self._release()
            elif kind == 'error':
                self._set_status('error', str(value.get('message', 'Voice activation unavailable.'))[:500])
            elif kind == 'behind' and not self._suspended:
                self._set_status('listening', 'Listening, but CPU is behind and phrases were skipped. Try the tiny model.')

    def _finished(self, *args):
        self._read()
        self._pause_token = ''
        if not self._enabled:
            self._set_status('off', self._off_message)
            self._release()
        elif self._suspended:
            self._set_status('paused', 'Wake microphone paused for voice interaction.')
            self._release()
        elif self._restart and not self._closing:
            self.start()
        elif not self._closing and self._state != 'error':
            self._set_status('error', 'Wake listener stopped. Check microphone/model and apply settings to retry.')

    def _error(self, error):
        if error == QProcess.FailedToStart:
            self._set_status('error', 'Could not start the wake listener: ' + self.process.errorString())
            self._release()

    def shutdown(self):
        self._closing = True
        self._callbacks.clear()
        self.pause_timer.stop()
        if self.process.state() != QProcess.NotRunning:
            self._write('shutdown')
            if not self.process.waitForFinished(300):
                self.process.kill()
                self.process.waitForFinished(1000)
