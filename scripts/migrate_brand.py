#!/usr/bin/env python3
"""Retire only owned pre-Tigo entry points; preserve private data and backups."""
from pathlib import Path
import os
import shutil
import sys

LEGACY_MARKER = 'JARVIS-CODEX MANAGED'


def owned(path):
    try:
        return (not path.is_symlink() and path.is_file() and path.stat().st_size < 100_000
                and LEGACY_MARKER in path.read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError):
        return False  # An unrelated binary/unreadable command is not ours.


def migrate(home=None, source=None):
    home = Path(home or Path.home())
    source = Path(source or Path(__file__).parent)
    bin_dir = home / '.local/bin'
    if os.name != 'nt':
        for suffix in ('', '-codex', '-full', '-gui'):
            old, new = bin_dir / ('jarvis' + suffix), bin_dir / ('tigo' + suffix)
            if owned(old) and new.is_file():
                backup = old.with_name(old.name + '.pre-tigo')
                if not backup.exists():
                    shutil.copy2(old, backup)
                old.write_text('#!/usr/bin/env bash\n# TIGO-CODEX MANAGED - compatibility alias\n'
                               'exec "$HOME/.local/bin/tigo' + suffix + '" "$@"\n')
                old.chmod(0o755)
        desktop = home / '.local/share/applications/jarvis-gui.desktop'
        if owned(desktop) and (desktop.parent / 'tigo-gui.desktop').is_file():
            backup = desktop.with_suffix('.desktop.pre-tigo')
            if not backup.exists():
                shutil.copy2(desktop, backup)
            desktop.unlink()
    else:
        for suffix in ('', '-full'):
            old = bin_dir / ('jarvis' + suffix + '.cmd')
            new = bin_dir / ('tigo' + suffix + '.cmd')
            if owned(old) and new.is_file():
                backup = old.with_suffix('.cmd.pre-tigo')
                if not backup.exists():
                    shutil.copy2(old, backup)
                old.write_text('@echo off\nrem TIGO-CODEX MANAGED - compatibility alias\n'
                               'call "%~dp0tigo' + suffix + '.cmd" %*\n')
    old_watch = home / '.local/share/jarvis-codex/watch.sh'
    if owned(old_watch) and (source / 'watch-linux.sh').is_file():
        shutil.copy2(source / 'watch-linux.sh', old_watch)
    old_watch_windows = home / '.local/share/jarvis-codex/watch-windows.ps1'
    if owned(old_watch_windows) and (source / 'watch-windows.ps1').is_file():
        shutil.copy2(source / 'watch-windows.ps1', old_watch_windows)
    if os.name == 'nt':
        for suffix in ('', '-full'):
            old = bin_dir / ('jarvis' + suffix + '.ps1')
            if owned(old) and (bin_dir / ('tigo' + suffix + '.ps1')).is_file():
                backup = old.with_suffix('.ps1.pre-tigo')
                if not backup.exists():
                    shutil.copy2(old, backup)
                old.write_text('# TIGO-CODEX MANAGED - compatibility alias\n'
                               "& (Join-Path $PSScriptRoot 'tigo" + suffix + ".ps1') @args\nexit $LASTEXITCODE\n")
    skill = home / '.agents/skills/jarvis-desktop/SKILL.md'
    if (not skill.is_symlink() and skill.is_file()
            and 'name: jarvis-desktop' in skill.read_text()
            and (skill.parent.parent / 'tigo-desktop/SKILL.md').is_file()):
        backup = home / '.local/share/tigo-codex/legacy-skill/SKILL.md'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(skill, backup)
        skill.unlink()
        if not any(skill.parent.iterdir()):
            skill.parent.rmdir()


if __name__ == '__main__':
    migrate()
