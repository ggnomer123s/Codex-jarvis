"""Deterministic OS speech adapter for tests; never plays real audio."""
from PySide6.QtCore import QObject, QLocale, Signal
from PySide6.QtTextToSpeech import QTextToSpeech, QVoice


class Voice:
    def __init__(self, name, locale, gender=QVoice.Gender.Male):
        self._name, self._locale, self._gender = name, QLocale(locale), gender
    def name(self): return self._name
    def locale(self): return self._locale
    def gender(self): return self._gender
    def age(self): return QVoice.Age.Adult


class Engine(QObject):
    stateChanged = Signal(object)
    errorOccurred = Signal(object, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spoken = []
        self.chosen = None
        self.rate = self.pitch = self.volume = None
        self._state = QTextToSpeech.State.Ready
        self._locale = QLocale('en_US')
        self.voices = [Voice('Irina','ru_RU',QVoice.Gender.Female), Voice('Dmitri','ru_RU'), Voice('David','en_US')]
    def locale(self): return self._locale
    def setLocale(self, locale): self._locale = locale
    def availableLocales(self): return list({v.locale().name():v.locale() for v in self.voices}.values())
    def availableVoices(self): return [v for v in self.voices if v.locale() == self._locale]
    def state(self): return self._state
    def errorString(self): return ''
    def setVoice(self, voice): self.chosen = voice
    def setRate(self, value): self.rate = value
    def setPitch(self, value): self.pitch = value
    def setVolume(self, value): self.volume = value
    def say(self, text):
        self.spoken.append(text)
        self._state = QTextToSpeech.State.Speaking
        self.stateChanged.emit(self._state)
    def stop(self):
        self._state = QTextToSpeech.State.Ready
        self.stateChanged.emit(self._state)
    def finish(self): self.stop()
