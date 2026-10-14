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
        backend = Backend(self.settings, codex_command=[sys.executable, "-u", str(script)], full_home=self.root / "full-profile", **kwargs)
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
assert sys.argv[1:] == ['--language','ru','--model','medium']
print(json.dumps({'type':'recording'}),flush=True)
if sys.stdin.readline().strip() == 'stop':
    print(json.dumps({'type':'transcribing'}),flush=True)
    print(json.dumps({'type':'transcript','text':'review this voice request'}),flush=True)
""")
        backend = self.backend("raise RuntimeError('Codex must not be started')", voice_command=[sys.executable, "-u", str(voice)])
        backend.savePreferences("low", "read-only", "", "ru", "medium")
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

    def prepare_profile(self, backend):
        backend.profile.home.mkdir()
        (backend.profile.home / "AGENTS.md").write_text("Full Access test profile")
        (backend.profile.home / "backend.txt").write_text("none")

    def test_full_access_is_explicit_isolated_and_not_restored_on_restart(self):
        backend = self.backend("""
import json,os,sys
sys.stdin.read()
text=json.dumps({'home':os.environ.get('CODEX_HOME',''), 'args':sys.argv[1:]})
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':text}}))
""")
        self.prepare_profile(backend)
        backend._thread_id = "normal-context"
        self.assertTrue(backend.setFullAccess(False))
        self.assertFalse(backend.fullAccess)
        with mock.patch("jarvis_gui.backend.elevated", return_value=False):
            self.assertTrue(backend.setFullAccess(True))
            self.assertEqual(backend._thread_id, "")
            backend.send("test")
            self.wait(lambda: not backend.busy)
        import json
        result = json.loads(backend.messages[-1]["text"])
        self.assertEqual(result["home"], str(backend.profile.home))
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", result["args"])
        backend.setFullAccess(False)
        self.assertFalse(backend.fullAccess)
        backend.send("normal")
        self.wait(lambda: not backend.busy)
        result = json.loads(backend.messages[-1]["text"])
        self.assertNotEqual(result["home"], str(backend.profile.home))
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", result["args"])
        reopened = Backend(self.settings, full_home=backend.profile.home)
        self.backends.append(reopened)
        self.assertFalse(reopened.fullAccess)

    def test_full_access_cannot_be_enabled_through_general_preferences(self):
        backend = self.backend("pass")
        self.assertFalse(backend.savePreferences("low", "full-access", "", "ru", "base"))
        self.assertFalse(backend.fullAccess)

    def test_full_access_refuses_elevated_execution(self):
        backend = self.backend("pass")
        self.prepare_profile(backend)
        with mock.patch("jarvis_gui.backend.elevated", return_value=True):
            self.assertFalse(backend.setFullAccess(True))
        self.assertFalse(backend.fullAccess)

    def test_model_and_voice_preferences_persist_and_reset_model_context(self):
        backend = self.backend("pass")
        backend._thread_id = "previous"
        self.assertTrue(backend.savePreferences("default", "read-only", "test-model", "ru", "small"))
        self.assertEqual(backend._thread_id, "")
        self.assertEqual((backend.model, backend.language, backend.voiceModel), ("test-model", "ru", "small"))
        self.assertEqual(self.settings.value("language"), "ru")
        self.assertEqual(self.settings.value("model"), "test-model")

    def test_separate_login_uses_full_home_without_starting_a_task(self):
        backend = self.backend("import sys; assert sys.argv[1:] == ['login','--device-auth']; print('Complete device sign-in at https://auth.openai.com/codex/device')")
        self.prepare_profile(backend)
        backend.profile.login()
        self.wait(lambda: not backend.profile.busy)
        self.assertEqual(backend.profile.process.processEnvironment().value("CODEX_HOME"), str(backend.profile.home))
        self.assertEqual(backend.profile.loginUrl, "https://auth.openai.com/codex/device")
        self.assertFalse(backend.fullAccess)
        self.assertFalse(backend.busy)

    def test_successful_profile_preparation_activates_only_after_process_finishes(self):
        backend = self.backend("pass")
        installer = self.root / "prepare.py"
        installer.write_text("from pathlib import Path; import sys; p=Path(sys.argv[1]); p.mkdir(); (p/'AGENTS.md').write_text('rules'); (p/'backend.txt').write_text('none')")
        backend.profile._start("install", sys.executable, [str(installer), str(backend.profile.home)])
        self.assertFalse(backend.fullAccess)
        self.wait(lambda: not backend.profile.busy)
        self.assertTrue(backend.fullAccess)

    def test_cancelled_profile_install_does_not_activate_full_access(self):
        backend = self.backend("pass")
        self.prepare_profile(backend)
        installer = self.root / "slow.py"
        installer.write_text("import time; time.sleep(60)")
        backend.profile._start("install", sys.executable, [str(installer)])
        backend.profile.cancel()
        self.wait(lambda: not backend.profile.busy)
        self.assertFalse(backend.fullAccess)

    def test_checkbox_prepares_a_legacy_missing_profile_without_text_input(self):
        backend = self.backend("pass")
        with mock.patch("jarvis_gui.backend.elevated", return_value=False), mock.patch.object(backend.profile, "install") as install:
            backend.setFullAccess(True)
        install.assert_called_once_with()
        self.assertFalse(backend.fullAccess)

    def test_unchecking_restores_retained_normal_workspace_access(self):
        backend = self.backend("pass")
        self.prepare_profile(backend)
        backend.configure("low", "workspace-write")
        with mock.patch("jarvis_gui.backend.elevated", return_value=False):
            backend.setFullAccess(True)
        self.assertTrue(backend.fullAccess)
        self.assertEqual(backend.normalAccess, "workspace-write")
        backend.setFullAccess(False)
        self.assertEqual(backend.access, "workspace-write")


if __name__ == "__main__":
    unittest.main()
