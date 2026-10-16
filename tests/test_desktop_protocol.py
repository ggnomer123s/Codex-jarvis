"""App-server parameter and executable discovery tests; no Qt or network."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gui"))
from tigo_gui.core import thread_options, turn_options, launch_command
from tigo_gui.preferences import LANGUAGES, cached_models


class TestDesktopProtocol(unittest.TestCase):
    def test_full_access_is_an_explicit_server_thread_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            options = thread_options(folder, "full-access", "custom/codex-model")
        self.assertEqual(options["sandbox"], "danger-full-access")
        self.assertEqual(options["approvalPolicy"], "never")
        self.assertEqual(options["model"], "custom/codex-model")

    def test_model_id_is_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                thread_options(folder, "read-only", "--invalid")

    def test_model_catalog_filters_hidden_invalid_and_duplicate_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "models_cache.json"
            path.write_text(json.dumps({"models": [{"slug": "model-a"}, {"slug": "hidden", "visibility": "hide"}, {"slug": "model-a"}, {"slug": "--invalid"}, None, {"id": "provider/model-b"}]}))
            self.assertEqual(cached_models(folder), ["model-a", "provider/model-b"])
            path.write_text("not JSON")
            self.assertEqual(cached_models(folder), [])

    def test_language_presets_include_russian_and_auto_detection(self):
        self.assertEqual(len(LANGUAGES), 16)
        self.assertIn(("ru", "Russian"), LANGUAGES)
        self.assertEqual(LANGUAGES[0][0], "auto")

    def test_prompt_is_structured_data_and_reasoning_is_explicit(self):
        prompt = "--permissions & literal input"
        value = turn_options("session-123", prompt, "high")
        self.assertEqual(value["threadId"], "session-123")
        self.assertEqual(value["input"], [{"type":"text", "text":prompt}])
        self.assertEqual(value["effort"], "high")
        self.assertNotIn("effort", turn_options("session", prompt, "default"))

    def test_rejects_unrecognized_permissions_and_missing_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                thread_options(folder, "unrecognized")
            with self.assertRaises(ValueError):
                turn_options("thread", "hello", "ultra")
            with self.assertRaises(ValueError):
                thread_options(str(Path(folder) / "missing"), "read-only")

    def test_windows_npm_launch_avoids_shell_interpolation(self):
        with tempfile.TemporaryDirectory(prefix="tigo & space ") as folder:
            root = Path(folder)
            script = root / "node_modules/@openai/codex/bin/codex.js"
            script.parent.mkdir(parents=True)
            script.write_text("// fixture")
            with mock.patch("tigo_gui.core.shutil.which", return_value="node.exe"):
                program, args = launch_command(str(root / "codex.cmd"), ["app-server", "--stdio"], windows=True)
            self.assertEqual(program, "node.exe")
            self.assertEqual(args, [str(script), "app-server", "--stdio"])
            self.assertNotIn("cmd.exe", args)

    def test_windows_missing_npm_entry_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "Reinstall"):
                launch_command(str(Path(folder) / "codex.cmd"), [], windows=True)



if __name__ == "__main__":
    unittest.main()
