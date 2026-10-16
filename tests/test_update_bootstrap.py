"""Bootstrap flow without real sudo, package downloads, sign-in or GUI input."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'scripts/update-cachyos.sh'


@unittest.skipUnless(os.name != 'nt' and shutil.which('bash'), 'CachyOS shell fixture')
class TestCachyBootstrap(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo updater ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base/'tools'
        self.bin.mkdir()
        self.home = self.base/'user'
        self.home.mkdir()
        self.repo = self.base/'checkout with spaces'
        self.repo.mkdir()
        (self.repo/'.git').mkdir()
        (self.repo/'scripts').mkdir()
        (self.repo/'gui').mkdir()
        self.log = self.base/'calls.jsonl'
        self.env = dict(os.environ, PATH=str(self.bin)+os.pathsep+os.environ['PATH'],
                        HOME=str(self.home), TIGO_TEST_REPO=str(self.repo),
                        TIGO_TEST_LOG=str(self.log))
        for tool in ('pacman','sudo','git','uv','uvx','python3','node','npm','codex'):
            self.tool(tool)
        launcher = self.home/'.local/bin/tigo-gui'
        launcher.parent.mkdir(parents=True)
        self.tool('launcher', launcher)
        installer = self.repo/'scripts/install-gui-linux.sh'
        installer.write_text('#!/usr/bin/env bash\nexec "'+sys.executable+'" -c \'import os; from pathlib import Path; Path(os.environ["TIGO_TEST_LOG"]).open("a").write("{\\"tool\\":\\"installer\\",\\"args\\":[]}\\n")\'\n')

    def tool(self, name, path=None):
        target = path or self.bin/name
        target.write_text(f'#!{sys.executable}\n'+'''import json,os,sys
from pathlib import Path
tool=Path(sys.argv[0]).name
args=sys.argv[1:]
with Path(os.environ['TIGO_TEST_LOG']).open('a') as log:log.write(json.dumps({'tool':tool,'args':args})+'\\n')
if tool=='git':
 if 'rev-parse' in args:print(os.environ['TIGO_TEST_REPO'])
 elif 'get-url' in args:print(os.environ.get('TIGO_TEST_ORIGIN','https://github.com/ggnomer123s/Codex-jarvis.git'))
 elif 'symbolic-ref' in args:print(os.environ.get('TIGO_TEST_BRANCH','main'))
 elif 'status' in args:print(os.environ.get('TIGO_TEST_DIRTY',''),end='')
if tool=='codex' and args==['login','status']:
 code=int(os.environ.get('TIGO_TEST_LOGIN_NEEDED','0'))
 if code:print('Not logged in' if code==1 else 'Configuration error',file=sys.stderr)
 sys.exit(code)
if tool=='sudo':sys.exit(int(os.environ.get('TIGO_TEST_PACKAGE_EXIT','0')))
if tool=='node':sys.exit(int(os.environ.get('TIGO_TEST_OLD_NODE','0')))
''')
        target.chmod(0o755)

    def run_script(self, **env):
        return subprocess.run(['bash',str(SCRIPT),str(self.repo)],env={**self.env,**env},
                              capture_output=True,text=True,timeout=15)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    @unittest.skipIf(hasattr(os,'geteuid') and os.geteuid()==0, 'Bootstrap deliberately rejects root')
    def test_existing_account_packages_and_ordered_update(self):
        result = self.run_script()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        calls = self.calls()
        package = next(x for x in calls if x['tool']=='sudo')['args']
        self.assertEqual(package[:4],['pacman','-Syu','--needed','--noconfirm'])
        self.assertIn('speech-dispatcher',package)
        self.assertIn('portaudio',package)
        self.assertNotIn('nodejs',package)  # A working user-selected Node is retained.
        self.assertTrue(any(x['tool']=='git' and 'pull' in x['args'] and '--ff-only' in x['args'] for x in calls))
        self.assertTrue(any(x['tool']=='uv' and x['args']==['python','install','3.12'] for x in calls))
        self.assertTrue(any(x['tool']=='uv' and '--python' in x['args'] and '--frozen' in x['args'] for x in calls))
        self.assertEqual(sum(x['tool']=='installer' for x in calls),1)
        self.assertEqual(calls[-1]['tool'],'tigo-gui')
        self.assertNotIn(['login','--device-auth'],[x['args'] for x in calls if x['tool']=='codex'])

    @unittest.skipIf(hasattr(os,'geteuid') and os.geteuid()==0, 'Bootstrap deliberately rejects root')
    def test_failed_packages_do_not_update_or_launch(self):
        result = self.run_script(TIGO_TEST_PACKAGE_EXIT='23')
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(any(x['tool'] in ('git','installer','tigo-gui') for x in self.calls()))

    @unittest.skipIf(hasattr(os,'geteuid') and os.geteuid()==0, 'Bootstrap deliberately rejects root')
    def test_login_runs_only_for_missing_authentication(self):
        result=self.run_script(TIGO_TEST_LOGIN_NEEDED='1')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn(['login','--device-auth'],[x['args'] for x in self.calls() if x['tool']=='codex'])

    @unittest.skipIf(hasattr(os,'geteuid') and os.geteuid()==0, 'Bootstrap deliberately rejects root')
    def test_unknown_login_error_does_not_start_reauthentication(self):
        result=self.run_script(TIGO_TEST_LOGIN_NEEDED='2')
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn(['login','--device-auth'],[x['args'] for x in self.calls() if x['tool']=='codex'])
        self.assertFalse(any(x['tool']=='tigo-gui' for x in self.calls()))

    @unittest.skipIf(hasattr(os,'geteuid') and os.geteuid()==0, 'Bootstrap deliberately rejects root')
    def test_old_shadowing_node_stops_before_checkout_changes(self):
        result=self.run_script(TIGO_TEST_OLD_NODE='1')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('nodejs',next(x for x in self.calls() if x['tool']=='sudo')['args'])
        self.assertFalse(any(x['tool']=='git' for x in self.calls()))

    def test_dirty_or_wrong_repository_is_not_pulled(self):
        for option,value in [('TIGO_TEST_DIRTY',' M README.md\n'),('TIGO_TEST_ORIGIN','https://example.com/other.git'),('TIGO_TEST_BRANCH','custom')]:
            with self.subTest(option=option):
                self.log.unlink(missing_ok=True)
                command=['bash','-c','source "$1"; prepare_checkout "$2"','fixture',str(SCRIPT),str(self.repo)]
                result=subprocess.run(command,env={**self.env,option:value},capture_output=True,text=True,timeout=10)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse(any('pull' in x['args'] or 'clone' in x['args'] for x in self.calls()))


@unittest.skipUnless(os.name=='nt' and shutil.which('powershell.exe'), 'Windows PowerShell 5 bootstrap fixture')
class TestWindowsBootstrap(unittest.TestCase):
    def test_native_stderr_probe_and_exit_codes_without_installing(self):
        with tempfile.TemporaryDirectory(prefix='tigo bootstrap ') as directory:
            path=Path(directory)
            fake=path/'probe.cmd'
            fake.write_text('@echo off\necho Expected probe error 1>&2\nexit /b 9\n')
            fixture=path/'fixture.ps1'
            fixture.write_text('''param([string]$source,[string]$probe)
. $source
if (Test-TigoNative $probe @('login','status')) { throw 'Expected probe failure' }
$caught = $false
try { Invoke-TigoNative $probe @('test') } catch { $caught = $true }
if (-not $caught) { throw 'Required native command failure was ignored' }
$caught = $false
try { Test-TigoLoginNeeded $probe } catch { $caught = $true }
if (-not $caught) { throw 'Unknown status error triggered a new sign-in' }
Write-Output 'Native probe passed'
''')
            result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(fixture),
                                   str(ROOT/'scripts/update-windows.ps1'),str(fake)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Native probe passed',result.stdout)

    def test_checkout_with_spaces_is_protected_without_network(self):
        with tempfile.TemporaryDirectory(prefix='tigo checkout ') as directory:
            path=Path(directory)
            repo=path/'repo with spaces'
            subprocess.run(['git','init','-b','main',str(repo)],check=True,capture_output=True)
            subprocess.run(['git','-C',str(repo),'remote','add','origin','https://github.com/ggnomer123s/Codex-jarvis.git'],check=True,capture_output=True)
            (repo/'local.txt').write_text('Do not remove this work')
            fixture=path/'fixture.ps1'
            fixture.write_text('''param([string]$source,[string]$repo)
. $source
$caught = $false
try { Update-TigoCheckout $repo } catch {
 if ($_.Exception.Message -notlike 'Local changes found*') { throw }
 $caught = $true
}
if (-not $caught) { throw 'Dirty checkout was not rejected' }
Write-Output 'Checkout guard passed'
''')
            result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(fixture),
                                   str(ROOT/'scripts/update-windows.ps1'),str(repo)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Checkout guard passed',result.stdout)
            self.assertEqual((repo/'local.txt').read_text(),'Do not remove this work')
