"""One Codex home; a small user preference shared by GUI and CLI launchers."""
import os
from pathlib import Path
import tempfile
from .compat import LEGACY


def codex_home():
    return Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')


def access_file():
    base = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local'))) if os.name == 'nt' else Path.home() / '.local/share'
    # Retain an existing private store, including history and clipboard paths.
    current, previous = base / 'tigo-codex', base / (LEGACY + '-codex')
    if not any((current / name).exists() for name in ('access-mode', 'conversations.sqlite3')):
        if any((previous / name).exists() for name in ('access-mode', 'conversations.sqlite3')):
            return previous / 'access-mode'
    return current / 'access-mode'


def read_access(path):
    try:
        with Path(path).open(encoding='ascii') as stream:
            mode = stream.read(64).strip()
    except FileNotFoundError:
        return 'full-access'
    except (OSError, UnicodeError):
        return 'read-only'
    return mode if mode in ('full-access', 'read-only', 'workspace-write') else 'read-only'


def write_access(path, mode):
    if mode not in ('full-access', 'read-only', 'workspace-write'):
        raise ValueError('Invalid access preference.')
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing to replace a symlinked access preference.')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.tigo-access-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='ascii') as stream:
            stream.write(mode + '\n')
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)
