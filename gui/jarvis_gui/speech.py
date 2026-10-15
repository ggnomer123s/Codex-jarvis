"""Local OS text-to-speech, with explicit cancellation and microphone handoff."""
import math
import re
import sys
from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
from PySide6.QtTextToSpeech import QTextToSpeech, QVoice
from .speech_text import spoken_text


def native_engine(parent):
    available = QTextToSpeech.availableEngines()
    preferred = ('winrt', 'sapi') if sys.platform == 'win32' else ('speechd', 'flite')
    for name in preferred:
        if name in available:
            engine = QTextToSpeech(name, parent)
            if engine.state() != QTextToSpeech.State.Error and (engine.availableLocales() or engine.availableVoices()):
                return engine
            engine.deleteLater()
    raise ValueError('No local speech engine is ready. Windows: install a system speech voice. Linux: install speech-dispatcher and espeak-ng, then restart JARVIS.')


def saved_number(settings, key, default, low, high):
    try:
        value = float(settings.value('speech/' + key, default))
        return max(low, min(high, value)) if math.isfinite(value) else default
    except (ValueError, TypeError):
        return default


class Speech(QObject):
    changed = Signal()

    def __init__(self, settings, parent=None, *, prepare=None, engine_factory=None):
        super().__init__(parent)
        self.settings = settings
        self.prepare = prepare or (lambda callback: callback())
        self.factory = engine_factory or native_engine
        self._enabled = str(settings.value('speech/enabled', True)).lower() == 'true'
        self._voice_id = str(settings.value('speech/voice', ''))
        self._rate = saved_number(settings, 'rate', -.05, -1, 1)
        self._pitch = saved_number(settings, 'pitch', -.12, -1, 1)
        self._volume = saved_number(settings, 'volume', .85, 0, 1)
        self._engine = None
        self._voices = {}
        self._active = self._started = self._closing = self._ignore_state = False
        self._generation = 0
        self._state = 'idle'
        self._status = 'Local speech is ready to initialize. Voices depend on your system.'
        self._quiet_callbacks = []
        self.quiet_timer = QTimer(self)
        self.quiet_timer.setSingleShot(True)
        self.quiet_timer.setInterval(300)
        self.quiet_timer.timeout.connect(self._quiet)
        self.start_timer = QTimer(self)
        self.start_timer.setSingleShot(True)
        self.start_timer.setInterval(5000)
        self.start_timer.timeout.connect(lambda: self._fail('The speech engine did not start. Check the voice and audio output.'))
        self.end_timer = QTimer(self)
        self.end_timer.setSingleShot(True)
        self.end_timer.setInterval(600000)
        self.end_timer.timeout.connect(lambda: self._fail('Speech time limit reached. Read the remaining text in chat.'))

    @Property(bool, notify=changed)
    def enabled(self): return self._enabled

    @Property(bool, notify=changed)
    def active(self): return self._active

    @Property(str, notify=changed)
    def state(self): return self._state

    @Property(str, notify=changed)
    def status(self): return self._status

    @Property(str, notify=changed)
    def voice(self): return self._voice_id

    @Property(float, notify=changed)
    def rate(self): return self._rate

    @Property(float, notify=changed)
    def pitch(self): return self._pitch

    @Property(float, notify=changed)
    def volume(self): return self._volume

    @Property('QVariantList', notify=changed)
    def voices(self):
        result = [{'id':'', 'label':'Automatic (Russian / English)'}]
        for key, voice in self._voices.items():
            result.append({'id':key, 'label':voice.name() + ' / ' + voice.locale().name()})
        if self._voice_id and self._voice_id not in self._voices:
            result.append({'id':self._voice_id, 'label':'Unavailable: ' + self._voice_id})
        return result

    @Slot(bool)
    def setEnabled(self, value):
        self._enabled = value
        self.settings.setValue('speech/enabled', value)
        if not value:
            self.stop()
            if self._state == 'error':
                self._state = 'finishing' if self._active else 'idle'
            self._status = 'Automatic speech is off. Read still works for individual replies.'
        self.changed.emit()

    @Slot(str, float, float, float, result=bool)
    def configure(self, voice, rate, pitch, volume):
        if not all(math.isfinite(x) for x in (rate, pitch, volume)) or not (-1 <= rate <= 1 and -1 <= pitch <= 1 and 0 <= volume <= 1):
            self._status = 'Choose a supported speech rate, pitch and volume.'
            self.changed.emit()
            return False
        if voice and voice not in self._voices and voice != self._voice_id:
            self._status = 'Refresh voices and choose an installed voice.'
            self.changed.emit()
            return False
        self.stop()
        self._voice_id, self._rate, self._pitch, self._volume = voice, rate, pitch, volume
        for key, value in dict(voice=voice, rate=rate, pitch=pitch, volume=volume).items():
            self.settings.setValue('speech/' + key, value)
        self.changed.emit()
        return True

    def _ensure_engine(self):
        if self._engine is None:
            self._engine = self.factory(self)
            self._engine.stateChanged.connect(self._native_state)
            self._engine.errorOccurred.connect(self._native_error)
        if self._engine.state() == QTextToSpeech.State.Error:
            raise ValueError(self._engine.errorString() or 'The local speech engine is unavailable.')
        if not self._voices:
            # Qt exposes voices for the current locale. Enumerate all installed
            # locales so Russian works even when the desktop language is English.
            original = self._engine.locale()
            try:
                for locale in self._engine.availableLocales() or [original]:
                    self._engine.setLocale(locale)
                    for voice in self._engine.availableVoices():
                        self._voices[voice.locale().name() + '/' + voice.name()] = voice
            finally:
                self._engine.setLocale(original)
        if not self._voices:
            raise ValueError('No speech voices are installed. Add a voice in system settings, then Refresh voices.')
        return self._engine

    @Slot()
    def refresh(self):
        if self._active or self._closing:
            return
        if self._engine:
            self._engine.stateChanged.disconnect(self._native_state)
            self._engine.errorOccurred.disconnect(self._native_error)
            self._engine.deleteLater()
            self._engine = None
            self._voices = {}
        try:
            self._ensure_engine()
            self._state, self._status = 'idle', 'Installed voices refreshed. Automatic chooses a matching Russian or English voice, preferring an adult male voice.'
        except (ValueError, RuntimeError) as exc:
            self._state, self._status = 'error', str(exc)
        self.changed.emit()

    def _choose_voice(self, text):
        if self._voice_id:
            if self._voice_id not in self._voices:
                raise ValueError('The saved voice is unavailable. Choose an installed voice or Automatic in Preferences > Speech.')
            return self._voices[self._voice_id]
        language = 'ru' if re.search(r'[\u0400-\u052f]', text) else 'en'
        candidates = [voice for voice in self._voices.values() if voice.locale().name().split('_')[0] == language]
        if not candidates:
            raise ValueError(('Russian' if language == 'ru' else 'English') + ' speech voice is not installed. Install it or choose a voice explicitly in Preferences > Speech.')
        return min(candidates, key=lambda v:(v.age() != QVoice.Age.Adult, v.gender() != QVoice.Gender.Male))

    def read(self, text, *, automatic=False):
        if self._closing or (automatic and not self._enabled):
            return False
        text = spoken_text(text)
        if not text:
            self._status = 'No prose to read. Code blocks and URLs stay in chat.'
            self.changed.emit()
            return False
        self._generation += 1
        generation = self._generation
        self._stop_native()
        self.quiet_timer.stop()
        self._quiet_callbacks.clear()
        self._active, self._started = True, False
        self._state, self._status = 'preparing', 'Preparing local speech; pausing the wake microphone.'
        self.changed.emit()
        try:
            self.prepare(lambda: self._speak(generation, text))
        except (ValueError, RuntimeError) as exc:
            self._fail(str(exc))
            return False
        return True

    def _speak(self, generation, text):
        if generation != self._generation or not self._active or self._closing:
            return
        try:
            engine = self._ensure_engine()
            voice = self._choose_voice(text)
            engine.setLocale(voice.locale())
            engine.setVoice(voice)
            engine.setRate(self._rate)
            engine.setPitch(self._pitch)
            engine.setVolume(self._volume)
            # Native configuration can synchronously report an error and cancel
            # this generation. Never speak after that cancellation.
            if generation != self._generation or not self._active or self._closing:
                return
            self._state, self._status = 'preparing', 'Starting local speech.'
            self.start_timer.start()
            self.end_timer.start()
            engine.say(text)
        except (ValueError, RuntimeError) as exc:
            self._fail(str(exc))
        self.changed.emit()

    def _native_state(self, state):
        if self._ignore_state or self._closing or not self._active:
            return
        if state == QTextToSpeech.State.Speaking:
            self._started = True
            self.start_timer.stop()
            self._state, self._status = 'speaking', 'Speaking locally. Use Stop speech to interrupt.'
            self.changed.emit()
        elif state == QTextToSpeech.State.Ready and self._started and self._engine.state() == state:
            self._cool_down('Finished speaking.')

    def _native_error(self, reason, message=''):
        if not self._ignore_state and not self._closing:
            self._fail(message or 'Local speech failed. Check the voice and audio device.')

    def _stop_native(self):
        self.start_timer.stop()
        self.end_timer.stop()
        if self._engine:
            self._ignore_state = True
            try:
                self._engine.stop()
            finally:
                self._ignore_state = False
        self._started = False

    def _cool_down(self, status):
        self._stop_native()
        self._state, self._status = 'finishing', status
        self.quiet_timer.start()
        self.changed.emit()

    def _fail(self, message):
        self._generation += 1
        self._stop_native()
        self._state, self._status = 'error', str(message)[:700]
        if self._active:
            self.quiet_timer.start()
        self.changed.emit()

    @Slot()
    def stop(self):
        if not self._active or self._closing:
            return
        self._generation += 1
        if not self.quiet_timer.isActive():
            self._cool_down('Speech stopped.')

    def when_quiet(self, callback):
        if not self._active:
            callback()
        else:
            self._quiet_callbacks.append(callback)
            self.stop()

    def _quiet(self):
        self._active = False
        if self._state != 'error': self._state = 'idle'
        callbacks, self._quiet_callbacks = self._quiet_callbacks, []
        self.changed.emit()
        for callback in callbacks:
            callback()

    def shutdown(self):
        self._closing = True
        self._generation += 1
        self._quiet_callbacks.clear()
        self.quiet_timer.stop()
        self._stop_native()
        self._active = False
