"""Real Qt subprocess cancellation plus pinned model download/extraction checks."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import time
import unittest
from unittest import mock
from PySide6.QtCore import QProcess, QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tigo_gui.neural_speech import NeuralEngine
from tigo_gui.speech import Speech
from tigo_gui.speech_models import VOICES, ensure_voice, unpack

APP = QApplication.instance() or QApplication([])

WORKER = '''import json,sys,time
sys.stdin.reconfigure(encoding='utf-8')
for line in sys.stdin:
 v=json.loads(line); token=v['id']
 def emit(kind,**kwargs):print(json.dumps({'type':kind,'id':token,**kwargs}),flush=True)
 if v['text']=='CRASH':sys.exit(9)
 if v['text']=='ERROR':emit('error',message='Audio device is missing');continue
 # A stale message must not cancel a newer generation.
 print(json.dumps({'type':'error','id':'old','message':'stale'}),flush=True)
 emit('preparing',message='Preparing a neural voice')
 if v['text']=='WAIT':time.sleep(30)
 time.sleep(.03)
 emit('speaking')
 time.sleep(.06)
 emit('done')
'''


class TestNeuralSpeech(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo neural ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root/'ui.ini'), QSettings.IniFormat)
        self.worker = self.root/'worker.py'
        self.worker.write_text(WORKER, encoding='utf-8')
        self.owners = []

    def tearDown(self):
        for owner in self.owners:
            owner.shutdown()
            owner.deleteLater()
        APP.processEvents()

    def wait(self, check):
        deadline = time.monotonic()+6
        while not check() and time.monotonic()<deadline: QTest.qWait(10)
        self.assertTrue(check())

    def speaker(self):
        def factory(parent):
            return NeuralEngine(parent, command=[sys.executable, '-u', str(self.worker)])
        speech = Speech(self.settings, engine_factory=factory)
        self.owners.append(speech)
        return speech

    def test_migrates_old_system_voice_without_enabling_muted_speech(self):
        self.settings.setValue('speech/voice', 'ru_RU/Old voice')
        self.settings.setValue('speech/pitch', -.6)
        self.settings.setValue('speech/rate', -.3)
        self.settings.setValue('speech/enabled', False)
        speech = Speech(self.settings)
        self.owners.append(speech)
        self.assertEqual(speech.engineKind, 'neural')
        self.assertEqual(speech.voice, '')
        self.assertEqual((speech.rate, speech.pitch), (0, 0))
        self.assertFalse(speech.enabled)
        speech.refresh()
        self.assertEqual(speech._choose_voice('Наставник').name(), 'Dmitri Neural')
        self.assertEqual(speech._choose_voice('Mentor').name(), 'Joe Neural')
        self.assertTrue(speech.configure('ru_RU/Denis Neural', .2, 0, .9))
        reopened = Speech(self.settings)
        self.owners.append(reopened)
        self.assertEqual(reopened.voice, 'ru_RU/Denis Neural')
        self.assertAlmostEqual(reopened.rate, .2)

    def test_success_reuses_warm_process_and_ignores_stale_events(self):
        speech = self.speaker()
        speech.read('Готово, наставник.')
        self.wait(lambda: speech.state=='speaking')
        pid = speech._engine.process.processId()
        self.assertGreater(pid, 0)
        self.assertEqual(speech._engine._voice.key, 'ru_RU-dmitri-medium')
        self.wait(lambda: not speech.active)
        self.assertEqual(speech._engine.process.processId(), pid)
        speech.read('Ready, mentor.')
        self.wait(lambda: speech.state=='speaking')
        self.assertEqual(speech._engine._voice.key, 'en_US-joe-medium')
        self.assertEqual(speech._engine.process.processId(), pid)
        self.wait(lambda: not speech.active)

    def test_stop_during_preparation_reaps_worker_before_microphone_callback(self):
        speech = self.speaker()
        speech.read('WAIT')
        self.wait(lambda: speech.status=='Preparing a neural voice')
        self.assertEqual(speech.state, 'preparing')
        self.assertGreater(speech._engine.process.processId(), 0)
        callbacks = []
        speech.when_quiet(lambda: callbacks.append(speech._engine.process.state()))
        self.wait(lambda: bool(callbacks))
        self.assertEqual(callbacks, [QProcess.NotRunning])
        self.assertFalse(speech.active)
        speech.read('Next reply')
        self.wait(lambda: speech.state=='speaking')
        self.wait(lambda: not speech.active)

    def test_worker_errors_and_crashes_are_visible_and_recoverable(self):
        speech = self.speaker()
        for text, message in [('ERROR', 'Audio device'), ('CRASH', 'process')]:
            speech.read(text)
            self.wait(lambda: speech.state=='error')
            self.assertIn(message, speech.status)
            self.wait(lambda: not speech.active)
        speech.read('Recovered')
        self.wait(lambda: speech.state=='speaking')
        self.wait(lambda: not speech.active)


class TestNeuralModelAssets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = next(iter(VOICES))
        self.prefix = 'vits-piper-'+self.key

    def archive(self, extra=None):
        result = io.BytesIO()
        with tarfile.open(fileobj=result, mode='w:bz2') as out:
            for name, data in [('tokens.txt',b'a'), ('espeak-ng-data/a',b'data'),
                               (self.key+'.onnx',b'model'), ('MODEL_CARD',b'fixture')]:
                member = tarfile.TarInfo(self.prefix+'/'+name)
                member.size = len(data)
                out.addfile(member, io.BytesIO(data))
            if extra: out.addfile(extra)
        return result.getvalue()

    def spec(self, data):
        return {**VOICES[self.key], 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def test_verified_download_is_cached_and_interrupted_partial_is_replaced(self):
        data = self.archive()
        (self.root/(self.key+'.part')).write_bytes(b'interrupted')
        with mock.patch.dict(VOICES, {self.key: self.spec(data)}), mock.patch('urllib.request.urlopen', return_value=io.BytesIO(data)) as fetch:
            path = ensure_voice(self.key, root=self.root)
            self.assertEqual((path/(self.key+'.onnx')).read_bytes(), b'model')
            self.assertEqual((path/'MODEL_CARD').read_text(), 'fixture')
            self.assertEqual(ensure_voice(self.key, root=self.root), path)
            self.assertEqual(fetch.call_count, 1)
            self.assertFalse((self.root/(self.key+'.part')).exists())

    def test_corrupt_or_oversized_download_is_not_installed(self):
        data = self.archive()
        for response in [data[:-1]+b'x', data+b'x']:
            with self.subTest(size=len(response)), mock.patch.dict(VOICES, {self.key: self.spec(data)}), mock.patch('urllib.request.urlopen', return_value=io.BytesIO(response)):
                with self.assertRaises(ValueError): ensure_voice(self.key, root=self.root)
                self.assertFalse((self.root/self.key).exists())
                self.assertFalse((self.root/(self.key+'.part')).exists())

    def test_archive_rejects_traversal_and_links(self):
        for member in [tarfile.TarInfo(self.prefix+'/../escape'), tarfile.TarInfo('/absolute')]:
            with self.subTest(path=member.name):
                with self.assertRaises(ValueError): unpack(io.BytesIO(self.archive(member)), self.root/'stage', self.prefix)
        link = tarfile.TarInfo(self.prefix+'/link')
        link.type, link.linkname = tarfile.SYMTYPE, '../outside'
        with self.assertRaises(ValueError): unpack(io.BytesIO(self.archive(link)), self.root/'stage', self.prefix)


if __name__ == '__main__':
    unittest.main()
