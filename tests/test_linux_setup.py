"""New Linux installer paths without sudo, downloads or real package changes."""
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

import test_update_bootstrap as bootstrap_fixtures

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'scripts/update-linux.sh'


@unittest.skipUnless(os.name != 'nt' and shutil.which('bash'), 'Linux bootstrap fixture')
class TestLinuxSetup(unittest.TestCase):
    def setUp(self):
        self.fixture = bootstrap_fixtures.TestCachyBootstrap(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.temp.cleanup)
        self.f = self.fixture

    @unittest.skipIf(hasattr(os, 'geteuid') and os.geteuid() == 0, 'Installer rejects root')
    def test_debian_full_flow_keeps_path_with_spaces_and_honors_no_launch(self):
        (self.f.bin/'pacman').unlink()
        for name in ('apt-get', 'apt-cache'):
            self.f.tool(name)
        for name in ('bash', 'realpath', 'awk'):
            (self.f.bin/name).symlink_to(shutil.which(name))
        for name, text in [('uname', 'x86_64'), ('getconf', 'glibc 2.41')]:
            file = self.f.bin/name
            file.write_text('#!'+sys.executable+'\nprint('+repr(text)+')\n')
            file.chmod(0o755)
        result = subprocess.run([shutil.which('bash'), str(SCRIPT), str(self.f.repo)],
                                env={**self.f.env, 'PATH':str(self.f.bin), 'TIGO_UPDATE_NO_LAUNCH':'1'},
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        calls = self.f.calls()
        self.assertTrue(any(x['tool']=='sudo' and x['args'][:2]==['apt-get','install'] for x in calls))
        self.assertTrue(any(x['tool']=='git' and 'pull' in x['args'] for x in calls))
        self.assertTrue(any(x['tool']=='uv' and '--frozen' in x['args'] for x in calls))
        self.assertEqual(sum(x['tool']=='installer' for x in calls), 1)
        self.assertFalse(any(x['tool']=='tigo-gui' for x in calls))

    def test_package_dispatch_does_not_run_another_distribution_manager(self):
        for manager in ('apt-get', 'dnf', 'zypper'):
            code = '''source "$1"
command() { [[ "$1" == -v && "$2" == "$TIGO_TEST_MANAGER" ]]; }
sudo() { printf '%s\\n' "$*"; }
apt-cache() { return 1; }
system_packages
'''
            result = subprocess.run(['bash','-c',code,'fixture',str(SCRIPT)],
                                    env={**os.environ,'TIGO_TEST_MANAGER':manager},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn(manager,result.stdout)
            for other in {'apt-get','dnf','zypper'}-{manager}:
                self.assertNotIn(other,result.stdout)

    def test_node_checksum_is_verified_before_private_runtime_installation(self):
        for bad in (False, True):
            with tempfile.TemporaryDirectory(prefix='node fixture ') as folder:
                base = Path(folder)
                archive = 'node-v22.1.0-linux-x64.tar.xz'
                payload = b'#!/bin/sh\nprintf "v22.1.0\\n"\n'
                with tarfile.open(base/archive, 'w:xz') as tar:
                    item = tarfile.TarInfo('node-v22.1.0-linux-x64/bin/node')
                    item.mode, item.size = 0o755, len(payload)
                    tar.addfile(item, io.BytesIO(payload))
                digest = '0'*64 if bad else hashlib.sha256((base/archive).read_bytes()).hexdigest()
                (base/'SHASUMS256.txt').write_text(digest+'  '+archive+'\n')
                tools = base/'tools'
                tools.mkdir()
                for name in ('tar','xz','awk','sha256sum','mkdir','dirname','mv','touch','rm','mktemp'):
                    (tools/name).symlink_to(shutil.which(name))
                (tools/'node').write_text('#!/bin/sh\nexit 1\n')
                (tools/'node').chmod(0o755)
                curl = tools/'curl'
                curl.write_text('#!'+sys.executable+'\nimport os,shutil,sys\nfrom pathlib import Path\na=sys.argv[1:];url=a[a.index("-o")-1];shutil.copyfile(Path(os.environ["TIGO_NODE_FIXTURE"])/url.rsplit("/",1)[-1],a[a.index("-o")+1])\n')
                curl.chmod(0o755)
                result = subprocess.run([shutil.which('bash'),'-c','source "$1"; install_node','fixture',str(SCRIPT)],
                                        env={**os.environ,'PATH':str(tools),'XDG_DATA_HOME':str(base/'data'),'TIGO_NODE_FIXTURE':str(base)},
                                        capture_output=True,text=True,timeout=15)
                installed = base/'data/tigo/runtime/node/bin/node'
                if bad:
                    self.assertNotEqual(result.returncode,0)
                    self.assertFalse(installed.exists())
                else:
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(installed.read_bytes(),payload)
