"""Shared access persistence and actual installer/native-probe regressions."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'gui'))
from tigo_gui.access import codex_home, read_access, write_access


class TestSharedAccess(unittest.TestCase):
    def test_default_full_and_persistent_restricted_modes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'state/access-mode'
            self.assertEqual(read_access(path), 'full-access')
            for mode in ('read-only', 'workspace-write', 'full-access'):
                write_access(path, mode)
                self.assertEqual(read_access(path), mode)
            path.write_text('unrecognized mode')
            self.assertEqual(read_access(path), 'read-only')
            with self.assertRaises(ValueError): write_access(path, 'other')


@unittest.skipUnless(os.name != 'nt' and shutil.which('bash'), 'Linux installer integration')
class TestSharedLinuxInstaller(unittest.TestCase):
    def test_all_session_paths_reuse_codex_home_and_cli_obeys_gui_preference(self):
        for session, desktop, server in [('unknown','unknown',None), ('x11','XFCE','tigo-x11'),
                                          ('wayland','Hyprland','hypruse'), ('wayland','GNOME','tigo-wayland')]:
            with self.subTest(session=session, desktop=desktop), tempfile.TemporaryDirectory(prefix='shared install ') as folder:
                base = Path(folder)
                home, shared, tools = base / 'home', base / 'current codex', base / 'tools'
                home.mkdir(); tools.mkdir()
                log = base / 'calls.jsonl'
                def executable(name, text):
                    p = tools / name
                    p.write_text('#!' + sys.executable + '\n' + text, encoding='utf-8')
                    p.chmod(0o755)
                executable('codex', "import json,os,sys\nwith open(os.environ['CALL_LOG'],'a') as f: f.write(json.dumps({'args':sys.argv[1:],'home':os.environ.get('CODEX_HOME')})+'\\n')\nsys.exit(1 if sys.argv[1:3]==['mcp','get'] else 0)\n")
                for name in ('uv', 'uvx', 'xdotool', 'wmctrl', 'maim', 'hyprctl', 'grim', 'wtype'):
                    executable(name, 'pass\n')
                executable('systemctl', 'raise SystemExit(1)\n')
                env = dict(os.environ, HOME=str(home), CODEX_HOME=str(shared), CALL_LOG=str(log),
                           XDG_SESSION_TYPE=session, XDG_CURRENT_DESKTOP=desktop,
                           PATH=str(tools) + os.pathsep + os.environ['PATH'])
                env.pop('HYPRLAND_INSTANCE_SIGNATURE', None)
                result = subprocess.run(['bash', str(ROOT / 'scripts/install-linux.sh')], cwd=base,
                                        env=env, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((shared / 'AGENTS.md').exists())
                self.assertFalse((home / '.codex').exists())
                self.assertFalse((home / '.local/share/tigo-codex/full-codex-home').exists())
                calls = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
                self.assertTrue(all(x['home'] == str(shared) for x in calls))
                registrations = [x['args'] for x in calls if x['args'][:2] == ['mcp','add']]
                self.assertEqual([x[2] for x in registrations], [server] if server else [])
                if server == 'hypruse': self.assertFalse(any('HYPRUSE_CONFINE' in x for x in registrations[0]))
                if server == 'tigo-x11': self.assertIn('TIGO_X11_ALLOW_INPUT=1', registrations[0])
                # GUI writes this exact shared preference; normal CLI reads it.
                flag = home / '.local/share/tigo-codex/access-mode'
                for mode, expected in [('full-access','--dangerously-bypass-approvals-and-sandbox'),
                                        ('read-only','--sandbox'), ('workspace-write','--sandbox')]:
                    write_access(flag, mode)
                    result = subprocess.run([str(home / '.local/bin/tigo'), 'normal'], env=env,
                                            capture_output=True, text=True, timeout=8)
                    if hasattr(os, 'geteuid') and os.geteuid() == 0 and mode == 'full-access':
                        self.assertNotEqual(result.returncode, 0)
                        continue
                    self.assertEqual(result.returncode, 0, result.stderr)
                    last = json.loads(log.read_text().splitlines()[-1])
                    self.assertEqual(last['args'][0], expected)
                    self.assertEqual(last['home'], str(shared))
                    if mode != 'full-access': self.assertIn(mode, last['args'])


@unittest.skipUnless(os.name == 'nt' and shutil.which('powershell.exe'), 'Windows PowerShell 5 native stderr regression')
class TestWindowsMissingMcp(unittest.TestCase):
    def test_expected_native_stderr_does_not_abort_installer_probe(self):
        with tempfile.TemporaryDirectory(prefix='shared codex ') as folder:
            fake = Path(folder) / 'codex.cmd'
            fake.write_text('@echo off\necho Error: No MCP server named windows-mcp found. 1>&2\nexit /b 1\n', encoding='ascii')
            script = r'''
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($env:TIGO_TEST_INSTALLER, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Installer syntax error' }
$probe = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Test-TigoMcp' }, $true)
if (-not $probe) { throw 'MCP probe helper missing' }
Invoke-Expression $probe.Extent.Text
if (Test-TigoMcp $env:TIGO_TEST_CODEX 'windows-mcp') { throw 'Missing MCP was not detected' }
if ($ErrorActionPreference -ne 'Stop') { throw 'Probe changed the caller error policy' }
Write-Output 'PASS: missing native MCP is a normal probe result'
'''
            encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
            env = dict(os.environ, TIGO_TEST_INSTALLER=str(ROOT / 'scripts/install-windows.ps1'), TIGO_TEST_CODEX=str(fake))
            result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-EncodedCommand',encoded],
                                    env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stdout + result.stderr)
            self.assertIn('PASS:',result.stdout)


if __name__ == '__main__': unittest.main()
