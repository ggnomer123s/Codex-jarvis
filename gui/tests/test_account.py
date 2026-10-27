"""Native account metadata, quota units and stale-reply guards; no real account."""
import tempfile
from pathlib import Path
import unittest
from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtWidgets import QApplication
from tigo_gui.account import CodexAccount, quota_window

APP = QApplication.instance() or QApplication([])


class Server(QObject):
    disconnected = Signal()
    def __init__(self):
        super().__init__()
        self.connected, self.calls = True, []
    def request(self, method, params, callback, timeout_ms=30000):
        self.calls.append((method, params, callback))


class TestCodexAccount(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = QSettings(str(Path(self.temp.name)/'settings.ini'), QSettings.IniFormat)
        self.server = Server()
        self.account = CodexAccount(self.server, self.settings)
        self.addCleanup(self.account.close)

    def test_native_refresh_precedes_ready_and_usage_reads(self):
        ready = []
        self.account.prepare(ready.append)
        method, params, callback = self.server.calls[0]
        self.assertEqual((method, params), ('account/read', {'refreshToken': True}))
        self.assertEqual(ready, [])
        callback({'requiresOpenaiAuth': True, 'account': {'type': 'chatgpt'}}, None)
        self.assertEqual(ready, [None])
        self.assertEqual([c[0] for c in self.server.calls], ['account/read', 'account/rateLimits/read'])

    def test_missing_durations_and_expired_reset_do_not_invent_recovery(self):
        self.assertFalse(quota_window({'usedPercent': 0}, 300, 1000)['known'])
        item = quota_window({'usedPercent': 100, 'windowDurationMins': 300, 'resetsAt': 999}, 300, 1000)
        self.assertEqual(item['remaining'], 0)
        self.assertIn('awaiting', item['reset'])

    def test_window_roles_and_model_buckets_are_not_assumed(self):
        self.account.update({'rateLimits': {'limitId': 'codex',
            'primary': {'usedPercent': 70, 'windowDurationMins': 10080},
            'secondary': {'usedPercent': 20, 'windowDurationMins': 300}}})
        self.assertEqual([w['remaining'] for w in self.account.windows], [80, 30])
        self.account.update({'rateLimits': {'limitId': 'special', 'normalModelSlug': 'model-special',
            'primary': {'usedPercent': 90, 'windowDurationMins': 300}}})
        self.assertEqual(self.account.windows[0]['remaining'], 80)
        self.account.set_model('model-special')
        self.assertEqual(self.account.windows[0]['remaining'], 10)
        self.assertFalse(self.account.windows[1]['known'])

    def test_hide_persists_and_stops_polling(self):
        self.account.refresh()
        self.assertTrue(self.account.poll.isActive())
        self.account.setVisible(False)
        self.assertFalse(self.account.poll.isActive())
        self.assertFalse(self.account.clock.isActive())
        reopened = CodexAccount(self.server, self.settings)
        self.addCleanup(reopened.close)
        self.assertFalse(reopened.visible)

    def test_account_change_and_disconnect_reject_old_usage(self):
        self.account.refresh()
        old = self.server.calls[-1][2]
        self.account.notification('account/updated', {'authMode': 'chatgpt'})
        old({'rateLimits': {'primary': {'usedPercent': 0, 'windowDurationMins': 300}}}, None)
        self.assertFalse(self.account.windows[0]['known'])
        current = self.server.calls[-1][2]
        self.server.connected = False
        self.server.disconnected.emit()
        current({'rateLimits': {'primary': {'usedPercent': 0, 'windowDurationMins': 300}}}, None)
        self.assertFalse(self.account.windows[0]['known'])

    def test_401_requires_sign_in_without_replaying_a_task(self):
        ready = []
        self.account.prepare(ready.append)
        self.server.calls[0][2](None, 'workspace routing discovery unauthorized (401)')
        self.assertTrue(self.account.needsSignIn)
        self.assertIn('not automatically retried', ready[0])
        self.account.refresh()
        self.assertEqual(len(self.server.calls), 1)
