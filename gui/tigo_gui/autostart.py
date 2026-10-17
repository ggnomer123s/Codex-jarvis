"""User-level login startup registration; never requires elevation."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

MARKER = '# TIGO-CODEX MANAGED: voice activation'
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
RUN_NAME = 'TigoVoiceActivation'
LEGACY_RUN_NAME = 'JarvisVoiceActivation'
LEGACY_MARKER = '# JARVIS-CODEX MANAGED: voice activation'


def background_command():
    python = Path(sys.executable).absolute()  # Preserve the virtualenv symlink.
    if os.name == 'nt' and python.with_name('pythonw.exe').is_file():
        python = python.with_name('pythonw.exe')
    return [str(python), '-m', 'tigo_gui', '--background']


def desktop_quote(value):
    if any(c in value for c in '\n\r\0'):
        raise ValueError('Invalid startup command path.')
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def set_autostart(enabled, command=None, *, platform=None, config_home=None):
    command = command or background_command()
    platform = platform or sys.platform
    if platform == 'win32':
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            try:
                previous, _ = winreg.QueryValueEx(key, RUN_NAME)
            except FileNotFoundError:
                previous = None
            if previous is not None and ' -m tigo_gui --background' not in str(previous):
                raise ValueError('Refusing to replace an unrelated startup registration.')
            if enabled:
                winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, subprocess.list2cmdline(command))
            elif previous is not None:
                winreg.DeleteValue(key, RUN_NAME)
            try:
                legacy, _ = winreg.QueryValueEx(key, LEGACY_RUN_NAME)
            except FileNotFoundError:
                legacy = None
            if legacy is not None and ' -m jarvis_gui --background' in str(legacy):
                winreg.DeleteValue(key, LEGACY_RUN_NAME)
        return
    if not platform.startswith('linux'):
        if enabled:
            raise ValueError('Voice autostart is supported on Linux and Windows 11.')
        return
    base = Path(config_home or os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
    target = base / 'autostart/tigo-voice.desktop'
    legacy = base / 'autostart/jarvis-voice.desktop'
    owned_legacy = (not legacy.is_symlink() and legacy.is_file() and legacy.stat().st_size <= 8192
                    and LEGACY_MARKER in legacy.read_text(encoding='utf-8'))
    if target.is_symlink() or (target.exists() and (target.stat().st_size > 8192 or MARKER not in target.read_text(encoding='utf-8'))):
        raise ValueError('Refusing to replace an unrelated startup file: ' + str(target))
    if not enabled:
        target.unlink(missing_ok=True)
        if owned_legacy:
            legacy.unlink()
        return
    content = ('[Desktop Entry]\n' + MARKER + '\nType=Application\nName=Tigo voice activation\n'
               'Comment=Start the configured Tigo wake listener with its window hidden\nExec=' + ' '.join(map(desktop_quote, command))
               + '\nTerminal=false\nX-GNOME-Autostart-enabled=true\n')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.tigo-voice-', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content)
        os.replace(name, target)
        if owned_legacy:
            legacy.unlink()
    finally:
        Path(name).unlink(missing_ok=True)
