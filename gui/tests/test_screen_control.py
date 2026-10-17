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

from PySide6.QtCore import QObject, QProcess, QRect, QSettings, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from tigo_gui.activation import Instance
from tigo_gui.backend import Backend
from tigo_gui.control_hotkey import ControlHotkey
from tigo_gui.screen_activity import ScreenActivity, desktop_call
from tigo_gui.screen_overlay import NativeOverlay, ScreenOverlay, overlay_bounds

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

    def test_windows_banner_avoids_native_notice_and_taskbars_at_mixed_dpi(self):
        layouts = [
            (QRect(0, 0, 1920, 1080), QRect(0, 0, 1920, 1032), 1.0),
            (QRect(-1280, 0, 1280, 720), QRect(-1280, 0, 1280, 688), 1.5),
            (QRect(0, -1080, 1920, 1080), QRect(64, -1080, 1856, 1080), 2.0),
            (QRect(0, 0, 800, 600), QRect(0, 40, 800, 560), 1.0),
            (QRect(0, 0, 480, 720), QRect(0, 0, 480, 680), 1.5),
        ]
        stopped = []
        overlay = NativeOverlay(lambda: stopped.append(True), platform='win32')
        try:
            for geometry, available, dpr in layouts:
                screen = mock.Mock()
                screen.geometry.return_value = geometry
                screen.availableGeometry.return_value = available
                screen.devicePixelRatio.return_value = dpr
                with self.subTest(geometry=geometry, dpr=dpr), mock.patch('tigo_gui.screen_overlay.QGuiApplication.screens',return_value=[screen]):
                    overlay.show(True, True)
                    APP.processEvents()
                    frame, room = overlay_bounds(geometry, available, True, dpr)
                    banner = next(w for w in overlay.windows if w.objectName() == 'screenControlBanner')
                    self.assertTrue(room.contains(banner.geometry()), (room, banner.geometry()))
                    self.assertEqual(banner.geometry().bottom(), room.bottom())
                    self.assertGreater((frame.left() - geometry.left()) * dpr, 56)
                    for edge in overlay.windows[:-1]:
                        self.assertTrue(frame.contains(edge.geometry()))
                        self.assertTrue(edge.windowFlags() & Qt.WindowTransparentForInput)
                    # Representative upstream top-center ownership notice (physical pixels).
                    native_notice = QRect(geometry.center().x() - round(400/dpr),
                                          geometry.top() + round(56/dpr), round(800/dpr), round(210/dpr))
                    self.assertFalse(native_notice.intersects(banner.geometry()))
                    self.assertTrue(banner.windowFlags() & Qt.WindowDoesNotAcceptFocus)
                    self.assertIn('Ctrl+Alt+Shift+Backspace', banner.findChild(QObject,'screenControlHint').property('text'))
                    banner.findChild(QPushButton,'returnControlButton').click()
            self.assertEqual(len(stopped),len(layouts))
        finally:
            overlay.hide()

    def test_x11_keeps_screen_edges_and_top_center_banner(self):
        geometry = QRect(-800, 20, 800, 600)
        available = QRect(-800, 60, 800, 560)
        frame, _ = overlay_bounds(geometry, available, False, 2)
        self.assertEqual(frame, geometry)
        screen = mock.Mock()
        screen.geometry.return_value, screen.availableGeometry.return_value = geometry, available
        screen.devicePixelRatio.return_value = 2
        overlay = NativeOverlay(lambda: None,platform='linux')
        try:
            with mock.patch('tigo_gui.screen_overlay.QGuiApplication.screens',return_value=[screen]):
                overlay.show(False, True)
            banner = next(w for w in overlay.windows if w.objectName() == 'screenControlBanner')
            self.assertEqual(banner.y(),geometry.top()+16)
            self.assertAlmostEqual(banner.geometry().center().x(),geometry.center().x(),delta=1)
        finally:
            overlay.hide()

    def test_monitor_geometry_workarea_and_dpi_changes_refresh_active_overlay(self):
        class Screen(QObject):
            geometryChanged = Signal(QRect)
            availableGeometryChanged = Signal(QRect)
            logicalDotsPerInchChanged = Signal(float)
        class Hotkey(QObject):
            activated = Signal()
            available = False
            def start(self): pass
            def verify(self): pass
            def close(self): pass
        screen = Screen()
        backend = mock.Mock()
        backend.screen_activity = ScreenActivity()
        backend.language = 'en'
        native = mock.Mock()
        with mock.patch.dict('os.environ',{'WAYLAND_DISPLAY':''}), \
             mock.patch('tigo_gui.screen_overlay.QGuiApplication.screens',return_value=[screen]), \
             mock.patch('tigo_gui.screen_overlay.NativeOverlay',return_value=native):
            overlay = ScreenOverlay(backend,hotkey=Hotkey())
            try:
                backend.screen_activity.handle_item('item/started',call())
                self.assertEqual(native.show.call_count,1)
                screen.geometryChanged.emit(QRect(0,0,1920,1080))
                screen.availableGeometryChanged.emit(QRect(0,0,1920,1032))
                screen.logicalDotsPerInchChanged.emit(144)
                self.assertEqual(native.show.call_count,4)
                backend.screen_activity.clear()
                screen.geometryChanged.emit(QRect())
                self.assertEqual(native.show.call_count,4)
            finally:
                overlay.close()
            screen.logicalDotsPerInchChanged.emit(96)
            self.assertEqual(native.show.call_count,4)


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
