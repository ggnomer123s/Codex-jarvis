"""Upgrade identities without moving private history or changing desktop grants."""
import os

LEGACY = 'jarvis'


def environment(name, default=None):
    """Prefer TIGO options; accept existing installations' environment variables."""
    return os.environ.get('TIGO_' + name, os.environ.get('JARVIS_' + name, default))


def existing_path(current, previous):
    # Keep absolute clipboard/history references and verified voice caches valid.
    return previous if not current.exists() and previous.exists() else current


def desktop_settings():
    from PySide6.QtCore import QSettings
    current = QSettings('Tigo', 'Desktop')
    if not current.contains('branding/migrated'):
        previous = QSettings('Jarvis', 'Desktop')
        for key in previous.allKeys():
            if not current.contains(key):
                current.setValue(key, previous.value(key))
        current.setValue('branding/migrated', True)
        current.sync()
    return current
