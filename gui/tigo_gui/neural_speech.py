"""Qt adapter for the neural subprocess; GUI never imports an inference engine."""
from enum import Enum
import json
import sys
from PySide6.QtCore import QLocale, QObject, QProcess, Signal
from .speech_models import VOICES


class State(Enum):
    Ready = 0
    Speaking = 1
    Error = 2


class VoiceAttribute(Enum):
    Adult = 0
    Male = 1


class NeuralVoice:
    def __init__(self, key): self.key = key
    def name(self): return VOICES[self.key]['name']
    def locale(self): return QLocale(VOICES[self.key]['locale'])
    def age(self): return VoiceAttribute.Adult
    def gender(self): return VoiceAttribute.Male


class NeuralEngine(QObject):
    stateChanged = Signal(object)
    errorOccurred = Signal(object, str)
    preparing = Signal(str)
    start_timeout = 120000

    def __init__(self, parent=None, *, command=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.command = command or [sys.executable, '-u', '-m', 'tigo_gui.neural_worker']
        self.process.started.connect(self._send)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.readyReadStandardError.connect(self._drain_error)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        self._buffer = b''
        self._stderr = ''
        self._state = State.Ready
        self._locale = QLocale('ru_RU')
        self._voice = NeuralVoice(next(iter(VOICES)))
        self._rate, self._volume = 0, .85
        self._id = 0
        self._pending = None
        self._busy = self._stopping = self._closing = False

    def locale(self): return self._locale
    def setLocale(self, locale): self._locale = locale
    def availableLocales(self): return list({v['locale']: QLocale(v['locale']) for v in VOICES.values()}.values())
    def availableVoices(self): return [NeuralVoice(k) for k, v in VOICES.items() if QLocale(v['locale']) == self._locale]
    def state(self): return self._state
    def errorString(self): return self._stderr
    def setVoice(self, voice): self._voice = voice
    def setRate(self, value): self._rate = value
    def setPitch(self, value): pass  # Preserve the trained voice's natural pitch.
    def setVolume(self, value): self._volume = value

    @property
    def is_quiet(self):
        return self.process.state() == QProcess.ProcessState.NotRunning or not (self._busy or self._stopping)

    def say(self, text):
        self._id += 1
        self._busy = True
        self._state = State.Ready
        self._pending = {'id': str(self._id), 'voice': self._voice.key, 'text': text,
                         'speed': 1 + self._rate*.3, 'volume': self._volume}
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self._start()
        elif not self._stopping and self.process.state() == QProcess.ProcessState.Running:
            self._send()

    def _start(self):
        self._stopping = False
        self._buffer, self._stderr = b'', ''
        self.process.start(self.command[0], self.command[1:])

    def _send(self):
        if self._pending is not None and not self._stopping and not self._closing:
            self.process.write((json.dumps(self._pending, ensure_ascii=False)+'\n').encode('utf-8'))
            self._pending = None

    def _read(self):
        self._buffer += bytes(self.process.readAllStandardOutput())
        if len(self._buffer) > 65536:
            self._error('The speech worker returned an oversized message.')
            return
        while b'\n' in self._buffer:
            line, self._buffer = self._buffer.split(b'\n', 1)
            try:
                event = json.loads(line)
            except (ValueError, UnicodeError):
                self._error('The speech worker returned an invalid message.')
                return
            if not isinstance(event, dict):
                self._error('The speech worker returned an invalid event.')
                return
            if self._closing or self._stopping or not self._busy or event.get('id') != str(self._id):
                continue
            kind = event.get('type')
            if kind == 'preparing':
                self.preparing.emit(str(event.get('message', 'Preparing neural speech.'))[:700])
            elif kind == 'speaking':
                self._state = State.Speaking
                self.stateChanged.emit(self._state)
            elif kind == 'done':
                self._busy = False
                self._state = State.Ready
                self.stateChanged.emit(self._state)
            elif kind == 'error':
                self._error(str(event.get('message', 'Neural speech failed.')))

    def _drain_error(self):
        self._stderr = (self._stderr + bytes(self.process.readAllStandardError()).decode('utf-8', 'replace'))[-1500:]

    def _error(self, message):
        self._stderr = message
        self._state = State.Error
        self.errorOccurred.emit(None, message + ' Check Preferences > Speech or rerun the GUI installer.')

    def _process_error(self, error):
        if not self._stopping and not self._closing:
            self._error('The neural speech process failed: ' + self.process.errorString())

    def _finished(self, code, status):
        expected = self._stopping or self._closing
        self._stopping = False
        if self._pending and not self._closing:
            self._start()
        elif not expected and self._busy:
            self._error('The neural speech process exited unexpectedly. ' + self._stderr[-400:])

    def stop(self):
        interrupt = self._busy or self._stopping
        self._id += 1
        self._pending = None
        self._busy = False
        self._state = State.Ready
        if interrupt and self.process.state() != QProcess.ProcessState.NotRunning:
            self._stopping = True
            self.process.kill()  # Cancels native inference, downloads and audio immediately.

    def shutdown(self):
        self._closing = True
        self.stop()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1500)
