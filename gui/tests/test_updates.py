"""Update Center UI, worker lifecycle and installer readiness handshake."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

from PySide6.QtCore import QObject, QMetaObject, QProcess, QSettings, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import tigo_gui
from tigo_gui.backend import Backend
from tigo_gui.updates import Updates, terminal_command

APP = QApplication.instance() or QApplication([])


class TestUpdates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo update ui ')
        self.root = Path(self.temp.name)
        self.updates = Updates(repo=self.root, storage=self.root/'state')

    def tearDown(self):
        self.updates.close()
        self.updates.deleteLater()
        APP.processEvents()
        self.temp.cleanup()

    def wait(self, condition, seconds=4):
        deadline = time.monotonic()+seconds
        while not condition() and time.monotonic()<deadline:
            QTest.qWait(10)
        self.assertTrue(condition())

    def test_real_worker_reports_invalid_checkout_without_installing(self):
        closed = []
        self.updates.quitRequested.connect(lambda: closed.append(True))
        self.updates.check()
        self.wait(lambda: not self.updates.busy)
        self.assertEqual(self.updates.state, 'error')
        self.assertEqual(closed, [])
        self.assertFalse((self.root/'state').exists())

    def test_worker_response_reaches_properties_and_cancel_reaps_owned_process(self):
        data = {'ok': True, 'state': 'available', 'version': '0.12.0', 'revision': 'a'*40,
                'local': 'b'*40, 'commits': 3, 'notes': 'Synthetic notes', 'message': 'Ready'}
        self.updates._action = 'check'
        self.updates._set('checking', 'Checking')
        self.updates.process.start(sys.executable, ['-c', 'print('+repr(json.dumps(data))+')'])
        self.wait(lambda: self.updates.state == 'available')
        self.assertEqual(self.updates.latestVersion, '0.12.0')
        self.assertEqual(self.updates.commits, 3)
        self.updates._action = 'check'
        self.updates._set('checking', 'Checking')
        self.updates.process.start(sys.executable, ['-c', 'import time; time.sleep(60)'])
        self.assertTrue(self.updates.process.waitForStarted(1000))
        self.updates.cancel()
        self.assertEqual(self.updates.state, 'idle')
        self.assertEqual(self.updates.process.state(), QProcess.NotRunning)

    def test_terminal_arguments_and_no_terminal_failure(self):
        command = ['/a path/python', '/an update/runner.py', '--manifest', '/a file/manifest.json']
        self.assertEqual(terminal_command(command, lambda name: '/bin/kitty' if name == 'kitty' else None), ['/bin/kitty', '-e', *command])
        with self.assertRaisesRegex(ValueError, 'No supported terminal'):
            terminal_command(command, lambda _: None)

    def test_quit_is_emitted_only_after_installer_ready_and_approved(self):
        bundle = self.root/'bundle'
        bundle.mkdir()
        closed = []
        self.updates.quitRequested.connect(lambda: closed.append(True))
        self.updates._revision = 'a'*40
        with mock.patch('subprocess.Popen'), mock.patch('tigo_gui.updates.terminal_command', side_effect=lambda args: args):
            self.updates._launch(bundle)
        self.assertEqual(closed, [])
        self.assertFalse((bundle/'approved').exists())
        (bundle/'ready').write_text('ready')
        self.updates._ready()
        self.assertEqual(closed, [True])
        self.assertEqual((bundle/'approved').read_text(), 'approved')

    def test_terminal_timeout_leaves_gui_open_and_never_approves_update(self):
        bundle = self.root/'bundle'
        bundle.mkdir()
        closed = []
        self.updates.quitRequested.connect(lambda: closed.append(True))
        self.updates._bundle = bundle
        self.updates._deadline = 0
        self.updates._ready()
        self.assertEqual(self.updates.state, 'error')
        self.assertEqual(closed, [])
        self.assertFalse((bundle/'approved').exists())

    def test_failed_approval_write_does_not_close_the_gui(self):
        bundle = self.root/'bundle'
        bundle.mkdir()
        (bundle/'ready').write_text('ready')
        closed = []
        self.updates.quitRequested.connect(lambda: closed.append(True))
        self.updates._bundle = bundle
        with mock.patch.object(Path, 'write_text', side_effect=PermissionError):
            self.updates._ready()
        self.assertEqual(closed, [])
        self.assertEqual(self.updates.state, 'error')
        self.assertFalse((bundle/'approved').exists())


class TestUpdateWindow(unittest.TestCase):
    def test_production_update_center_draft_guard_reduced_motion_and_notice(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = QSettings(str(root/'ui.ini'), QSettings.IniFormat)
            settings.setValue('speech/enabled', False)
            backend = Backend(settings, codex_home_override=root/'codex')
            engine = QQmlApplicationEngine()
            warnings = []
            engine.warnings.connect(lambda items: warnings.extend(str(x) for x in items))
            engine.rootContext().setContextProperty('bridge', backend)
            engine.load(QUrl.fromLocalFile(str(Path(tigo_gui.__file__).parent/'ui/Main.qml')))
            try:
                self.assertTrue(engine.rootObjects(), warnings)
                window = engine.rootObjects()[0]
                window.setWidth(1060)
                window.setHeight(760)
                self.assertTrue(QMetaObject.invokeMethod(window.findChild(QObject, 'updatesButton'), 'clicked'))
                QTest.qWait(260)
                center = window.findChild(QObject, 'updateCenter')
                self.assertTrue(center.property('opened'))
                self.assertLessEqual(center.property('height'), 696)
                backend.updater._revision = 'a'*40
                backend.updater._set('available', 'Synthetic update available')
                button = window.findChild(QObject, 'installUpdateButton')
                composer = window.findChild(QObject, 'composer')
                composer.setProperty('text', 'An unsent draft')
                QTest.qWait(30)
                self.assertFalse(button.property('enabled'))
                with mock.patch.object(backend.updater, 'install') as install:
                    backend.installUpdate(True)
                    install.assert_not_called()
                    composer.setProperty('text', '')
                    QTest.qWait(30)
                    self.assertTrue(button.property('enabled'))
                    self.assertTrue(QMetaObject.invokeMethod(button, 'clicked'))
                    install.assert_called_once()
                self.assertTrue(QMetaObject.invokeMethod(center, 'close'))
                backend.setReducedMotion(True)
                QTest.qWait(150)
                self.assertFalse(window.findChild(QObject, 'activityCore').property('animationRunning'))
                self.assertEqual(str(settings.value('reducedMotion')).lower(), 'true')
                backend._show_notice('Synthetic notice')
                self.assertTrue(QMetaObject.invokeMethod(window.findChild(QObject, 'dismissNoticeButton'), 'clicked'))
                self.assertEqual(backend.notice, '')
                self.assertFalse(QQuickWindow.grabWindow(window).isNull())
                self.assertEqual(warnings, [])
            finally:
                backend.shutdown()
                for window in engine.rootObjects():
                    window.close()
                engine.deleteLater()
                APP.processEvents()
