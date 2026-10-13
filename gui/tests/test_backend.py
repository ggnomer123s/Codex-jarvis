"""Exercise the real Qt process bridge with isolated fake CLI/voice workers."""
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from jarvis_gui.backend import Backend

APP = QApplication.instance() or QApplication([])


class TestBackend(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="jarvis-ui-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root / "settings.ini"), QSettings.Format.IniFormat)
        self.settings.setValue("folder", str(self.root))
        self.backends = []

    def tearDown(self):
        for backend in self.backends:
            backend.shutdown()
            backend.deleteLater()
        APP.processEvents()

    def backend(self, source, **kwargs):
        script = self.root / "fake_cli.py"
        script.write_text(source, encoding="utf-8")
        backend = Backend(self.settings, codex_command=[sys.executable, "-u", str(script)], **kwargs)
        self.backends.append(backend)
        return backend

    def wait(self, condition, seconds=6):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            APP.processEvents()
            if condition():
                return
            QTest.qWait(10)
        self.fail("Timed out waiting for the process bridge")

    def test_request_response_and_resume_through_real_process(self):
        backend = self.backend("""
import json, sys
prompt = sys.stdin.read()
print(json.dumps({'type':'thread.started','thread_id':'session-123'}), flush=True)
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':prompt + ' / ' + ('resumed' if 'resume' in sys.argv else 'new')}}), flush=True)
print(json.dumps({'type':'turn.completed'}), flush=True)
""")
        backend.send("--dangerously-bypass-approvals-and-sandbox & literal text")
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.messages[-1]["role"], "assistant")
        self.assertIn("& literal text / new", backend.messages[-1]["text"])
        backend.send("second message")
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.messages[-1]["text"], "second message / resumed")
        backend.newSession()
        self.assertEqual(backend.messages, [])
        self.assertEqual(backend._thread_id, "")

    def test_fragmented_json_utf8_and_final_line_without_newline(self):
        backend = self.backend("""
import json, sys, time
sys.stdin.read()
data=json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'hello \\u2605'}}, ensure_ascii=False).encode()
for fragment in (data[:-2], data[-2:]):
    sys.stdout.buffer.write(fragment); sys.stdout.buffer.flush(); time.sleep(.03)
""")
        backend.send("hello")
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.messages[-1]["text"], "hello \u2605")

    def test_nonzero_exit_displays_failure_and_recovers(self):
        backend = self.backend("import sys; sys.stdin.read(); print('Login required', file=sys.stderr); sys.exit(3)")
        backend.send("hello")
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.messages[-1]["role"], "error")
        self.assertIn("Login required", backend.messages[-1]["text"])
        self.assertEqual(backend.activity, "Request failed")

    def test_stop_releases_busy_state(self):
        backend = self.backend("import sys,time; sys.stdin.read(); print('{\"type\":\"thread.started\",\"thread_id\":\"slow\"}',flush=True); time.sleep(60)")
        backend.send("slow task")
        self.wait(lambda: backend._thread_id == "slow")
        backend.stop()
        self.wait(lambda: not backend.busy)
        self.assertIn("Task stopped", backend.messages[-1]["text"])

    def test_permission_change_starts_fresh_context(self):
        backend = self.backend("pass")
        backend._thread_id = "old-session"
        backend.configure("high", "workspace-write")
        self.assertEqual(backend.access, "workspace-write")
        self.assertEqual(backend._thread_id, "")
        self.assertEqual(self.settings.value("effort"), "high")

    def test_voice_transcript_is_reviewed_and_never_auto_sent(self):
        voice = self.root / "fake_voice.py"
        voice.write_text("""
import json,sys
print(json.dumps({'type':'recording'}),flush=True)
if sys.stdin.readline().strip() == 'stop':
    print(json.dumps({'type':'transcribing'}),flush=True)
    print(json.dumps({'type':'transcript','text':'review this voice request'}),flush=True)
""")
        backend = self.backend("raise RuntimeError('Codex must not be started')", voice_command=[sys.executable, "-u", str(voice)])
        received = []
        backend.transcriptReady.connect(received.append)
        with mock.patch("jarvis_gui.backend.dependencies_available", return_value=True):
            backend.toggleVoice()
            self.wait(lambda: backend.voiceState == "recording")
            backend.toggleVoice()
            self.wait(lambda: backend.voiceState == "idle")
        self.assertEqual(received, ["review this voice request"])
        self.assertEqual(backend.messages, [])
        self.assertFalse(backend.busy)

    def test_missing_voice_dependency_does_not_start_recording(self):
        backend = self.backend("pass")
        with mock.patch("jarvis_gui.backend.dependencies_available", return_value=False):
            backend.toggleVoice()
        self.assertEqual(backend.voiceState, "idle")
        self.assertIn("Voice packages are missing", backend.messages[-1]["text"])


if __name__ == "__main__":
    unittest.main()
