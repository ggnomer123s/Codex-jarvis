"""History resume, reviewed attachments and inert Markdown through real Qt."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from PySide6.QtCore import QSettings,QUrl
from PySide6.QtGui import QImage,QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tigo_gui.backend import Backend
from tigo_gui.presentation import message_blocks

APP = QApplication.instance() or QApplication([])


class TestConveniences(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo conversation ')
        self.root = Path(self.temp.name)
        self.backends=[]
        self.settings=QSettings(str(self.root/'ui.ini'),QSettings.Format.IniFormat)
        self.settings.setValue('speech/enabled', False)
        self.settings.setValue('folder',str(self.root))
        Path(self.settings.fileName()).with_suffix('.access').write_text('read-only\n')

    def tearDown(self):
        for backend in self.backends:
            backend.shutdown(); backend.deleteLater()
        APP.processEvents()
        self.temp.cleanup()

    def backend(self, scenario='normal'):
        value=Backend(self.settings,codex_command=[sys.executable,'-u',str(Path(__file__).with_name('fake_app_server.py')),scenario,str(self.root/'requests.jsonl')],codex_home_override=self.root/'codex')
        self.backends.append(value)
        return value

    def wait(self, backend):
        deadline=time.monotonic()+5
        while backend.busy and time.monotonic()<deadline:QTest.qWait(10)
        self.assertFalse(backend.busy)

    def requests(self):
        return [json.loads(line)['request'] for line in (self.root/'requests.jsonl').read_text(encoding='utf-8').splitlines()]

    def test_reopen_history_displays_locally_then_resumes_without_replaying(self):
        backend=self.backend()
        self.assertTrue(backend.send('Find the archived needle'))
        self.wait(backend)
        key=backend.historyEntries[0]['id']
        backend.pinConversation(key,True)
        backend.renameConversation(key,'Pinned topic')
        backend.newSession()
        self.assertTrue(backend.send('Second conversation'))
        self.wait(backend)
        backend.searchHistory('ARCHIVED NEEDLE')
        self.assertEqual(backend.historyEntries[0]['title'],'Pinned topic')
        backend.shutdown()
        backend=self.backend()
        self.assertTrue(backend.openConversation(key))
        self.assertEqual(backend.process.processId(),0)
        self.assertEqual(backend.messages[0]['text'],'Find the archived needle')
        self.assertTrue(backend.send('Continue this topic'))
        self.wait(backend)
        methods=[x.get('method') for x in self.requests()]
        self.assertEqual(methods.count('turn/start'),3)
        self.assertEqual(methods.count('thread/resume'),1)
        backend.savePreferences('low','workspace-write','','auto','base')
        self.assertFalse(backend.openConversation(key))
        self.assertEqual(backend.access,'workspace-write')
        self.assertIn('same access mode',backend.notice)

    def test_reviewed_image_and_file_inputs_edit_and_changed_file_rejection(self):
        backend=self.backend()
        text=self.root/'notes & space.txt';text.write_text('a' + 'я' * 5000,encoding='utf-8')
        image_path=self.root/'image.png'
        image=QImage(32,24,QImage.Format.Format_ARGB32);image.fill(0xff22aa99)
        self.assertTrue(image.save(str(image_path)))
        self.assertTrue(backend.addAttachments([QUrl.fromLocalFile(str(image_path)),str(text)]))
        self.assertFalse(backend.addAttachments([QUrl('https://example.com/file.txt')]))
        self.assertEqual(len(backend.attachments),2)
        self.assertTrue(backend.attachments[1]['preview'].startswith('aя'))
        text.write_text('Changed after preview',encoding='utf-8')
        self.assertFalse(backend.send('Inspect'))
        self.assertEqual(backend.process.processId(),0)
        self.assertEqual(len(backend.attachments),2)
        backend.removeAttachment(1)
        self.assertTrue(backend.addAttachments([str(text)]))
        self.assertTrue(backend.send('Inspect'))
        self.wait(backend)
        inputs=next(x['params']['input'] for x in self.requests() if x.get('method')=='turn/start')
        self.assertEqual(inputs,[{'type':'text','text':'Inspect'}, {'type':'localImage','path':str(image_path.resolve())}, {'type':'text','text':'User-selected local file reference (read with available tools and current permissions):\n' + json.dumps({'name':text.name,'path':str(text.resolve())},ensure_ascii=False)}])
        self.assertEqual(backend.attachments,[])
        count=len(self.requests());draft=[]
        backend.draftRequested.connect(draft.append)
        backend.editMessage(0)
        self.assertEqual(draft,['Inspect'])
        self.assertEqual(len(backend.attachments),2)
        self.assertEqual(len(self.requests()),count)
        backend.copyText('print("hello")\n')
        self.assertEqual(QGuiApplication.clipboard().text(),'print("hello")\n')

    def test_clipboard_image_is_previewed_and_not_submitted(self):
        backend=self.backend()
        # QSettings may retain a noncanonical spelling, including Windows short
        # paths, while attachment inspection resolves the selected file path.
        alias=self.root/'alias'
        alias.mkdir()
        backend.history.path=alias/'..'/backend.history.path.name
        image=QImage(8,8,QImage.Format.Format_ARGB32);image.fill(0xff445566)
        QGuiApplication.clipboard().setImage(image)
        backend.pasteImage()
        self.assertEqual(len(backend.attachments),1)
        self.assertEqual(backend.attachments[0]['kind'],'image')
        self.assertEqual(backend.process.processId(),0)
        path = Path(backend.attachments[0]['path'])
        self.assertTrue(path.exists())
        backend.removeAttachment(0)
        self.assertFalse(path.exists())

    def test_markdown_code_copy_data_and_no_external_resource_loading(self):
        blocks=message_blocks('# Heading\n\n- **Bold**\n- [site](https://example.com)\n\n![remote](https://example.com/track.png)\n<img src="file:///private">\n[bad](javascript:alert)\n\n```python\nprint("hello")\n```\n')
        code=next(x for x in blocks if x['kind']=='code')
        self.assertEqual(code['text'],'print("hello")\n')
        rendered=''.join(x['text'] for x in blocks if x['kind']=='markdown')
        self.assertNotIn('<img',rendered)
        self.assertNotIn('href="javascript:',rendered)
        self.assertIn('href="https://example.com"',rendered)
        self.assertIn('<h1',rendered)
        self.assertEqual(message_blocks('~~~text\nunfinished')[0]['text'],'unfinished')
        self.assertEqual(message_blocks('**literal**',False)[0]['kind'],'plain')

    def test_status_explains_failure_and_stopping_is_explicit(self):
        backend=self.backend('error')
        self.assertTrue(backend.send('Check status'))
        self.wait(backend)
        self.assertEqual(backend.taskStatus['title'],'Failed')
        self.assertIn('Login required',backend.taskStatus['detail'])
        self.assertIn(':',backend.taskStatus['elapsed'])
