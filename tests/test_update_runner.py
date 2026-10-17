"""Detached updater runner with harmless installers and a real parent process."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from tigo_gui.update_runner import wait_for_parent

RUNNER = Path(__file__).resolve().parents[1]/'gui/tigo_gui/update_runner.py'


@unittest.skipUnless(os.name != 'nt', 'POSIX detached runner fixture')
class TestUpdateRunner(unittest.TestCase):
    def test_waiting_does_not_kill_a_live_application(self):
        parent = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        try:
            with self.assertRaises(TimeoutError):
                wait_for_parent(parent.pid, 0.03)
            self.assertIsNone(parent.poll())
        finally:
            parent.terminate()
            parent.wait()

    def run_fixture(self, fails=False):
        with tempfile.TemporaryDirectory(prefix='detached update ') as folder:
            root = Path(folder)
            repo, bundle = root/'checkout', root/'bundle'
            (repo/'.git').mkdir(parents=True)
            (repo/'scripts').mkdir()
            bundle.mkdir()
            marker = repo/'launched'
            (repo/'scripts/tigo-gui-linux.sh').write_text('printf launched > '+shlex.quote(str(marker))+'\n')
            (bundle/'update-linux.sh').write_text('''#!/bin/bash
[[ "$TIGO_UPDATE_NO_LAUNCH" == 1 && "$TIGO_UPDATE_EXPECTED_REV" == aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ]] || exit 12
printf updated > "$1/installed"
''' + ('exit 13\n' if fails else 'exit 0\n'))
            parent = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(.2)'])
            try:
                result = root/'last-result.json'
                manifest = bundle/'manifest.json'
                manifest.write_text(json.dumps({'repo':str(repo),'revision':'a'*40,'parent':parent.pid,'result':str(result)}))
                (bundle/'approved').write_text('approved')
                process = subprocess.run([sys.executable,str(RUNNER),'--manifest',str(manifest)],
                                         input='\n',capture_output=True,text=True,timeout=6)
                self.assertTrue((bundle/'ready').exists())
                self.assertEqual((repo/'installed').read_text(),'updated')
                value = json.loads(result.read_text())
                if fails:
                    self.assertEqual(process.returncode,1,process.stdout+process.stderr)
                    self.assertEqual(value['state'],'failed')
                    self.assertIn('13',value['message'])
                    self.assertFalse(marker.exists())
                else:
                    self.assertEqual(process.returncode,0,process.stdout+process.stderr)
                    self.assertEqual(value['state'],'success')
                    deadline=time.monotonic()+2
                    while not marker.exists() and time.monotonic()<deadline:
                        time.sleep(.01)
                    self.assertEqual(marker.read_text(),'launched')
            finally:
                if parent.poll() is None:
                    parent.terminate()
                parent.wait()

    def test_install_waits_for_exit_pins_revision_and_requests_relaunch(self):
        self.run_fixture()

    def test_installer_failure_is_recorded_without_claiming_a_successful_restart(self):
        self.run_fixture(True)
