"""Local speech state, cancellation and real-process microphone handoffs."""
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import time
import unittest
from unittest import mock
from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from PySide6.QtTextToSpeech import QTextToSpeech
from tigo_gui.backend import Backend
from tigo_gui.speech import Speech
from fake_speech import Engine

APP = QApplication.instance() or QApplication([])


class TestSpeech(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo speech ')
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root/'ui.ini'),QSettings.Format.IniFormat)
        self.settings.setValue('folder',str(self.root))
        Path(self.settings.fileName()).with_suffix('.access').write_text('read-only\n')
        self.owners = []
        self.engine = None

    def tearDown(self):
        for owner in self.owners:
            owner.shutdown(); owner.deleteLater()
        APP.processEvents()
        self.temp.cleanup()

    def factory(self, parent):
        self.engine = Engine(parent)
        return self.engine

    def speech(self, **kwargs):
        speech = Speech(self.settings,engine_factory=self.factory,**kwargs)
        self.owners.append(speech)
        return speech

    def backend(self, scenario='normal'):
        backend=Backend(self.settings,codex_home_override=self.root/'codex',speech_engine_factory=self.factory,
                        codex_command=[sys.executable,'-u',str(Path(__file__).with_name('fake_app_server.py')),scenario,str(self.root/'requests.jsonl')])
        self.owners.append(backend)
        return backend

    def wait(self, check):
        deadline=time.monotonic()+6
        while not check() and time.monotonic()<deadline:QTest.qWait(10)
        self.assertTrue(check())

    def test_native_state_voice_selection_and_settings_persist(self):
        speech=self.speech()
        self.assertTrue(speech.enabled)
        speech.read('Наставник, **всё готово**.\n```sh\nrm unsafe\n```')
        self.assertEqual(self.engine.chosen.name(),'Dmitri')
        self.assertNotIn('rm unsafe',self.engine.spoken[-1])
        self.assertEqual(speech.state,'speaking')
        self.assertTrue(speech.active)
        self.engine.finish()
        self.assertTrue(speech.active)  # Hold the wake mic through the speaker tail.
        self.wait(lambda:not speech.active)
        self.assertTrue(speech.configure('en_US/David',.2,-.3,.6))
        speech.setEnabled(False)
        reopened=self.speech()
        self.assertFalse(reopened.enabled)
        self.assertEqual(reopened.voice,'en_US/David')
        self.assertAlmostEqual(reopened.volume,.6)
        self.assertFalse(reopened.read('Automatic is off',automatic=True))
        self.assertTrue(reopened.read('Read this manually'))
        self.assertEqual(self.engine.chosen.name(),'David')
        self.assertEqual(self.engine.volume,.6)

    def test_cancel_before_pause_ack_never_says_stale_text(self):
        prepared=[]
        speech=self.speech(prepare=prepared.append)
        speech.read('First')
        self.assertIsNone(self.engine)
        speech.stop()
        prepared[0]()
        self.assertIsNone(self.engine)
        self.wait(lambda:not speech.active)
        speech.read('Second')
        prepared[0]()
        prepared[1]()
        self.assertEqual(self.engine.spoken,['Second'])

    def test_missing_russian_voice_and_native_error_are_visible(self):
        speech=self.speech()
        speech.refresh()
        self.engine.voices=[v for v in self.engine.voices if v.locale().name().startswith('en')]
        speech._voices = {}  # Simulate a refreshed engine with only English voices.
        speech.read('Привет, наставник')
        self.assertEqual(speech.state,'error')
        self.assertIn('Russian',speech.status)
        self.assertEqual(self.engine.spoken,[])
        self.wait(lambda:not speech.active)
        speech.read('Hello')
        self.engine.errorOccurred.emit(QTextToSpeech.ErrorReason.Playback,'No audio output')
        self.assertEqual(speech.state,'error')
        self.assertIn('No audio output',speech.status)
        self.wait(lambda:not speech.active)

    def test_configuration_error_never_starts_playback_and_can_be_muted(self):
        speech=self.speech()
        speech.refresh()
        def fail(_):
            self.engine.errorOccurred.emit(QTextToSpeech.ErrorReason.Configuration, 'Voice configuration failed')
        with mock.patch.object(self.engine,'setPitch',side_effect=fail):
            speech.read('Hello')
        self.assertEqual(speech.state,'error')
        self.assertEqual(self.engine.spoken,[])
        speech.setEnabled(False)
        self.wait(lambda:not speech.active)
        self.assertEqual(speech.state,'idle')
        self.assertIn('off',speech.status)

    def test_manual_recording_waits_for_speaker_tail_then_starts(self):
        backend=self.backend()
        voice=self.root/'voice.py'
        voice.write_text('''import json,sys
print(json.dumps({'type':'ready'}),flush=True)
for line in sys.stdin:
 value=json.loads(line)
 if value['command']=='record':
  print(json.dumps({'type':'recording','id':value['id']}),flush=True)
 if value['command']=='shutdown': break
''',encoding='utf-8')
        backend._voice_command=[sys.executable,'-u',str(voice)]
        backend.speaker.read('Ready, mentor.')
        with mock.patch('tigo_gui.backend.dependencies_available',return_value=True):
            backend.toggleVoice()
        self.assertEqual(backend.voice.processId(),0)
        self.assertTrue(backend.speaker.active)
        self.wait(lambda:backend.voiceState=='recording')
        self.assertFalse(backend.speaker.active)
        self.assertNotEqual(backend.voice.processId(),0)
        self.assertEqual(backend.process.processId(),0)
        backend.cancelVoice()

    def test_all_messages_are_queued_and_history_is_silent(self):
        backend=self.backend('commentary')
        backend.send('The task is complete.')
        self.wait(lambda:not backend.busy)
        self.assertEqual(self.engine.spoken,['I will inspect the task.'])
        self.engine.finish()
        self.wait(lambda:len(self.engine.spoken)==2)
        self.assertEqual(self.engine.spoken,['I will inspect the task.','The task is complete.'])
        key=backend.historyEntries[0]['id']
        backend.speaker.stop()
        self.wait(lambda:not backend.speaker.active)
        backend.newSession()
        self.assertTrue(backend.openConversation(key))
        QTest.qWait(30)
        self.assertEqual(self.engine.spoken,['I will inspect the task.','The task is complete.'])
        self.assertEqual(backend.process.state(),backend.process.ProcessState.Running)

    def test_completed_cards_speak_whole_canonical_text_once_before_turn_end(self):
        backend=self.backend()
        backend._begin('codex')
        backend._thread_id,backend._turn_id='thread','turn'
        scope={'threadId':'thread','turnId':'turn'}
        greeting='Привет, наставник. Я на связи, готов к делу. Как ты?'
        for char in greeting:
            backend._notification('item/agentMessage/delta',dict(scope,itemId='one',delta=char))
        QTest.qWait(50)
        self.assertIsNone(self.engine)  # Even complete sentences wait for the card.
        canonical=greeting+'\n\nВсё готово.\n```sh\nprivate command\n```'
        item={'type':'agentMessage','id':'one','text':canonical,'phase':'commentary'}
        backend._notification('item/completed',dict(scope,item=item))
        self.assertTrue(backend.busy)
        self.assertEqual(self.engine.spoken,[greeting+'\n\nВсё готово.'])
        self.assertEqual(backend._messages[backend._item_rows['one']]['text'],canonical)
        backend._notification('item/completed',dict(scope,item=item))
        final='The task is complete. You can review the result now.'
        backend._notification('item/completed',dict(scope,item={
            'type':'agentMessage','id':'two','text':final,'phase':'final_answer'}))
        self.assertEqual(len(self.engine.spoken),1)
        backend._finish('completed')
        self.engine.finish()
        self.wait(lambda:len(self.engine.spoken)==2)
        self.assertEqual(self.engine.spoken[-1],final)
        self.engine.finish()
        self.wait(lambda:not backend.speaker.active)
        self.assertEqual(len(self.engine.spoken),2)  # No duplicate at turn completion.
        backend.readMessage(backend._item_rows['one'])
        self.assertEqual(self.engine.spoken[-1],self.engine.spoken[0])

    def test_stop_mutes_remaining_cards_and_next_task_can_speak(self):
        backend=self.backend()
        def begin(turn):
            backend._begin('codex')
            backend._thread_id,backend._turn_id='thread',turn
        def complete(turn,item_id,text):
            backend._notification('item/completed',{'threadId':'thread','turnId':turn,
                'item':{'type':'agentMessage','id':item_id,'text':text}})
        begin('one')
        complete('one','first','First block. More text.')
        complete('one','queued','Queued block. More text.')
        backend.speaker.stop()
        complete('one','muted','Must remain silent.')
        backend._finish('completed')
        self.wait(lambda:not backend.speaker.active)
        self.assertEqual(self.engine.spoken,['First block. More text.'])
        begin('two')
        complete('one','stale','Old turn stays silent.')
        complete('two','new','New block. The next task can speak.')
        self.assertEqual(self.engine.spoken[-1],'New block. The next task can speak.')
        self.assertEqual(len(self.engine.spoken),2)
        backend._finish('completed')

    def test_unfinished_card_is_not_read_when_turn_ends(self):
        backend=self.backend()
        backend._begin('codex')
        backend._thread_id,backend._turn_id='thread','turn'
        backend._notification('item/agentMessage/delta',{'threadId':'thread','turnId':'turn',
            'itemId':'incomplete','delta':'This card has not completed. Still writing...'})
        backend._finish('completed')
        QTest.qWait(50)
        self.assertIsNone(self.engine)

    def test_message_queue_has_no_300ms_gap_or_repeated_microphone_pause(self):
        prepared=[]
        def prepare(callback):
            prepared.append(True)
            callback()
        speech=self.speech(prepare=prepare)
        speech.begin_stream()
        for text in ['Hello, mentor. Ready for work.','Next block. More details.','Last block. All done.']:
            speech.enqueue(text)
        self.assertEqual(self.engine.spoken,['Hello, mentor. Ready for work.'])
        self.engine.finish()
        QTest.qWait(50)
        self.assertEqual(self.engine.spoken,['Hello, mentor. Ready for work.','Next block. More details.'])
        self.engine.finish()
        QTest.qWait(50)
        self.assertEqual(self.engine.spoken,['Hello, mentor. Ready for work.','Next block. More details.','Last block. All done.'])
        self.assertEqual(len(prepared),1)
        self.engine.finish()
        self.assertTrue(speech.active)
        QTest.qWait(50)
        self.assertTrue(speech.active)  # Final speaker tail still protects mic.
        speech.enqueue('A late block. More details.')
        QTest.qWait(50)
        self.assertEqual(self.engine.spoken[-1],'A late block. More details.')
        self.assertEqual(len(prepared),1)
        self.engine.finish()
        self.wait(lambda:not speech.active)

    def test_wake_pause_precedes_speech_and_resumes_after_cooldown(self):
        backend=self.backend()
        script=self.root/'wake.py'
        script.write_text('''import json,sys,time
print(json.dumps({'type':'listening'}),flush=True)
for line in sys.stdin:
 v=json.loads(line)
 if v['command']=='pause':
  time.sleep(.05)
  print(json.dumps({'type':'paused','token':v['token']}),flush=True)
 if v['command']=='resume': print(json.dumps({'type':'listening'}),flush=True)
 if v['command']=='shutdown': break
''',encoding='utf-8')
        backend.wake_control.command=[sys.executable,'-u',str(script)]
        backend.wake_control.register=lambda _:None
        with mock.patch('tigo_gui.wake_control.dependencies_available',return_value=True):
            self.assertTrue(backend.wake_control.configure(True,False,'base','ru','',True))
        self.wait(lambda:backend.wake.state=='listening')
        backend.speaker.read('Готово, наставник.')
        self.assertIsNone(self.engine)
        self.wait(lambda:backend.speaker.state=='speaking')
        self.assertEqual(backend.wake.state,'paused')
        self.engine.finish()
        self.assertEqual(backend.wake.state,'paused')
        self.wait(lambda:backend.wake.state=='listening')
        self.assertFalse(backend.speaker.active)
        self.assertEqual(backend.process.processId(),0)

    def test_cancel_manual_recording_during_speech_cannot_start_late_capture(self):
        backend=self.backend()
        backend.speaker.read('Hello, mentor.')
        with mock.patch('tigo_gui.backend.dependencies_available',return_value=True):
            backend.toggleVoice()
        self.assertEqual(backend.voiceState,'starting')
        self.assertTrue(backend.speaker.active)
        backend.cancelVoice()
        self.wait(lambda:not backend.speaker.active)
        self.assertEqual(backend.voice.processId(),0)
        self.assertEqual(backend.voiceState,'idle')

    def test_failed_and_interrupted_requests_are_not_automatically_read(self):
        backend=self.backend('error')
        backend.send('Check this')
        self.wait(lambda:not backend.busy)
        self.assertIsNone(self.engine)
        self.assertFalse(backend.speaker.active)

    def test_interrupted_turn_stops_but_commentary_only_turn_is_spoken(self):
        backend=self.backend('slow')
        backend.send('A task')
        self.wait(lambda:bool(backend._turn_id))
        backend.stop()
        self.wait(lambda:not backend.busy)
        self.assertIsNone(self.engine)
        backend=self.backend('commentary-only')
        backend.send('A task')
        self.wait(lambda:not backend.busy)
        self.assertEqual(self.engine.spoken,['I will inspect the task.'])

    def test_real_qt_mock_plugin_is_only_injected_in_tests(self):
        if 'mock' not in QTextToSpeech.availableEngines():
            self.skipTest('Qt test-only speech plugin is not shipped on this platform')
        speech=Speech(self.settings,engine_factory=lambda parent:QTextToSpeech('mock',parent))
        self.owners.append(speech)
        speech.read('Ready, mentor.')
        self.wait(lambda:speech.state in ('speaking','finishing','idle'))
        self.assertNotEqual(speech.state,'error',speech.status)
        speech.stop()
        self.wait(lambda:not speech.active)

    def test_missing_native_library_keeps_text_gui_available(self):
        script='''import builtins,tempfile
from pathlib import Path
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
app=QApplication([])
original=builtins.__import__
def without_speech(name,*args,**kwargs):
 if name=='PySide6.QtTextToSpeech': raise ImportError('libpulse.so.0 is missing')
 return original(name,*args,**kwargs)
builtins.__import__=without_speech
from tigo_gui.backend import Backend
with tempfile.TemporaryDirectory() as directory:
 settings=QSettings(str(Path(directory)/'ui.ini'),QSettings.IniFormat)
 backend=Backend(settings,codex_home_override=Path(directory)/'codex')
 assert backend.speech.enabled
 backend.speaker.refresh()
 assert backend.speaker.engineKind=='neural'
 assert any('Dmitri Neural' in v['label'] for v in backend.speaker.voices)
 assert backend.speaker.state=='idle'
 backend.speaker.setEngine('system')
 backend.speaker.read('A local voice test')
 assert backend.speaker.state=='error'
 assert 'libpulse' in backend.speaker.status
 assert backend.process.processId()==0
 backend.shutdown()
print('Text backend works without the optional speech module.')
'''
        result=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
