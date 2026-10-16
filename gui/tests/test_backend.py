"""Exercise the real Qt process bridge with isolated fake CLI/voice workers."""
from pathlib import Path
import json
import sys
import tempfile
import time
import unittest
from unittest import mock

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tigo_gui.backend import Backend

APP = QApplication.instance() or QApplication([])


class TestBackend(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tigo-ui-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root / "settings.ini"), QSettings.Format.IniFormat)
        self.settings.setValue('speech/enabled', False)
        self.settings.setValue("folder", str(self.root))
        Path(self.settings.fileName()).with_suffix(".access").write_text("read-only\n")
        self.backends = []

    def tearDown(self):
        for backend in self.backends:
            backend.shutdown()
            backend.deleteLater()
        APP.processEvents()

    def backend(self, source, **kwargs):
        script = self.root / "fake_cli.py"
        script.write_text(source, encoding="utf-8")
        backend = Backend(self.settings, codex_command=[sys.executable, "-u", str(script)], codex_home_override=self.root / "full-profile", **kwargs)
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

    def server_backend(self, scenario="normal", **kwargs):
        log = self.root / (scenario + ".jsonl")
        script = Path(__file__).with_name("fake_app_server.py")
        backend = Backend(self.settings, codex_command=[sys.executable, "-u", str(script), scenario, str(log)], codex_home_override=self.root / "full-profile", **kwargs)
        self.backends.append(backend)
        backend.test_log = log
        return backend

    def requests(self, backend):
        return [json.loads(line) for line in backend.test_log.read_text().splitlines()]

    def test_request_response_reuses_process_and_thread(self):
        backend = self.server_backend()
        prompt = "--dangerously-bypass-approvals-and-sandbox & literal text"
        backend.send(prompt)
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.messages[-1]["text"], prompt)
        pid = backend.process.processId()
        self.assertTrue(backend.serverReady)
        backend.send("second message")
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.process.processId(), pid)
        self.assertEqual(backend.messages[-1]["text"], "second message")
        requests = self.requests(backend)
        methods = [x["request"].get("method") for x in requests]
        self.assertEqual(methods.count("initialize"), 1)
        self.assertEqual(methods.count("thread/start"), 1)
        self.assertEqual(methods.count("turn/start"), 2)
        backend.newSession()
        self.assertEqual(backend.messages, [])
        self.assertEqual(backend._thread_id, "")
        self.assertFalse(backend.canResume)

    def test_fragmented_json_utf8_stream_has_one_authoritative_answer(self):
        backend = self.server_backend("fragmented")
        backend.send("hello")
        self.wait(lambda: not backend.busy)
        self.assertEqual([x["text"] for x in backend.messages if x["role"] == "assistant"], ["hello ★"])

    def test_failed_turn_reports_error_without_destroying_worker(self):
        backend = self.server_backend("error")
        backend.send("hello")
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.messages[-1]["role"], "error")
        self.assertIn("Login required", backend.messages[-1]["text"])
        self.assertEqual(backend.activity, "Request failed")
        self.assertTrue(backend.serverReady)

    def test_stop_interrupts_turn_and_preserves_connection(self):
        backend = self.server_backend("slow")
        backend.send("slow task")
        self.wait(lambda: bool(backend._turn_id))
        pid = backend.process.processId()
        backend.stop()
        self.wait(lambda: not backend.busy)
        self.assertIn("Task stopped", backend.messages[-1]["text"])
        self.assertEqual(backend.process.processId(), pid)
        self.assertIn("turn/interrupt", [x["request"].get("method") for x in self.requests(backend)])

    def test_human_takeover_closes_real_owned_worker_and_does_not_resume(self):
        backend = self.server_backend('slow')
        backend.send('Synthetic task that waits for cancellation')
        self.wait(lambda: bool(backend._turn_id))
        self.assertGreater(backend.process.processId(), 0)
        backend.screen_activity.handle_item('item/started', {'type': 'mcpToolCall', 'id': 'desktop',
                                                           'server': 'hypruse', 'tool': 'pointer'})
        backend.takeControl()
        self.wait(lambda: backend.process.state() == backend.process.ProcessState.NotRunning)
        self.assertFalse(backend.busy)
        self.assertFalse(backend.screen_activity.active)
        self.assertEqual(backend.stage, 'stopped')
        QTest.qWait(150)
        self.assertEqual(backend.process.processId(), 0)

    def test_late_completed_turn_cannot_finish_or_write_into_next_task(self):
        backend = self.server_backend("late")
        backend.send("first")
        self.wait(lambda: not backend.busy)
        backend.send("second")
        self.wait(lambda: not backend.busy)
        self.assertEqual(backend.messages[-1]["text"], "second")
        self.assertNotIn("STALE", str(backend.messages))

    def test_cancel_during_startup_does_not_leave_a_worker(self):
        backend=self.server_backend("slow-init")
        backend.send("cancel immediately")
        backend.stop()
        self.wait(lambda: not backend.busy)
        self.assertFalse(backend.serverReady)
        self.assertEqual(backend.process.state(),backend.process.ProcessState.NotRunning)

    def test_unexpected_approval_is_declined_without_widening_permissions(self):
        backend=self.server_backend("approval")
        backend.send("test")
        self.wait(lambda: not backend.busy)
        self.wait(lambda: any(x["request"].get("id")=="approval" and "result" in x["request"] for x in self.requests(backend)))
        replies=[x["request"] for x in self.requests(backend) if x["request"].get("id")=="approval"]
        self.assertEqual(replies[0]["result"],{"decision":"decline"})
        starts=[x["request"]["params"] for x in self.requests(backend) if x["request"].get("method")=="thread/start"]
        self.assertEqual(starts[0]["sandbox"],"read-only")

    def test_atomic_preferences_reject_invalid_model_without_saving_workflows(self):
        backend=self.backend("pass")
        self.assertFalse(backend.saveAllPreferences("low","read-only","--invalid","ru","base","[]",True,"cpu",1,False,""))
        self.assertFalse(backend.autoReasoning)
        self.assertEqual(backend.voiceBeam,3)

    def test_failed_resume_does_not_silently_start_a_new_thread(self):
        backend=self.server_backend("resume-error")
        backend.checkpoints.save(backend._checkpoint_key(),"saved-thread","interrupted")
        backend.resumePrevious()
        self.wait(lambda: not backend.busy)
        self.assertIn("Thread not available",backend.messages[-1]["text"])
        methods=[x["request"].get("method") for x in self.requests(backend)]
        self.assertNotIn("thread/start",methods)
        self.assertNotIn("turn/start",methods)

    def test_permission_change_starts_fresh_context(self):
        backend = self.backend("pass")
        backend._thread_id = "old-session"
        backend.configure("high", "workspace-write")
        self.assertEqual(backend.access, "workspace-write")
        self.assertEqual(backend._thread_id, "")
        self.assertEqual(self.settings.value("effort"), "high")

    def test_voice_worker_survives_two_recordings_without_auto_submission(self):
        voice = self.root / "fake_voice.py"
        voice.write_text("""
import json,sys
print(json.dumps({'type':'ready','modelLoadMs':12,'microphones':[]}),flush=True)
recording_id = ''
for line in sys.stdin:
    value=json.loads(line)
    if value['command']=='shutdown': break
    if value['command']=='record':
        assert value['language']=='ru' and value['beam']==3
        recording_id=value['id']
        print(json.dumps({'type':'recording','id':recording_id}),flush=True)
    elif value['command']=='stop':
        print(json.dumps({'type':'transcript','id':recording_id,'text':'review this voice request','timings':{'transcribeMs':10}}),flush=True)
        print(json.dumps({'type':'idle','id':recording_id}),flush=True)
""")
        backend = self.backend("raise RuntimeError('Codex must not be started')", voice_command=[sys.executable, "-u", str(voice)])
        backend.savePreferences("low", "read-only", "", "ru", "medium")
        received = []
        backend.transcriptReady.connect(received.append)
        with mock.patch("tigo_gui.backend.dependencies_available", return_value=True):
            pid = None
            for _ in range(2):
                backend.toggleVoice()
                self.wait(lambda: backend.voiceState == "recording")
                if pid is None: pid=backend.voice.processId()
                self.assertEqual(backend.voice.processId(), pid)
                backend.toggleVoice()
                self.wait(lambda: backend.voiceState == "idle")
        self.assertEqual(received, ["review this voice request"] * 2)
        self.assertEqual(backend.messages, [])
        self.assertTrue(backend.voiceReady)
        self.assertFalse(backend.busy)

    def test_missing_voice_dependency_does_not_start_recording(self):
        backend = self.backend("pass")
        with mock.patch("tigo_gui.backend.dependencies_available", return_value=False):
            backend.toggleVoice()
        self.assertEqual(backend.voiceState, "idle")
        self.assertIn("Voice packages are missing", backend.messages[-1]["text"])

    def prepare_profile(self, backend):
        backend.profile.home.mkdir()
        (backend.profile.home / "AGENTS.md").write_text("Full Access test profile")
        (backend.profile.home / "backend.txt").write_text("none")

    def test_access_switches_reuse_one_home_but_restart_runtime(self):
        backend = self.server_backend()
        self.prepare_profile(backend)
        backend.send("normal first")
        self.wait(lambda: not backend.busy)
        normal_pid=backend.process.processId()
        backend._thread_id = "normal-context"
        with mock.patch("tigo_gui.backend.elevated", return_value=False):
            self.assertTrue(backend.setFullAccess(True))
            self.assertEqual(backend._thread_id, "")
            self.assertFalse(backend.serverReady)
            backend.send("full")
            self.wait(lambda: not backend.busy)
        full_pid=backend.process.processId()
        self.assertNotEqual(full_pid, normal_pid)
        requests=self.requests(backend)
        starts=[x for x in requests if x["request"].get("method")=="thread/start"]
        self.assertEqual(starts[-1]["home"], str(backend.profile.home))
        self.assertEqual(starts[-1]["request"]["params"]["sandbox"], "danger-full-access")
        backend.setFullAccess(False)
        self.assertFalse(backend.fullAccess)
        self.assertFalse(backend.serverReady)
        backend.send("normal")
        self.wait(lambda: not backend.busy)
        starts=[x for x in self.requests(backend) if x["request"].get("method")=="thread/start"]
        self.assertEqual(starts[-1]["home"], str(backend.profile.home))
        self.assertEqual(starts[-1]["request"]["params"]["sandbox"], "read-only")
        reopened=Backend(self.settings, codex_home_override=backend.profile.home)
        self.backends.append(reopened)
        self.assertFalse(reopened.fullAccess)

    def test_explicit_resume_recovers_saved_thread_without_replaying_task(self):
        backend = self.server_backend()
        backend.send("a task")
        self.wait(lambda: not backend.busy)
        saved=backend._thread_id
        backend.shutdown()
        reopened=self.server_backend()
        self.assertTrue(reopened.canResume)
        reopened.resumePrevious()
        self.wait(lambda: not reopened.busy)
        self.assertEqual(reopened._thread_id,saved)
        methods=[x["request"].get("method") for x in self.requests(reopened)]
        self.assertEqual(methods.count("turn/start"),1)
        self.assertEqual(methods.count("thread/resume"),1)

    def test_workflow_alias_does_not_use_model_and_verifies_each_step(self):
        backend = self.server_backend()
        workflow=[{"name":"Focus editor","aliases":["focus editor"],"steps":[
            {"call":{"server":"tigo-x11","tool":"focus_window","arguments":{"window_id":"1"}},
             "after":{"call":{"server":"tigo-x11","tool":"windows","arguments":{}},"contains":"Editor ready"}}]}]
        self.assertTrue(backend.saveRuntimePreferences(json.dumps(workflow),False,"cpu",3,False,""))
        backend.send("FOCUS EDITOR")
        self.wait(lambda: not backend.busy)
        methods=[x["request"].get("method") for x in self.requests(backend)]
        self.assertNotIn("turn/start",methods)
        self.assertEqual(methods.count("mcpServer/tool/call"),2)
        self.assertIn("1 steps verified",backend.messages[-1]["text"])

    def test_changed_precondition_stops_before_mutating_action(self):
        backend = self.server_backend("bad-check")
        observe={"call":{"server":"tigo-x11","tool":"windows","arguments":{}},"contains":"Editor ready"}
        workflow=[{"name":"Focus","aliases":["focus"],"steps":[{"call":{"server":"tigo-x11","tool":"focus_window","arguments":{}},"before":observe,"after":observe}]}]
        backend.saveRuntimePreferences(json.dumps(workflow),False,"cpu",3,False,"")
        backend.send("focus")
        self.wait(lambda: not backend.busy)
        tools=[x["request"]["params"].get("tool") for x in self.requests(backend) if x["request"].get("method")=="mcpServer/tool/call"]
        self.assertEqual(tools,["windows"])
        self.assertIn("Precondition changed",backend.messages[-1]["text"])

    def test_failed_postcondition_does_not_repeat_the_action(self):
        backend=self.server_backend("bad-check")
        check={"call":{"server":"tigo-x11","tool":"windows","arguments":{}},"contains":"Editor ready"}
        workflow=[{"name":"Focus","aliases":["focus"],"steps":[{"call":{"server":"tigo-x11","tool":"focus_window","arguments":{}},"after":check,"timeoutMs":500}]}]
        backend.saveRuntimePreferences(json.dumps(workflow),False,"cpu",3,False,"")
        backend.send("focus")
        self.wait(lambda:not backend.busy)
        tools=[x["request"]["params"]["tool"] for x in self.requests(backend) if x["request"].get("method")=="mcpServer/tool/call"]
        self.assertEqual(tools.count("focus_window"),1)
        self.assertGreater(tools.count("windows"),1)
        self.assertIn("not verified",backend.messages[-1]["text"])

    def test_mcp_refusal_is_reported_and_does_not_switch_tools(self):
        backend=self.server_backend("refusal")
        check={"call":{"server":"tigo-x11","tool":"windows","arguments":{}},"contains":"Editor ready"}
        workflow=[{"name":"Focus","aliases":["focus"],"steps":[{"call":{"server":"tigo-x11","tool":"focus_window","arguments":{}},"after":check}]}]
        backend.saveRuntimePreferences(json.dumps(workflow),False,"cpu",3,False,"")
        backend.send("focus")
        self.wait(lambda:not backend.busy)
        tools=[x["request"]["params"]["tool"] for x in self.requests(backend) if x["request"].get("method")=="mcpServer/tool/call"]
        self.assertEqual(tools,["focus_window"])
        self.assertIn("Not authorized",backend.messages[-1]["text"])

    def test_local_commands_do_not_start_codex(self):
        backend=self.backend("raise RuntimeError('must stay local')")
        backend.send("/status")
        self.assertFalse(backend.busy)
        self.assertEqual(backend.process.state(),backend.process.ProcessState.NotRunning)
        self.assertIn("not connected",backend.messages[-1]["text"])

    def test_default_full_access_and_saved_disable_survive_restart(self):
        Path(self.settings.fileName()).with_suffix(".access").unlink()
        backend = self.backend("pass")
        self.assertTrue(backend.fullAccess)
        self.assertEqual(backend.profile.home, backend._normal_home)
        backend.setFullAccess(False)
        self.assertFalse(backend.fullAccess)
        reopened = Backend(self.settings, codex_home_override=backend.profile.home)
        self.backends.append(reopened)
        self.assertFalse(reopened.fullAccess)
        self.assertEqual(reopened._normal_home, backend._normal_home)

    def test_full_access_refuses_elevated_execution(self):
        backend = self.backend("pass")
        self.prepare_profile(backend)
        with mock.patch("tigo_gui.backend.elevated", return_value=True):
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

    def test_login_uses_current_home_without_starting_a_task(self):
        backend = self.backend("import sys; assert sys.argv[1:] == ['login','--device-auth']; print('Complete device sign-in at https://auth.openai.com/codex/device')")
        self.prepare_profile(backend)
        backend.profile.login()
        self.wait(lambda: not backend.profile.busy)
        self.assertEqual(backend.profile.process.processEnvironment().value("CODEX_HOME"), str(backend.profile.home))
        self.assertEqual(backend.profile.loginUrl, "https://auth.openai.com/codex/device")
        self.assertFalse(backend.fullAccess)
        self.assertFalse(backend.busy)

    def test_access_checkbox_never_installs_another_profile(self):
        backend = self.backend("pass")
        with mock.patch("tigo_gui.backend.elevated", return_value=False):
            self.assertTrue(backend.setFullAccess(True))
        self.assertTrue(backend.fullAccess)
        self.assertEqual(backend.profile.process.processId(), 0)
        self.assertEqual(backend.profile.home, backend._normal_home)

    def test_inline_controls_keep_draft_independent_and_use_advertised_reasoning(self):
        backend = self.backend("pass")
        backend._thread_id = "old-thread"
        self.assertTrue(backend.selectModel("test-model"))
        self.assertEqual(backend._thread_id, "")
        self.assertTrue(backend.selectReasoning("xhigh"))
        self.assertEqual(backend.effort, "xhigh")
        backend._model_efforts["test-model"] = ["low", "high"]
        self.assertFalse(backend.selectReasoning("xhigh"))
        self.assertEqual([x["code"] for x in backend.reasoningOptions], ["default", "low", "high"])
        self.assertTrue(backend.selectReasoning("high"))
        self.assertFalse(backend.selectModel("invalid model; command"))

    def test_unchecking_restores_retained_normal_workspace_access(self):
        backend = self.backend("pass")
        self.prepare_profile(backend)
        backend.configure("low", "workspace-write")
        with mock.patch("tigo_gui.backend.elevated", return_value=False):
            backend.setFullAccess(True)
        self.assertTrue(backend.fullAccess)
        self.assertEqual(backend.normalAccess, "workspace-write")
        backend.setFullAccess(False)
        self.assertEqual(backend.access, "workspace-write")


if __name__ == "__main__":
    unittest.main()
