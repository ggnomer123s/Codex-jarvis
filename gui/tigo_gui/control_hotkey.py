"""A temporary emergency-stop shortcut; never suppress ordinary user input."""
import ctypes
import json
import os
import shlex
import shutil
import subprocess
import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, Signal

SHORTCUT = 'Ctrl+Alt+Shift+F10'


class WindowsFilter(QAbstractNativeEventFilter):
    def __init__(self, callback, hotkey_id):
        super().__init__()
        self.callback, self.hotkey_id = callback, hotkey_id

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b'windows_generic_MSG', b'windows_dispatcher_MSG'):
            from ctypes import wintypes
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == self.hotkey_id:  # WM_HOTKEY
                self.callback()
                return True, 0
        return False, 0


class ControlHotkey(QObject):
    activated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.available = False
        self.reason = 'Use the Return control button; a global shortcut is unavailable on this desktop.'
        self._filter = None
        self._hypr = None
        self._command = shlex.join([sys.executable, '-m', 'tigo_gui.takeover'])
        self._id = 0x5447

    def _run(self, *args):
        result = subprocess.run([self._hypr, *args], capture_output=True, text=True, timeout=2,
                                check=True)
        return result.stdout

    @staticmethod
    def _matching(binds):
        if not isinstance(binds, list) or len(binds) > 4096:
            raise ValueError('Invalid Hyprland bindings response.')
        return [b for b in binds if isinstance(b, dict) and b.get('modmask') == 13 and b.get('key') == 'F10']

    def verify(self):
        # A compositor config reload removes runtime bindings. Verify before
        # advertising the shortcut again; never overwrite a user's replacement.
        if self.available and self._hypr:
            try:
                matching = self._matching(json.loads(self._run('-j', 'binds')))
                self.available = len(matching) == 1 and matching[0].get('dispatcher') == 'exec' and matching[0].get('arg') == self._command
            except (OSError, subprocess.SubprocessError, ValueError, TypeError):
                self.available = False
            if not self.available:
                self.start()

    def start(self):
        if self.available:
            return
        try:
            if sys.platform == 'win32':
                # Modifiers plus MOD_NOREPEAT; no hooks, input blocking or elevation.
                if not ctypes.windll.user32.RegisterHotKey(None, self._id, 0x4007, 0x79):
                    raise OSError('Emergency shortcut is already registered.')
                self._filter = WindowsFilter(self.activated.emit, self._id)
                QCoreApplication.instance().installNativeEventFilter(self._filter)
            elif os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') and shutil.which('hyprctl'):
                self._hypr = shutil.which('hyprctl')
                matching = self._matching(json.loads(self._run('-j', 'binds')))
                if matching and not (len(matching) == 1 and matching[0].get('dispatcher') == 'exec'
                                     and matching[0].get('arg') == self._command):
                    raise OSError('Emergency shortcut is already in your Hyprland bindings.')
                if not matching:
                    output = self._run('keyword', 'bind', 'CTRL ALT SHIFT,F10,exec,' + self._command)
                    if output.strip() != 'ok':
                        raise OSError('Hyprland did not accept the emergency shortcut.')
            else:
                return
            self.available = True
            self.reason = ''
        except (OSError, subprocess.SubprocessError, ValueError, TypeError) as exc:
            self.reason = str(exc)[:240]

    def close(self):
        if not self.available:
            return
        self.available = False
        if self._filter is not None:
            ctypes.windll.user32.UnregisterHotKey(None, self._id)
            QCoreApplication.instance().removeNativeEventFilter(self._filter)
            self._filter = None
        elif self._hypr:
            try:
                matching = self._matching(json.loads(self._run('-j', 'binds')))
                # Never unbind another user binding added while Tigo was running.
                if len(matching) == 1 and matching[0].get('dispatcher') == 'exec' and matching[0].get('arg') == self._command:
                    self._run('keyword', 'unbind', 'CTRL ALT SHIFT,F10')
            except (OSError, subprocess.SubprocessError, ValueError, TypeError):
                pass
