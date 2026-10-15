"""Exercise the real shared-profile Full Access CLI dispatcher with a fake Codex binary.

No elevated privilege, GUI, network or real Codex command is required.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "jarvis-full-launcher.sh"


@unittest.skipIf(not hasattr(os, "geteuid") or os.geteuid() == 0,
                 "The launcher correctly forbids root; run behavior tests as a normal user")
class TestFullLauncher(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.argsfile = self.base / "args"
        self.homefile = self.base / "codex_home"
        codex = self.bin / "codex"
        codex.write_text(
            '#!/usr/bin/env bash\n'
            'printf "%s\\n" "$@" > "$JARVIS_TEST_ARGS_FILE"\n'
            'printf "%s\\n" "$CODEX_HOME" > "$JARVIS_TEST_HOME_FILE"\n',
            encoding="utf-8",
        )
        codex.chmod(0o755)

    def call(self, *args):
        env = os.environ.copy()
        env.update({
            "HOME": str(self.base),
            "CODEX_HOME": str(self.base / "chosen-codex-home"),
            "PATH": str(self.bin) + os.pathsep + env.get("PATH", ""),
            "JARVIS_TEST_ARGS_FILE": str(self.argsfile),
            "JARVIS_TEST_HOME_FILE": str(self.homefile),
        })
        return subprocess.run(
            ["bash", str(LAUNCHER), *args],
            capture_output=True, text=True, timeout=8, env=env, check=False,
        )

    def check_codex_call(self, expected):
        self.assertEqual(self.argsfile.read_text().splitlines(), expected)
        self.assertEqual(
            self.homefile.read_text().strip(),
            str(self.base / "chosen-codex-home"),
        )

    def test_fast_effort_and_full_access(self):
        result = self.call("fast")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.check_codex_call([
            "--dangerously-bypass-approvals-and-sandbox",
            "--config", "model_reasoning_effort=low",
        ])

    def test_deep_effort_and_full_access(self):
        result = self.call("deep")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.check_codex_call([
            "--dangerously-bypass-approvals-and-sandbox",
            "--config", "model_reasoning_effort=high",
        ])

    def test_normal_inherits_profile_config(self):
        for mode in ((), ("normal",)):
            with self.subTest(mode=mode):
                result = self.call(*mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.check_codex_call(["--dangerously-bypass-approvals-and-sandbox"])

    def test_login_reuses_configured_home(self):
        result = self.call("login")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.check_codex_call(["login"])

    def test_unknown_mode_does_not_start_agent(self):
        result = self.call("magical")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.argsfile.exists())

    def test_extra_args_do_not_start_agent(self):
        result = self.call("fast", "do-something")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.argsfile.exists())

    def test_help_never_starts_agent(self):
        result = self.call("help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("fast", result.stdout)
        self.assertIn("deep", result.stdout)
        self.assertFalse(self.argsfile.exists())


if __name__ == "__main__":
    unittest.main()
