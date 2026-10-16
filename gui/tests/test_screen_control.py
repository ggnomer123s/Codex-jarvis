"""Screen activity, human cancellation, global-key conflicts and stop IPC."""
import ctypes
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock
import uuid

from PySide6.QtCore import QProcess, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from tigo_gui.activation import Instance
from tigo_gui.backend import Backend
from tigo_gui.control_hotkey import ControlHotkey
from tigo_gui.screen_activity import ScreenActivity, desktop_call
from tigo_gui.screen_overlay import NativeOverlay

APP = QApplication.instance() or QApplication([])


def call(key='one', **extra):
    return {'id': key, 'type': 'mcpToolCall', 'server': 'hypruse', 'tool': 'pointer', **extra}


class TestScreenActivity(unittest.TestCase):
    def test_only_desktop_calls_not_prose_or_generic_shell(self):
        self.assertTrue(desktop_call(call()))
        self.assertTrue(desktop_call(call(server='jarvis-x11', tool='click')))
        self.assertTrue(desktop_call(call(server='other', tool='mcp__hypruse__screenshot')))
        for item in (None, [], {}, call(type='commandExecution', command='hypruse screenshot'),
                     call(server='files', tool='read'), call(type='agentMessage', text='I own the screen'),
                     call(server='windows-mcp', tool='ControlStatus')):
            self.assertFalse(desktop_call(item))

    def test_overlap_tail_and_cancel_do_not_leave_indicator_stuck(self):
        activity = ScreenActivity()
        activity.handle_item('item/started', call())
        activity.handle_item('item/started', call('two'))
        activity.handle_item('item/completed', call())
        activity.handle_item('item/completed', call('foreign'))
        QTest.qWait(1300)
        self.assertTrue(activity.active)
        activity.handle_item('item/completed', {'id': 'two'})
        self.assertTrue(activity.active)
        QTest.qWait(1300)
        self.assertFalse(activity.active)
        activity.handle_item('item/started', call())
        activity.clear()
        activity.handle_item('item/completed', call())
        self.assertFalse(activity.active)

    def test_scoped_notification_and_human_stop_end_owned_task(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = QSettings(str(root/'ui.ini'), QSettings.IniFormat)
            settings.setValue('speech/enabled', False)
            backend = Backend(settings, codex_home_override=root/'codex')
            try:
                backend._begin('codex')
                backend._thread_id, backend._turn_id = 'thread', 'turn'
                def event(thread, turn, item):
                    backend._notification('item/started', {'threadId': thread, 'turnId': turn, 'item': item})
                event('foreign', 'turn', call())
                event('thread', 'old-turn', call())
                self.assertFalse(backend.screen_activity.active)
                event('thread', 'turn', call())
                self.assertTrue(backend.screen_activity.active)
                with mock.patch.object(backend.server, 'close', wraps=backend.server.close) as close:
                    backend.takeControl()
                    close.assert_called_once()
                self.assertFalse(backend.busy)
                self.assertFalse(backend.screen_activity.active)
                self.assertEqual(backend.stage, 'stopped')
                event('thread', 'turn', call('late'))
                self.assertFalse(backend.screen_activity.active)
            finally:
                backend.shutdown()

    def test_native_banner_is_nonexclusive_and_return_button_invokes_stop(self):
        stopped = []
        overlay = NativeOverlay(lambda: stopped.append(True))
        try:
            overlay.show(True, True)
            self.assertEqual(len(overlay.windows), len(APP.screens()) * 5)
            banner = next(w for w in overlay.windows if w.objectName() == 'screenControlBanner')
            edges = [w for w in overlay.windows if w is not banner]
            self.assertTrue(all(w.windowFlags() & Qt.WindowTransparentForInput for w in edges))
            self.assertTrue(banner.windowFlags() & Qt.WindowDoesNotAcceptFocus)
            banner.findChild(QPushButton, 'returnControlButton').click()
            self.assertEqual(stopped, [True])
        finally:
            overlay.hide()
        self.assertEqual(overlay.windows, [])


class TestHotkey(unittest.TestCase):
    def hypr(self):
        key = ControlHotkey()
        key._hypr = '/fake/hyprctl'
        return key

    def test_conflicting_compositor_key_is_not_overwritten(self):
        key = self.hypr()
        with mock.patch.dict('os.environ', {'HYPRLAND_INSTANCE_SIGNATURE': 'test'}), \
             mock.patch('shutil.which', return_value='/fake/hyprctl'), \
             mock.patch.object(key, '_run', return_value=json.dumps([{'modmask': 13, 'key': 'F10', 'dispatcher': 'exec', 'arg': 'user-command'}])) as run:
            key.start()
            self.assertFalse(key.available)
            self.assertEqual(run.call_count, 1)

    def test_own_runtime_key_is_removed_but_user_replacement_is_preserved(self):
        for replaced in (False, True):
            key = self.hypr()
            own = [{'modmask': 13, 'key': 'F10', 'dispatcher': 'exec', 'arg': key._command}]
            other = own + [{'modmask': 13, 'key': 'F10', 'dispatcher': 'exec', 'arg': 'user-command'}]
            with mock.patch.dict('os.environ', {'HYPRLAND_INSTANCE_SIGNATURE': 'test'}), \
                 mock.patch('shutil.which', return_value='/fake/hyprctl'), \
                 mock.patch.object(key, '_run', side_effect=['[]', 'ok', json.dumps(other if replaced else own), 'ok']) as run:
                key.start()
                self.assertTrue(key.available)
                key.close()
                self.assertEqual(run.call_count, 3 if replaced else 4)

    def test_windows_registration_dispatch_and_cleanup_without_input_hooks(self):
        user32 = mock.Mock()
        user32.RegisterHotKey.return_value = 1
        key = ControlHotkey()
        seen = []
        key.activated.connect(lambda: seen.append(True))
        with mock.patch('sys.platform', 'win32'), mock.patch.object(ctypes, 'windll', mock.Mock(user32=user32), create=True):
            key.start()
            self.assertTrue(key.available)
            user32.RegisterHotKey.assert_called_once_with(None, key._id, 0x4007, 0x79)
            from ctypes import wintypes
            msg = wintypes.MSG()
            msg.message, msg.wParam = 0x0312, key._id
            self.assertEqual(key._filter.nativeEventFilter(b'windows_dispatcher_MSG', ctypes.addressof(msg)), (True, 0))
            self.assertEqual(seen, [True])
            key.close()
            user32.UnregisterHotKey.assert_called_once_with(None, key._id)


class TestTakeoverIPC(unittest.TestCase):
    def test_stop_message_reaches_only_existing_same_user_instance(self):
        name = 'screen-test-' + str(uuid.uuid4())
        owner = Instance(namespace=name)
        self.addCleanup(owner.close)
        self.assertTrue(owner.claim())
        stopped, activated = [], []
        owner.controlRequested.connect(lambda: stopped.append(True))
        owner.activated.connect(lambda: activated.append(True))
        code = '''import sys
from PySide6.QtCore import QCoreApplication
from tigo_gui.activation import Instance
app=QCoreApplication([])
raise SystemExit(0 if Instance(namespace=sys.argv[1]).contact(activate=False,takeover=True) else 1)
'''
        process = QProcess()
        process.start(sys.executable, ['-c', code, name])
        deadline = time.monotonic() + 6
        while process.state() != QProcess.NotRunning and time.monotonic() < deadline:
            QTest.qWait(10)
        if process.state() != QProcess.NotRunning:
            process.kill()
            process.waitForFinished(1000)
            self.fail('Stop IPC timed out')
        self.assertEqual(process.exitCode(), 0, bytes(process.readAllStandardError()).decode(errors='replace'))
        self.assertEqual(stopped, [True])
        self.assertEqual(activated, [])
