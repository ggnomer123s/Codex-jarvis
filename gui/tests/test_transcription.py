"""Provider selection, owned worker lifecycle and production dictation settings."""
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock
from PySide6.QtCore import QObject, QMetaObject, QSettings, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tigo_gui.backend import Backend
from tigo_gui.interface_tools import interface_summary
import tigo_gui
from fake_speech import Engine

APP = QApplication.instance() or QApplication([])


class TestDictation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo dictation ')
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root/'settings.ini'),QSettings.Format.IniFormat)
        self.settings.setValue('speech/enabled',False)
        self.settings.setValue('folder',str(self.root))
        self.root.joinpath('settings.access').write_text('read-only\n')
        self.backends=[]

    def tearDown(self):
        for backend in self.backends:
            backend.shutdown();backend.deleteLater()
        APP.processEvents()
        self.temp.cleanup()

    def backend(self, **kwargs):
        backend=Backend(self.settings,codex_home_override=self.root/'profile',speech_engine_factory=Engine,**kwargs)
        self.backends.append(backend)
        return backend

    def wait(self, condition):
        deadline=time.monotonic()+4
        while not condition() and time.monotonic()<deadline:
            QTest.qWait(10)
        self.assertTrue(condition())

    def test_provider_persists_without_credentials_and_keeps_local_model(self):
        backend=self.backend()
        self.assertEqual(backend.transcriptionProvider,'local')
        self.assertTrue(backend.saveTranscriptionPreferences('online'))
        reopened=self.backend()
        self.assertEqual(reopened.transcriptionProvider,'online')
        self.assertEqual(reopened.voiceModel,backend.voiceModel)
        self.assertFalse(any('key' in name.lower() for name in self.settings.allKeys()))
        self.assertFalse(backend.saveTranscriptionPreferences('unknown'))

    def test_online_auto_language_stops_before_microphone_worker(self):
        backend=self.backend()
        backend.saveTranscriptionPreferences('online')
        backend.toggleVoice()
        self.assertEqual(backend.voiceState,'idle')
        self.assertEqual(backend.voice.processId(),0)
        self.assertIn('language',backend.messages[-1]['text'])

    def test_online_worker_reused_review_required_then_cancel_and_provider_change(self):
        worker=self.root/'worker.py'
        worker.write_text('''import json,sys
assert sys.argv[sys.argv.index('--provider')+1]=='online'
print(json.dumps({'type':'ready','microphones':[]}),flush=True)
for line in sys.stdin:
    value=json.loads(line)
    if value['command']=='shutdown':break
    if value['command']=='record':
        print(json.dumps({'type':'recording','id':value['id']}),flush=True)
    elif value['command']=='stop':
        print(json.dumps({'type':'transcript','id':value['id'],'text':'Review online dictation'}),flush=True)
        print(json.dumps({'type':'idle','id':value['id']}),flush=True)
''')
        backend=self.backend(voice_command=[sys.executable,'-u',str(worker)])
        backend.savePreferences('low','read-only','','ru','small')
        backend.saveTranscriptionPreferences('online')
        received=[];backend.transcriptReady.connect(received.append)
        with mock.patch('tigo_gui.backend.dependencies_available',return_value=True):
            backend.toggleVoice();self.wait(lambda:backend.voiceState=='recording')
            pid=backend.voice.processId()
            self.assertFalse(backend.saveTranscriptionPreferences('local'))
            backend.toggleVoice();self.wait(lambda:backend.voiceState=='idle')
            self.assertEqual(received,['Review online dictation'])
            self.assertFalse(backend.busy)
            self.assertEqual(backend.process.processId(),0)
            backend.toggleVoice();self.wait(lambda:backend.voiceState=='recording')
            self.assertEqual(backend.voice.processId(),pid)
            backend.cancelVoice()
            self.assertEqual(backend.voice.processId(),0)
            self.assertTrue(backend.saveTranscriptionPreferences('local'))
        self.assertEqual(received,['Review online dictation'])

    def test_qml_provider_selection_filters_auto_and_discloses_upload(self):
        backend=self.backend()
        engine=QQmlApplicationEngine()
        warnings=[]
        engine.warnings.connect(lambda items:warnings.extend(str(x) for x in items))
        engine.rootContext().setContextProperty('bridge',backend)
        engine.load(QUrl.fromLocalFile(str(Path(tigo_gui.__file__).parent/'ui/Main.qml')))
        self.assertTrue(engine.rootObjects(),warnings)
        window=engine.rootObjects()[0]
        try:
            popup=window.findChild(QObject,'preferences')
            QMetaObject.invokeMethod(popup,'open')
            window.findChild(QObject,'preferenceTabs').setProperty('currentIndex',1)
            choice=window.findChild(QObject,'transcriptionChoice')
            choice.setProperty('currentIndex',1)
            QTest.qWait(30)
            language=window.findChild(QObject,'languageChoice')
            self.assertNotEqual(language.property('currentValue'),'auto')
            self.assertIn('Google',window.findChild(QObject,'transcriptionPrivacy').property('text'))
            QMetaObject.invokeMethod(window.findChild(QObject,'savePreferencesButton'),'clicked')
            QTest.qWait(20)
            self.assertEqual(backend.transcriptionProvider,'online')
            self.assertEqual(backend.language,'ru')
            self.assertEqual(backend.voice.processId(),0)
            self.assertFalse(warnings,warnings)
        finally:
            window.close();engine.deleteLater();APP.processEvents()

    def test_interface_inventory_uses_reported_tools_without_claiming_ownership(self):
        self.assertIn('No semantic',interface_summary([{'name':'windows-mcp','tools':{}}]))
        self.assertIn('Windows UI Automation',interface_summary([{'name':'windows-mcp','tools':{'Snapshot':{}}}]))
        self.assertIn('X11 AT-SPI',interface_summary([{'name':'tigo-x11','tools':[{'name':'ui_elements'},{'name':'click_ui'}]}]))
        self.assertIn('does not prove',interface_summary([{'name':'hypruse','tools':{'ui':{},'click_ui':{}}}]))
