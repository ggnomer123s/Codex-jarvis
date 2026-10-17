"""Detached stdlib-only terminal runner, copied before the application exits.

Interactive sudo/winget/login stay in the terminal. Only a small result record,
never terminal output or credentials, is saved for the next Update Center.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import time


def wait_for_parent(pid, seconds=90):
    if pid <= 1:
        raise ValueError('Invalid application process.')
    if sys.platform == 'win32':
        from ctypes import wintypes
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.restype = wintypes.HANDLE
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        handle = api.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            if ctypes.get_last_error() == 87:  # Already exited.
                return
            raise OSError('Could not wait for the application to exit.')
        api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        try:
            if api.WaitForSingleObject(handle, int(seconds * 1000)) != 0:
                raise TimeoutError('Tigo did not exit; update was not started.')
        finally:
            api.CloseHandle(handle)
        return
    if hasattr(os, 'pidfd_open'):
        try:
            descriptor = os.pidfd_open(pid)
        except ProcessLookupError:
            return
        try:
            if not select.select([descriptor], [], [], seconds)[0]:
                raise TimeoutError('Tigo did not exit; update was not started.')
        finally:
            os.close(descriptor)
        return
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    raise TimeoutError('Tigo did not exit; update was not started.')


def result(path, state, message):
    value = {'state': state, 'message': message, 'time': datetime.now(timezone.utc).isoformat()}
    temporary = path.with_suffix('.tmp')
    try:
        temporary.write_text(json.dumps(value), encoding='utf-8')
        temporary.replace(path)
    except OSError:
        print('[notice] Could not save installation status; inspect this terminal.', flush=True)


def launch(repo):
    command = (['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(repo / 'scripts/tigo-gui-windows.ps1')]
               if sys.platform == 'win32' else ['bash', str(repo / 'scripts/tigo-gui-linux.sh')])
    options = {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if sys.platform == 'win32' else {'start_new_session': True}
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, cwd=repo, **options)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args()
    manifest = Path(args.manifest).resolve()
    info = json.loads(manifest.read_text(encoding='utf-8'))
    repo, bundle = Path(info['repo']).resolve(), manifest.parent
    if not re.fullmatch('[0-9a-f]{40}', info['revision']) or not (repo / '.git').exists():
        raise ValueError('Invalid update manifest.')
    output = Path(info['result'])
    # The GUI exits only after this handshake. No repository mutation yet.
    (bundle / 'ready').write_text('ready', encoding='ascii')
    try:
        deadline = time.monotonic() + 20
        while not (bundle / 'approved').is_file() and time.monotonic() < deadline:
            time.sleep(0.1)
        if not (bundle / 'approved').is_file():
            raise TimeoutError('The application did not approve closing. No update was started.')
        print('Tigo update: waiting for the application to close...', flush=True)
        wait_for_parent(int(info['parent']))
        result(output, 'running', 'Installing the reviewed update in a terminal.')
        env = {**os.environ, 'TIGO_UPDATE_NO_LAUNCH': '1', 'TIGO_UPDATE_EXPECTED_REV': info['revision']}
        command = (['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(bundle / 'update-windows.ps1'), '-RepoPath', str(repo)]
                   if sys.platform == 'win32' else ['bash', str(bundle / 'update-linux.sh'), str(repo)])
        code = subprocess.call(command, env=env)
        if code:
            raise RuntimeError('Installation stopped (exit ' + str(code) + '). Inspect the terminal, then rerun the installer.')
        launch(repo)
        result(output, 'success', 'Installation completed. Tigo launch was requested.')
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as exc:
        result(output, 'failed', str(exc)[:500])
        print('\nTigo update failed: ' + str(exc), flush=True)
        # Keep failures visible even when the old/new app cannot start.
        try:
            input('Press Enter to close this terminal. Your work was not reset or stashed. ')
        except EOFError:
            pass
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
