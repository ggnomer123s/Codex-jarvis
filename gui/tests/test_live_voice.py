"""Live previews precede final transcription; composer revisions are reversible."""
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock
import numpy as np
from PySide6.QtCore import QObject,QSettings,QUrl,QCoreApplication,QEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
import tigo_gui
from tigo_gui.backend import Backend
from tigo_gui.voice import VoiceWorker
APP=QApplication.instance() or QApplication([])


class TestLiveVoice(unittest.TestCase):
    def test_local_and_online_preview_arrive_before_stop_and_final(self):
        for provider in ('local','online'):
            events=[]
            class Stream:
                def __init__(self,**kw): self.callback=kw['callback']
                def __enter__(self):
                    self.callback(bytes(64000),32000,None,None)
                    return self
                def __exit__(self,*a): pass
            sd=types.SimpleNamespace(RawInputStream=Stream,query_devices=lambda *a:{'default_samplerate':16000,'max_input_channels':1},check_input_settings=lambda **kw:None)
            model=mock.Mock()
            model.transcribe.side_effect=[([types.SimpleNamespace(text='partial words')],None),([types.SimpleNamespace(text='correct final words')],None)]
            with mock.patch.dict('sys.modules',{'sounddevice':sd}):
                worker=VoiceWorker('base',provider=provider,model_factory=lambda *a,**kw:model)
            def output(kind,**data):
                events.append({'type':kind,**data})
                if kind=='preview': worker.stop.set()
            worker.output=output
            with mock.patch('tigo_gui.transcription.transcribe_online',side_effect=['partial words','correct final words']):
                worker.command({'command':'record','id':'live','language':'ru','preview':True})
                worker.thread.join(3)
                if worker.thread.is_alive():
                    worker.cancelled.set();worker.stop.set();worker.thread.join(1)
                    self.fail(str(events))
            kinds=[e['type'] for e in events]
            self.assertLess(kinds.index('preview'),kinds.index('transcribing'))
            self.assertEqual(next(e['text'] for e in events if e['type']=='transcript'),'correct final words')

    def test_composer_preview_revision_final_cancel_and_manual_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);settings=QSettings(str(root/'settings.ini'),QSettings.IniFormat)
            settings.setValue('speech/enabled',False)
            backend=Backend(settings,codex_home_override=root/'home')
            engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('bridge',backend)
            engine.load(QUrl.fromLocalFile(str(Path(tigo_gui.__file__).parent/'ui/Main.qml')))
            window=engine.rootObjects()[0];composer=window.findChild(QObject,'composer')
            try:
                backend._voice_state='recording';backend.changed.emit()
                backend.transcriptPreview.emit('first words')
                self.assertEqual(composer.property('text'),'first words')
                self.assertFalse(backend._draft_present)
                backend.transcriptPreview.emit('revised words')
                self.assertEqual(composer.property('text'),'revised words')
                backend.transcriptReady.emit('Final words')
                self.assertEqual(composer.property('text'),'Final words')
                composer.setProperty('text','')
                backend.transcriptPreview.emit('cancel me')
                backend._voice_state='idle';backend.changed.emit()
                self.assertEqual(composer.property('text'),'')
                backend._voice_state='recording';backend.changed.emit()
                backend.transcriptPreview.emit('editable')
                composer.setProperty('text','my edit')
                backend.transcriptPreview.emit('late words')
                self.assertEqual(composer.property('text'),'my edit')
                self.assertTrue(backend._voice_auto_blocked)
            finally:
                backend._voice_state='idle';backend.shutdown();window.close();engine.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);APP.processEvents()
