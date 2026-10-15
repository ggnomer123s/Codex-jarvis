"""Run the GUI installer from outside its checkout with isolated fixture tools."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name != "nt" and shutil.which("bash"), "Linux installer integration")
class TestGuiInstallation(unittest.TestCase):
    def test_installation_updates_shared_profile_from_an_unrelated_directory(self):
        with tempfile.TemporaryDirectory(prefix="jarvis install ") as folder:
            base = Path(folder)
            checkout = base / "checkout with spaces"
            scripts = checkout / "scripts"
            scripts.mkdir(parents=True)
            (checkout / "gui").mkdir()
            shutil.copyfile(ROOT / "scripts/install-gui-linux.sh", scripts / "install-gui-linux.sh")
            profile = base / "prepared-profile"
            tools = base / "tools"
            tools.mkdir()

            def executable(path, body):
                path.write_text(f"#!{sys.executable}\n" + body)
                path.chmod(0o755)

            for name in ("uv", "uvx", "codex"):
                executable(tools / name, "pass\n")
            # Record the real installer's embedded menu script without writing to
            # the runner's home. The shared-profile fixture alone writes temp files.
            executable(tools / "python3", "import json,os,sys\nfrom pathlib import Path\nPath(os.environ['JARVIS_TEST_MENU_RECORD']).write_text(json.dumps({'root':sys.argv[2], 'inputMode':sys.argv[1], 'script':sys.stdin.read()}))\n")
            installer = scripts / "install-linux.sh"
            installer.write_text("#!/usr/bin/env bash\nset -eu\n[[ $# -eq 0 ]]\nmkdir -p \"$JARVIS_TEST_PROFILE_PATH\"\nprintf rules > \"$JARVIS_TEST_PROFILE_PATH/AGENTS.md\"\nprintf none > \"$JARVIS_TEST_PROFILE_PATH/backend.txt\"\n")
            unrelated = base / "unrelated"
            unrelated.mkdir()
            record = base / "menu-record.json"
            environment = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                               JARVIS_TEST_PROFILE_PATH=str(profile), JARVIS_TEST_MENU_RECORD=str(record))
            result = subprocess.run(["bash", str(scripts / "install-gui-linux.sh")], cwd=unrelated,
                                    env=environment, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((profile / "AGENTS.md").is_file())
            self.assertTrue((profile / "backend.txt").is_file())
            self.assertEqual(json.loads(record.read_text())["root"], str(checkout))
            self.assertEqual(json.loads(record.read_text())["inputMode"], "-")


if __name__ == "__main__":
    unittest.main()
