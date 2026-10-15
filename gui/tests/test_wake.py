"""Actual Qt wake-worker ownership, single-instance IPC and window lifecycle."""
from pathlib import Path
import sys
import tempfile
import time
import unittest
import uuid
from unittest import mock

from PySide6.QtCore import QObject, QSettings, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import jarvis_gui
from jarvis_gui.activation import Instance
from jarvis_gui.backend import Backend
from jarvis_gui.wake_control import WakeControl

APP = QApplication.instance() or QApplication([])
FAKE = '''import json, sys, time
def emit(kind, **data):
 print(json.dumps({'type':kind, **data}), flush=True)
emit('listening')
for line in sys.stdin:
 value = json.loads(line)
 if value['command'] == 'pause':
  time.sleep(.06)
  emit('paused', token=value['token'])
  emit('wake')
 elif value['command'] == 'resume': emit('listening')
 elif value['command'] == 'test-wake':
  emit('wake'); emit('wake')
 elif value['command'] == 'shutdown': break
'''


class TestWakeControl(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        script = self.root / 'fake_wake.py'
        script.write_text(FAKE, encoding='utf-8')
        self.settings = QSettings(str(self.root / 'settings.ini'), QSettings.IniFormat)
        self.register = mock.Mock()
        self.control = WakeControl(self.settings, command=[sys.executable, '-u', str(script)], register=self.register)
        self.addCleanup(self.control.shutdown)
        self.names = []
        self.control.activated.connect(lambda: self.names.append('wake'))

    def wait(self, condition):
        deadline = time.monotonic() + 4
        while not condition() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(condition(), self.control.status)

    def enable(self, model='base'):
        with mock.patch('jarvis_gui.wake_control.dependencies_available', return_value=True):
            self.assertTrue(self.control.configure(True, True, model, 'ru', '', True))
        self.wait(lambda: self.control.state == 'listening')

    def test_disabled_by_default_then_wake_cooldown_and_disable(self):
        self.assertFalse(self.control.enabled)
        self.assertEqual(self.control.process.processId(), 0)
        self.register.assert_not_called()
        self.enable()
        self.control._write('test-wake')
        self.wait(lambda: bool(self.names))
        QTest.qWait(80)
        self.assertEqual(self.names, ['wake'])
        self.control.disable()
        self.wait(lambda: self.control.process.processId() == 0)
        self.assertFalse(self.control.enabled)
        self.register.assert_called_with(False)
        self.assertFalse(self.settings.value('wake/enabled', type=bool))

    def test_manual_mic_waits_for_pause_ack_then_resumes_same_process(self):
        self.enable()
        pid = self.control.process.processId()
        released = []
        self.control.reserve_microphone(lambda: released.append(True))
        self.assertEqual(released, [])
        self.wait(lambda: bool(released))
        self.assertEqual(self.control.state, 'paused')
        self.assertEqual(self.names, [])
        self.control.set_suspended(False)
        self.wait(lambda: self.control.state == 'listening')
        self.assertEqual(self.control.process.processId(), pid)

    def test_cancelled_manual_request_does_not_open_mic_on_late_ack(self):
        self.enable()
        released = []
        self.control.reserve_microphone(lambda: released.append(True))
        self.control.set_suspended(False)
        QTest.qWait(180)
        self.assertEqual(released, [])
        self.assertEqual(self.control.state, 'listening')

    def test_reconfigure_restarts_owned_worker_and_cleanup_error_still_disables_mic(self):
        self.enable()
        pid = self.control.process.processId()
        self.enable('tiny')
        self.wait(lambda: self.control.process.processId() not in (pid, 0) and self.control.state == 'listening')
        self.register.side_effect = OSError('Startup directory is read-only')
        self.control.disable()
        self.wait(lambda: self.control.process.processId() == 0)
        self.assertFalse(self.control.enabled)
        self.assertIn('cleanup', self.control.status)

    def test_pause_timeout_kills_only_wake_worker_and_releases_manual_input(self):
        self.enable()
        # A hung worker cannot acknowledge pause.
        self.control._write = lambda *a, **k: None
        released = []
        self.control.reserve_microphone(lambda: released.append(True))
        self.control._pause_timeout()
        self.wait(lambda: bool(released))
        self.assertEqual(self.control.process.processId(), 0)
        self.assertTrue(self.control.enabled)
        self.control.set_suspended(False)
        self.wait(lambda: self.control.state == 'listening')

    def test_background_window_is_hidden_and_close_keeps_enabled_listener(self):
        backend = Backend(self.settings, start_hidden=True, tray_available=True, full_home=self.root / 'full')
        engine = QQmlApplicationEngine()
        warnings = []
        engine.warnings.connect(lambda items: warnings.extend(str(i) for i in items))
        engine.rootContext().setContextProperty('bridge', backend)
        engine.load(QUrl.fromLocalFile(str(Path(jarvis_gui.__file__).parent / 'ui/Main.qml')))
        try:
            self.assertTrue(engine.rootObjects(), warnings)
            window = engine.rootObjects()[0]
            self.assertFalse(window.isVisible())
            backend.wake_control._enabled = True
            backend.wake_control.changed.emit()
            window.showNormal()
            QTest.qWait(80)
            window.close()
            QTest.qWait(80)
            self.assertFalse(window.isVisible())
            self.assertTrue(backend.wake.enabled)
            self.assertEqual(backend.wake.process.processId(), 0)  # No real mic in tests.
            self.assertEqual(warnings, [])
        finally:
            backend.wake_control._enabled = False
            backend.shutdown()
            for window in engine.rootObjects(): window.close()
            engine.deleteLater(); backend.deleteLater(); APP.processEvents()

    def test_backend_manual_voice_waits_for_wake_stream_then_resumes_listener(self):
        voice = self.root / 'manual_voice.py'
        voice.write_text("""import json,sys
print(json.dumps({'type':'ready','microphones':[]}),flush=True)
for line in sys.stdin:
 value=json.loads(line)
 if value['command']=='shutdown': break
 if value['command']=='record': print(json.dumps({'type':'recording','id':value['id']}),flush=True)
""", encoding='utf-8')
        backend = Backend(self.settings, voice_command=[sys.executable, '-u', str(voice)], full_home=self.root / 'full')
        self.addCleanup(backend.shutdown)
        wake = backend.wake_control
        wake.command, wake.register = self.control.command, self.register
        with mock.patch('jarvis_gui.wake_control.dependencies_available', return_value=True):
            wake.configure(True, False, 'base', 'ru', '', True)
        self.wait(lambda: wake.state == 'listening')
        pid = wake.process.processId()
        with mock.patch('jarvis_gui.backend.dependencies_available', return_value=True):
            backend.toggleVoice()
        self.assertEqual(backend.voice.processId(), 0)
        self.wait(lambda: backend.voiceState == 'recording')
        self.assertEqual(wake.state, 'paused')
        backend.cancelVoice()
        self.wait(lambda: wake.state == 'listening')
        self.assertEqual(wake.process.processId(), pid)
        self.assertEqual(backend.process.processId(), 0)

    def test_backend_cancel_before_pause_ack_does_not_start_manual_worker(self):
        backend = Backend(self.settings, full_home=self.root / 'full')
        self.addCleanup(backend.shutdown)
        wake = backend.wake_control
        wake.command, wake.register = self.control.command, self.register
        with mock.patch('jarvis_gui.wake_control.dependencies_available', return_value=True):
            wake.configure(True, False, 'base', 'ru', '', True)
        self.wait(lambda: wake.state == 'listening')
        with mock.patch('jarvis_gui.backend.dependencies_available', return_value=True):
            backend.toggleVoice()
            backend.cancelVoice()
        QTest.qWait(180)
        self.assertEqual(backend.voice.processId(), 0)
        self.assertEqual(backend.voiceState, 'idle')
        self.assertEqual(wake.state, 'listening')

    def test_backend_stop_before_pause_ack_cancels_without_opening_manual_mic(self):
        backend = Backend(self.settings, full_home=self.root / 'full')
        self.addCleanup(backend.shutdown)
        wake = backend.wake_control
        wake.command, wake.register = self.control.command, self.register
        with mock.patch('jarvis_gui.wake_control.dependencies_available', return_value=True):
            wake.configure(True, False, 'base', 'ru', '', True)
        self.wait(lambda: wake.state == 'listening')
        with mock.patch('jarvis_gui.backend.dependencies_available', return_value=True):
            backend.toggleVoice()
            backend.toggleVoice()
        self.wait(lambda: backend.voiceState == 'idle' and wake.state == 'listening')
        self.assertEqual(backend.voice.processId(), 0)


class TestInstance(unittest.TestCase):
    def test_second_launch_activates_owner_and_background_ping_does_not(self):
        name = 'jarvis-test-' + str(uuid.uuid4())
        owner = Instance(namespace=name)
        other = Instance(namespace=name)
        self.addCleanup(owner.close)
        activations = []
        owner.activated.connect(lambda: activations.append(True))
        self.assertTrue(owner.claim())
        self.assertFalse(other.claim())
        QTest.qWait(80)
        self.assertEqual(activations, [True])
        self.assertTrue(other.contact(activate=False))
        QTest.qWait(80)
        self.assertEqual(activations, [True])


if __name__ == '__main__':
    unittest.main()
