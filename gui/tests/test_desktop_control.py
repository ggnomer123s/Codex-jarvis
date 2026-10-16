"""Read ownership via the existing app-server, without a model or input call."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from jarvis_gui.backend import Backend

APP = QApplication.instance() or QApplication([])


class TestDesktopControl(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.backends = []

    def tearDown(self):
        for backend in self.backends:
            backend.shutdown()
            backend.deleteLater()
        APP.processEvents()
        self.temp.cleanup()

    def backend(self, scenario):
        settings = QSettings(str(self.root/'ui.ini'), QSettings.IniFormat)
        settings.setValue('speech/enabled', False)
        settings.setValue('folder', str(self.root))
        backend = Backend(settings, codex_home_override=self.root/'codex',
                          codex_command=[sys.executable,'-u',str(Path(__file__).with_name('fake_app_server.py')),
                                         scenario,str(self.root/'requests.jsonl')])
        self.backends.append(backend)
        return backend

    def wait(self, condition):
        deadline = time.monotonic()+6
        while not condition() and time.monotonic()<deadline: QTest.qWait(10)
        self.assertTrue(condition())

    def requests(self):
        return [json.loads(line)['request'] for line in (self.root/'requests.jsonl').read_text().splitlines()]

    def test_default_full_access_and_read_only_user_ownership_check(self):
        backend = self.backend('windows-control-user')
        self.assertTrue(backend.fullAccess)
        backend._needs_deep = True
        backend.checkDesktopControl()
        self.wait(lambda:not backend.busy)
        self.assertIn('You currently own', backend.desktopControlStatus)
        self.assertIn('7.5 s', backend.desktopControlStatus)
        self.assertTrue(backend.fullAccess)
        self.assertTrue(backend._needs_deep)
        self.assertFalse(backend.speaker.active)
        requests = self.requests()
        self.assertNotIn('turn/start', [x.get('method') for x in requests])
        calls = [x['params'] for x in requests if x.get('method')=='mcpServer/tool/call']
        self.assertEqual([(x['server'],x['tool'],x['arguments']) for x in calls], [('windows-mcp','ControlStatus',{})])

    def test_text_status_command_does_not_send_a_prompt(self):
        backend = self.backend('windows-control-text')
        self.assertTrue(backend.send('/desktop-status'))
        self.wait(lambda:not backend.busy)
        self.assertIn('You currently own', backend.desktopControlStatus)
        self.assertNotIn('turn/start', [x.get('method') for x in self.requests()])

    def test_missing_tool_never_falls_back_to_input(self):
        backend = self.backend('windows-control-missing')
        backend.checkDesktopControl()
        self.wait(lambda:not backend.busy)
        self.assertIn('does not expose ControlStatus', backend.desktopControlStatus)
        self.assertNotIn('mcpServer/tool/call', [x.get('method') for x in self.requests()])

    def test_status_error_is_not_retried(self):
        backend = self.backend('windows-control-error')
        backend.checkDesktopControl()
        self.wait(lambda:not backend.busy)
        self.assertIn('refused', backend.desktopControlStatus)
        self.assertEqual(sum(x.get('method')=='mcpServer/tool/call' for x in self.requests()),1)

    def test_cancel_pending_status_releases_only_owned_connection(self):
        backend = self.backend('windows-control-slow')
        backend.checkDesktopControl()
        self.wait(lambda:(self.root/'requests.jsonl').exists() and any(x.get('method')=='mcpServer/tool/call' for x in self.requests()))
        backend.stop()
        self.wait(lambda:not backend.busy)
        self.assertEqual(backend.desktopControlStatus,'Check stopped.')
        self.assertFalse(backend.serverReady)
