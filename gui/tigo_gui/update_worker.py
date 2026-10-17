"""Bounded Git inspection and preparation. Never checkout code during a check."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

ORIGINS = {'https://github.com/ggnomer123s/Codex-jarvis',
           'https://github.com/ggnomer123s/Codex-jarvis.git',
           'git@github.com:ggnomer123s/Codex-jarvis.git'}
SHA = re.compile(r'[0-9a-f]{40}')


def git(repo, *args, limit=512_000):
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never',
           'GIT_SSH_COMMAND': 'ssh -o BatchMode=yes'}
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                            timeout=60, env=env)
    if result.returncode:
        # Never forward credential-helper output, URLs with credentials or raw logs.
        raise ValueError('Git could not complete ' + args[0] + '. Check connectivity and repository access in a terminal.')
    if len(result.stdout) > limit:
        raise ValueError('Repository response exceeds the update size limit.')
    return result.stdout.decode('utf-8', errors='replace').strip()


def validate(repo):
    repo = Path(repo).resolve()
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
        raise ValueError('Updates require the root of the Tigo source checkout.')
    if git(repo, 'remote', 'get-url', 'origin') not in ORIGINS:
        raise ValueError('The origin is not the official Tigo repository.')
    if git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD') != 'main':
        raise ValueError('Select main after saving your work. Other branches are not updated.')
    if git(repo, 'status', '--porcelain'):
        raise ValueError('Local changes found. Commit or save them before updating; nothing was discarded.')
    return repo


def is_ancestor(repo, older, newer):
    result = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', older, newer],
                            capture_output=True, timeout=10)
    if result.returncode not in (0, 1):
        raise ValueError('Could not compare repository history.')
    return result.returncode == 0


def inspect(repo):
    repo = validate(repo)
    git(repo, 'fetch', '--quiet', '--no-tags', 'origin', 'main')
    local = git(repo, 'rev-parse', 'HEAD')
    remote = git(repo, 'rev-parse', 'FETCH_HEAD')
    if not SHA.fullmatch(local) or not SHA.fullmatch(remote):
        raise ValueError('Git did not return a valid revision.')
    if local == remote:
        state, message = 'current', 'You are up to date.'
    elif is_ancestor(repo, local, remote):
        state, message = 'available', 'An update is ready to review.'
    elif is_ancestor(repo, remote, local):
        state, message = 'ahead', 'This checkout contains local commits ahead of main.'
    else:
        raise ValueError('Local and remote history diverged. Resolve this in Git; no files were changed.')
    project = tomllib.loads(git(repo, 'show', remote + ':gui/pyproject.toml'))
    version = project.get('project', {}).get('version', '')
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)', version):
        raise ValueError('The update has no valid application version.')
    notes = git(repo, 'show', remote + ':changes.md', limit=512_000)
    # Stop at the first old entry: report new changes, not the entire project log.
    sections = re.split(r'(?m)^## ', notes)[1:]
    notes = '\n\n'.join('## ' + s.strip() for s in sections[:3])[:18_000]
    count = int(git(repo, 'rev-list', '--count', local + '..' + remote))
    return {'state': state, 'message': message, 'revision': remote, 'local': local,
            'version': version, 'notes': notes, 'commits': count}


def prepare(repo, expected, bundle, platform):
    repo = validate(repo)
    if not SHA.fullmatch(expected):
        raise ValueError('Check for updates before installation.')
    latest = inspect(repo)
    if latest['revision'] != expected or latest['state'] != 'available':
        raise ValueError('The available update changed. Check again before installing.')
    bundle = Path(bundle)
    bundle.mkdir(parents=True, exist_ok=False, mode=0o700)
    names = ['update-windows.ps1'] if platform == 'win32' else ['update-linux.sh', 'update-cachyos.sh']
    for name in names:
        source = git(repo, 'show', expected + ':scripts/' + name)
        (bundle / name).write_text(source + '\n', encoding='utf-8')
    # Run the already-installed launcher outside the venv and source checkout.
    shutil.copyfile(Path(__file__).with_name('update_runner.py'), bundle / 'runner.py')
    return {'bundle': str(bundle.resolve()), 'revision': expected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'prepare'])
    parser.add_argument('--repo', required=True)
    parser.add_argument('--revision', default='')
    parser.add_argument('--bundle', default='')
    parser.add_argument('--platform', default=sys.platform)
    args = parser.parse_args()
    try:
        result = inspect(args.repo) if args.action == 'check' else prepare(args.repo, args.revision, args.bundle, args.platform)
        print(json.dumps({'ok': True, **result}), flush=True)
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'message': str(exc)[:500]}), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
