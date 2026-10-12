"""Stdlib-only tests for JARVIS opt-in memory (no Codex, mic, or network)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "jarvis_memory.py"


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "private-memory"
        self.env = dict(os.environ, JARVIS_MEMORY_DIR=str(self.directory))

    def call(self, *args, input_text=None):
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            input=input_text, capture_output=True, text=True, env=self.env, timeout=10,
        )

    def test_empty_search(self):
        result = self.call("search", "dolphin")
        self.assertEqual(result.returncode, 0)
        self.assertIn("No matching", result.stdout)

    def test_requires_explicit_save(self):
        result = self.call("add", input_text="Dolphin issue\nVerified restart\nKDE\nno\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.directory / "confirmed-fixes.json").exists())

    def test_add_search_forget_flow(self):
        added = self.call("add", input_text="Dolphin issue\nVerified restart\nKDE\nYES\n")
        self.assertEqual(added.returncode, 0, added.stderr)
        data = json.loads((self.directory / "confirmed-fixes.json").read_text())
        self.assertEqual(len(data), 1)
        item_id = data[0]["id"]
        self.assertTrue(data[0]["verified_by_user"])
        self.assertIn("Dolphin issue", self.call("search", "dolphin").stdout)
        self.assertIn("No matching", self.call("search", "firefox").stdout)
        self.assertIn(item_id, self.call("list").stdout)
        aborted = self.call("forget", item_id, input_text="no\n")
        self.assertNotEqual(aborted.returncode, 0)
        self.assertEqual(len(json.loads((self.directory / "confirmed-fixes.json").read_text())), 1)
        removed = self.call("forget", item_id, input_text="DELETE\n")
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertEqual(json.loads((self.directory / "confirmed-fixes.json").read_text()), [])
        if os.name != "nt":
            self.assertEqual((self.directory / "confirmed-fixes.json").stat().st_mode & 0o777, 0o600)

    def test_cannot_save_blank_entries(self):
        result = self.call("add", input_text="\nsolution\ncontext\nYES\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.directory / "confirmed-fixes.json").exists())


if __name__ == "__main__":
    unittest.main()
