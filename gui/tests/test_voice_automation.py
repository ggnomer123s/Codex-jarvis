"""Hands-free voice lifecycle, draft preservation and hidden background startup."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from PySide6.QtCore import QObject, QMetaObject, QSettings, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
import tigo_gui
from tigo_gui.backend import Backend
from fake_speech import Engine
from test_wake import FAKE as WAKE_WORKER

APP=QApplication.instance() or QApplication([])


class TestVoiceAutomation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tigo hands free ')
        self.root=Path(self.temp.name)
        self.settings=QSettings(str(self.root/'settings.ini'),QSettings.IniFormat)
        self.settings.setValue('speech/enabled',False)
        self.settings.setValue('language','ru')
        self.settings.setValue('folder',str(self.root))
        self.root.joinpath('settings.access').write_text('read-only\n')
        self.backends=[]

    def tearDown(self):
        for backend in self.backends:
            backend.shutdown();backend.deleteLater()
        APP.processEvents();self.temp.cleanup()

    def wait(self,condition):
        deadline=time.monotonic()+5
        while not condition() and time.monotonic()<deadline:QTest.qWait(10)
        self.assertTrue(condition())

    def backend(self,reason='silence',delay=False,no_idle=False):
        worker=self.root/('voice-'+str(len(self.backends))+'.py')
        worker.write_text('''import json,sys
def emit(kind,**data):print(json.dumps({'type':kind,**data}),flush=True)
emit('ready',microphones=[])
recording=''
for line in sys.stdin:
 value=json.loads(line)
 if value['command']=='shutdown':break
 if value['command']=='record':
  recording=value['id'];emit('recording',id=recording)
 if (value['command']=='record' and not %r) or value['command']=='finish':
  emit('speech_end',id=recording,reason=%r)
  emit('transcript',id=recording,text='Synthetic voice request',endReason=%r)
  if %r:break
  emit('idle',id=recording)
'''%(delay,reason,reason,no_idle))
        server=Path(__file__).with_name('fake_app_server.py')
        backend=Backend(self.settings,codex_command=[sys.executable,'-u',str(server),'normal',str(self.root/'requests.jsonl')],
                        voice_command=[sys.executable,'-u',str(worker)],codex_home_override=self.root/'profile',speech_engine_factory=Engine)
        backend.wake.register=mock.Mock()
        self.backends.append(backend)
        return backend

    def record(self,backend):
        with mock.patch('tigo_gui.backend.dependencies_available',return_value=True):backend.toggleVoice()

    def test_explicit_auto_send_submits_once_only_after_voice_worker_idle(self):
        backend=self.backend()
        self.assertTrue(backend.saveVoiceAutomation(True,1600))
        self.record(backend)
        self.wait(lambda:any(x['role']=='assistant' for x in backend.messages))
        self.assertEqual([x['text'] for x in backend.messages if x['role']=='user'],['Synthetic voice request'])
        self.assertEqual(backend.voiceState,'idle')
        self.assertEqual(backend._pending_voice_submit,None)

    def test_off_manual_stop_and_time_limit_keep_review_flow(self):
        for enabled,reason in ((False,'silence'),(True,'manual'),(True,'limit')):
            backend=self.backend(reason)
            backend.saveVoiceAutomation(enabled,1600)
            received=[];backend.transcriptReady.connect(received.append)
            self.record(backend)
            self.wait(lambda:bool(received) and backend.voiceState=='idle')
            self.assertEqual(received,['Synthetic voice request'])
            self.assertEqual(backend.process.processId(),0)

    def test_existing_or_edited_draft_and_attachments_prevent_auto_send(self):
        for scenario in ('existing','edited','attachment'):
            backend=self.backend(delay=True)
            backend.saveVoiceAutomation(True,1600)
            if scenario=='existing':backend.updateDraftState(True)
            if scenario=='attachment':backend._attachments=[{'fixture':True}]
            received=[];backend.transcriptReady.connect(received.append)
            self.record(backend)
            self.wait(lambda:backend.voiceState=='recording')
            if scenario=='edited':
                backend.updateDraftState(True);backend.updateDraftState(False)
            backend._voice_write('finish')
            self.wait(lambda:backend.voiceState=='idle' and bool(received))
            self.assertEqual(backend.process.processId(),0)
            self.assertIn('kept in the draft',backend.notice)
            backend._attachments=[]

    def test_cancel_while_recording_sends_nothing(self):
        backend=self.backend(delay=True)
        backend.saveVoiceAutomation(True,1600)
        self.record(backend);self.wait(lambda:backend.voiceState=='recording')
        backend.cancelVoice();QTest.qWait(60)
        self.assertEqual(backend.process.processId(),0)
        self.assertEqual(backend._pending_voice_submit,None)

    def test_worker_exit_before_idle_preserves_text_without_auto_send(self):
        backend=self.backend(no_idle=True)
        backend.saveVoiceAutomation(True,1600)
        received=[];backend.transcriptReady.connect(received.append)
        self.record(backend)
        self.wait(lambda:backend.voice.processId()==0 and bool(received))
        self.assertEqual(received,['Synthetic voice request'])
        self.assertEqual(backend.process.processId(),0)

    def test_wake_starts_dictation_and_submits_with_separate_opt_ins(self):
        backend=self.backend()
        backend.saveVoiceAutomation(True,1600)
        script=self.root/'wake.py';script.write_text(WAKE_WORKER)
        backend.wake.command=[sys.executable,'-u',str(script)]
        with mock.patch('tigo_gui.wake_control.dependencies_available',return_value=True):
            self.assertTrue(backend.wake.configure(True,False,'base','ru','',True,'online',True))
        self.wait(lambda:backend.wake.state=='listening')
        with mock.patch('tigo_gui.backend.dependencies_available',return_value=True):
            backend.wake._write('test-wake')
            self.wait(lambda:any(x['role']=='assistant' for x in backend.messages))
        self.assertEqual([x['text'] for x in backend.messages if x['role']=='user'],['Synthetic voice request'])
        self.assertEqual(backend.wake.provider,'online')
        self.assertTrue(backend.wake.recordAfterWake)
        self.assertEqual(self.settings.value('wake/provider'),'online')
        self.assertEqual(backend.wake.register.call_args.args,(False,))

    def test_qml_wake_options_save_and_automation_does_not_open_microphone(self):
        backend=self.backend()
        engine=QQmlApplicationEngine();warnings=[]
        engine.warnings.connect(lambda items:warnings.extend(str(x) for x in items))
        engine.rootContext().setContextProperty('bridge',backend)
        engine.load(QUrl.fromLocalFile(str(Path(tigo_gui.__file__).parent/'ui/Main.qml')))
        self.assertTrue(engine.rootObjects(),warnings)
        window=engine.rootObjects()[0]
        try:
            QMetaObject.invokeMethod(window.findChild(QObject,'preferences'),'open')
            window.findChild(QObject,'preferenceTabs').setProperty('currentIndex',5)
            window.findChild(QObject,'wakeRecordAfter').setProperty('checked',True)
            window.findChild(QObject,'wakeProvider').setProperty('currentIndex',1)
            QTest.qWait(30)
            box=window.findChild(QObject,'wakeAutomation').findChild(QObject,'voiceAutoSend')
            box.setProperty('checked',True);QMetaObject.invokeMethod(box,'clicked')
            QMetaObject.invokeMethod(window.findChild(QObject,'savePreferencesButton'),'clicked')
            QTest.qWait(20)
            self.assertTrue(backend.voiceAutoSend)
            self.assertTrue(backend.wake.recordAfterWake)
            self.assertEqual(backend.wake.provider,'online')
            self.assertIn('speech phrases',window.findChild(QObject,'wakePrivacy').property('text'))
            self.assertEqual(backend.wake.process.processId(),0)
            self.assertEqual(backend.voice.processId(),0)
            self.assertFalse(warnings,warnings)
        finally:
            window.close();engine.deleteLater();APP.processEvents()

    def test_production_background_start_stays_hidden_without_tray_and_on_wake_error(self):
        child=self.root/'background.py'
        fake=self.root/'fake_wake.py';fake.write_text("import json,time\nprint(json.dumps({'type':'error','message':'Fixture microphone unavailable'}),flush=True)\ntime.sleep(4)\n")
        child.write_text('''import sys
from pathlib import Path
from PySide6.QtCore import QSettings,QTimer
from PySide6.QtGui import QGuiApplication
from tigo_gui import app as entry
from tigo_gui.backend import Backend
from tigo_gui.activation import Instance
from unittest.mock import Mock
settings=QSettings(%r,QSettings.IniFormat)
settings.setValue('speech/enabled',False);settings.setValue('wake/enabled',True)
def factory(*args,**kwargs):
 b=Backend(settings,**kwargs)
 b.wake.command=[sys.executable,'-u',%r];b.wake.register=Mock()
 QTimer.singleShot(1200,check)
 return b
entry.Backend=factory
entry.Instance=lambda owner:Instance(owner,namespace=%r)
entry.QSystemTrayIcon.isSystemTrayAvailable=lambda:False
class FixtureOverlay:
 def __init__(self,*args):pass
 def close(self):pass
entry.ScreenOverlay=FixtureOverlay
def check():
 windows=[w for w in QGuiApplication.topLevelWindows() if w.title()=='Tigo - Personal intelligence']
 ok=len(windows)==1 and not windows[0].isVisible()
 print('HIDDEN_BACKGROUND_OK' if ok else 'UNEXPECTED_VISIBLE_WINDOW',flush=True)
 QGuiApplication.instance().exit(0 if ok else 3)
sys.argv=['tigo','--background']
raise SystemExit(entry.main())
'''%(str(self.root/'background.ini'),str(fake),str(self.root)))
        result=subprocess.run([sys.executable,str(child)],env={**os.environ,'QT_QPA_PLATFORM':'offscreen','QT_QUICK_BACKEND':'software'},capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('HIDDEN_BACKGROUND_OK',result.stdout)
