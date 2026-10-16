"""Real owned-process cancellation, decoding and offline/online preference isolation."""
import io
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

import av
import numpy as np
from PySide6.QtCore import QObject, QMetaObject, QProcess, QSettings, QUrl, Q_ARG
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tigo_gui.neural_speech import OnlineEngine
from tigo_gui.online_worker import decode_audio
from tigo_gui.speech import Speech
from tigo_gui.backend import Backend
import tigo_gui
from test_neural_speech import WORKER

APP = QApplication.instance() or QApplication([])


class TestOnlineSpeech(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo-online-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root/'ui.ini'), QSettings.IniFormat)
        self.worker = self.root/'fake_worker.py'
        self.worker.write_text(WORKER)
        self.owners = []

    def tearDown(self):
        for owner in self.owners:
            owner.shutdown()
            owner.deleteLater()
        APP.processEvents()

    def wait(self, condition):
        end = time.monotonic()+5
        while not condition() and time.monotonic() < end:
            QTest.qWait(10)
        self.assertTrue(condition())

    def speaker(self):
        speech = Speech(self.settings)
        self.owners.append(speech)
        return speech

    def test_local_is_default_and_female_automatic_matches_both_languages(self):
        speech = self.speaker()
        self.assertEqual(speech.engineKind, 'neural')
        speech.refresh()  # Catalog only; no models/downloads are started.
        self.assertTrue(speech.configure('auto:female', 0, 0, .8))
        self.assertEqual(speech._choose_voice('Привет').name(), 'Irina Neural')
        self.assertEqual(speech._choose_voice('Hello').name(), 'Lessac High')
        self.assertEqual(self.speaker().voice, 'auto:female')

    def test_online_selection_preserves_separate_local_voice_and_muted_setting(self):
        speech = self.speaker()
        speech.setEnabled(False)
        speech.refresh()
        self.assertTrue(speech.configure('ru_RU/Irina Neural', 0, 0, .8))
        speech.setEngine('online')
        self.assertEqual(speech.engineKind, 'online')
        self.assertIn('Microsoft', speech.status)
        self.assertFalse(speech.enabled)
        self.assertTrue(speech.configure('auto:female', 0, 0, .8))
        self.assertEqual(speech._choose_voice('Привет').name(), 'Svetlana Online')
        self.assertEqual(speech._choose_voice('Hello').name(), 'Aria Online')
        self.assertEqual(speech._engine.process.state(), QProcess.NotRunning)
        speech.setEngine('neural')
        self.assertEqual(speech.voice, 'ru_RU/Irina Neural')
        speech.setEngine('online')
        self.assertEqual(speech.voice, 'auto:female')
        self.assertEqual(self.speaker().engineKind, 'online')

    def test_online_cancel_reaps_worker_before_releasing_microphone_and_errors_do_not_switch(self):
        speech = self.speaker()
        speech.factory = lambda parent: OnlineEngine(parent, command=[sys.executable, '-u', str(self.worker)])
        speech.setEngine('online')
        speech.read('WAIT')
        self.wait(lambda: speech.status == 'Preparing a neural voice')
        released = []
        speech.when_quiet(lambda: released.append(speech._engine.process.state()))
        self.wait(lambda: bool(released))
        self.assertEqual(released, [QProcess.NotRunning])
        speech.read('ERROR')
        self.wait(lambda: speech.state == 'error')
        self.wait(lambda: not speech.active)
        self.assertEqual(speech.engineKind, 'online')
        self.assertIn('Audio device', speech.status)
        speech.read('Recovered')
        self.wait(lambda: speech.state == 'speaking')
        self.assertIn('Microsoft', speech.status)
        self.wait(lambda: not speech.active)


class TestOnlineDecoder(unittest.TestCase):
    def test_mp3_decodes_to_finite_mono_24khz_and_is_bounded(self):
        raw = io.BytesIO()
        signal = (.1*np.sin(2*np.pi*220*np.arange(2400)/24000)).astype(np.float32)
        with av.open(raw, 'w', format='mp3') as output:
            stream = output.add_stream('libmp3lame', rate=24000)
            stream.layout = 'mono'
            frame = av.AudioFrame.from_ndarray(signal.reshape(1, -1), format='flt', layout='mono')
            frame.sample_rate = 24000
            for packet in stream.encode(frame): output.mux(packet)
            for packet in stream.encode(None): output.mux(packet)
        decoded = decode_audio(raw.getvalue())
        self.assertEqual(decoded.dtype, np.float32)
        self.assertEqual(decoded.ndim, 1)
        self.assertTrue(np.isfinite(decoded).all())
        self.assertGreater(float(np.max(np.abs(decoded))), .01)
        with mock.patch('tigo_gui.online_worker.MAX_SAMPLES', 1):
            with self.assertRaises(ValueError): decode_audio(raw.getvalue())
        for data in (b'', b'invalid mp3'):
            with self.assertRaises(Exception): decode_audio(data)


class TestSpeechSettingsWindow(unittest.TestCase):
    def test_actual_engine_selector_privacy_and_female_preview_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = QSettings(str(Path(folder)/'ui.ini'), QSettings.IniFormat)
            settings.setValue('speech/enabled', False)
            settings.setValue('language', 'ru')
            backend = Backend(settings)
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty('bridge', backend)
            engine.load(QUrl.fromLocalFile(str(Path(tigo_gui.__file__).parent/'ui/Main.qml')))
            window = engine.rootObjects()[0]
            try:
                QMetaObject.invokeMethod(window.findChild(QObject, 'preferences'), 'open')
                window.findChild(QObject, 'preferenceTabs').setProperty('currentIndex', 6)
                QTest.qWait(80)
                selector = window.findChild(QObject, 'speechEngineChoice')
                selector.setProperty('currentIndex', 1)
                self.assertTrue(QMetaObject.invokeMethod(selector, 'activated', Q_ARG(int, 1)))
                QTest.qWait(80)
                self.assertEqual(backend.speaker.engineKind, 'online')
                self.assertIn('sent to Microsoft', window.findChild(QObject, 'speechPrivacy').property('text'))
                choice = window.findChild(QObject, 'speakingVoiceChoice')
                choice.setProperty('currentIndex', 1)  # Automatic female.
                with mock.patch.object(backend.speaker, 'read', return_value=True) as read:
                    self.assertTrue(QMetaObject.invokeMethod(window.findChild(QObject, 'testSpeechButton'), 'clicked'))
                self.assertEqual(backend.speaker.voice, 'auto:female')
                self.assertIn('Тиго', read.call_args.args[0])
                self.assertIn('наставник', read.call_args.args[0])
                self.assertFalse(backend.speaker.enabled)
                selector.setProperty('currentIndex', 0)
                QMetaObject.invokeMethod(selector, 'activated', Q_ARG(int, 0))
                QTest.qWait(50)
                self.assertEqual(backend.speaker.engineKind, 'neural')
                self.assertIn('without uploading', window.findChild(QObject, 'speechPrivacy').property('text'))
            finally:
                backend.shutdown()
                window.close()
                engine.deleteLater()
                APP.sendPostedEvents(None, 52)
                APP.processEvents()
