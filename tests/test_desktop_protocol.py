"""Desktop CLI protocol tests; no Qt, microphone or network required."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gui"))
from jarvis_gui.core import build_arguments, launch_command, parse_event


class TestDesktopProtocol(unittest.TestCase):
    def test_prompt_uses_stdin_and_selected_sandbox(self):
        with tempfile.TemporaryDirectory() as folder:
            args = build_arguments(folder, "high", "workspace-write")
        self.assertEqual(args[-1], "-")
        self.assertIn("workspace-write", args)
        self.assertIn("model_reasoning_effort=high", args)
        self.assertIn('approval_policy="never"', args)
        self.assertNotIn("--ask-for-approval", args)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", args)

    def test_resume_keeps_explicit_session_and_default_effort(self):
        with tempfile.TemporaryDirectory() as folder:
            args = build_arguments(folder, "default", thread_id="session-123")
        self.assertEqual(args[-3:], ["resume", "session-123", "-"])
        self.assertFalse(any("model_reasoning_effort" in arg for arg in args))

    def test_rejects_unrecognized_permissions_and_missing_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                build_arguments(folder, access="danger-full-access")
            with self.assertRaises(ValueError):
                build_arguments(folder, effort="ultra")
            with self.assertRaises(ValueError):
                build_arguments(str(Path(folder) / "missing"))

    def test_windows_npm_launch_avoids_shell_interpolation(self):
        with tempfile.TemporaryDirectory(prefix="jarvis & space ") as folder:
            root = Path(folder)
            script = root / "node_modules/@openai/codex/bin/codex.js"
            script.parent.mkdir(parents=True)
            script.write_text("// fixture")
            with mock.patch("jarvis_gui.core.shutil.which", return_value="node.exe"):
                program, args = launch_command(str(root / "codex.cmd"), ["exec", "-"], windows=True)
            self.assertEqual(program, "node.exe")
            self.assertEqual(args, [str(script), "exec", "-"])
            self.assertNotIn("cmd.exe", args)

    def test_windows_missing_npm_entry_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "Reinstall"):
                launch_command(str(Path(folder) / "codex.cmd"), [], windows=True)

    def test_thread_and_completed_answer(self):
        event = parse_event(json.dumps({"type": "thread.started", "thread_id": "abc"}))
        self.assertEqual((event.kind, event.text), ("thread", "abc"))
        event = parse_event(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "Done"}}))
        self.assertEqual((event.kind, event.text), ("answer", "Done"))

    def test_mcp_activity_and_failed_turn(self):
        event = parse_event(json.dumps({"type": "item.started", "item": {"type": "mcp_tool_call", "server": "jarvis-x11", "tool": "windows"}}))
        self.assertIn("jarvis-x11 / windows", event.text)
        event = parse_event(json.dumps({"type": "turn.failed", "error": {"message": "Login required"}}))
        self.assertEqual((event.kind, event.text), ("error", "Login required"))

    def test_noise_and_non_object_records_are_ignored(self):
        for line in ("not json", "[]", "null", '{"type":"item.started","item":null}'):
            self.assertIsNone(parse_event(line))


if __name__ == "__main__":
    unittest.main()
