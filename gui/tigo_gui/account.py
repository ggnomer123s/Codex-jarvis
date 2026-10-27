"""Native Codex token refresh and honest, transient subscription usage status."""
from datetime import datetime
import math
import re
import time
from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot


def authorization_error(message):
    return bool(re.search(r'\b401\b|unauthori[sz]ed|not logged in|sign.in required|authentication required|token (?:has )?expired', str(message), re.I))


AUTH_MESSAGE = ('Codex authorization failed (401). Use Sign in to Codex to renew the existing login. '
                'If it persists, check your ChatGPT workspace access and update Codex CLI. '
                'The task was not automatically retried.')


def clean_snapshot(value):
    result = {'_received': time.time()}
    for key in ('primary', 'secondary'):
        window = value.get(key)
        if isinstance(window, dict):
            result[key] = {k: window.get(k) for k in ('usedPercent', 'windowDurationMins', 'resetsAt')}
    model = value.get('normalModelSlug')
    if isinstance(model, str) and len(model) <= 128:
        result['normalModelSlug'] = model
    return result


def quota_window(value, minutes, now):
    """Do not guess window duration, missing percentages or reset recovery."""
    result = {'label': '5 hours' if minutes == 300 else 'Weekly', 'known': False,
              'remaining': 0., 'summary': 'Unavailable', 'reset': 'Reset time unavailable'}
    if not isinstance(value, dict) or value.get('windowDurationMins') != minutes:
        return result
    used = value.get('usedPercent')
    if type(used) not in (int, float) or not math.isfinite(used) or used < 0:
        return result
    left = max(0., 100. - used)
    result.update(known=True, remaining=left, summary=f'{left:g}% left')
    reset = value.get('resetsAt')
    if type(reset) in (int, float) and math.isfinite(reset) and 0 < reset < 32_503_680_000:
        seconds = max(0, int(reset-now))
        if seconds == 0:
            result['reset'] = 'Reset due; awaiting Codex update'
        else:
            days, hours, minutes_left = seconds//86400, seconds//3600 % 24, seconds//60 % 60
            countdown = f'{days}d {hours}h' if days else (f'{hours}h {minutes_left}m' if hours else f'{max(1, minutes_left)}m')
            local = datetime.fromtimestamp(reset).astimezone().strftime('%a %H:%M')
            result['reset'] = f'Resets in {countdown} ({local})'
    return result


class CodexAccount(QObject):
    changed = Signal()

    def __init__(self, server, settings, parent=None):
        super().__init__(parent)
        self.server, self.settings = server, settings
        self._visible = str(settings.value('showUsageLimits', True)).lower() == 'true'
        self._auth_required = self._preparing = self._reading = self._closing = False
        self._generation = 0
        self._usage_epoch = 0
        self._snapshots = {}
        self._default_snapshot = None
        self._model = ''
        self._updated = 0.
        self._error = False
        self._quota_supported = True
        self._status = 'Connect to Codex to read subscription usage.'
        self.poll = QTimer(self)
        self.poll.setInterval(60000)
        self.poll.timeout.connect(self.refresh)
        self.clock = QTimer(self)
        self.clock.setInterval(15000)
        self.clock.timeout.connect(self.changed.emit)
        if self._visible: self.clock.start()
        server.disconnected.connect(self.disconnected)

    @Property(bool, notify=changed)
    def visible(self): return self._visible
    @Property(bool, notify=changed)
    def needsSignIn(self): return self._auth_required
    @Property(bool, notify=changed)
    def preparing(self): return self._preparing
    @Property(bool, notify=changed)
    def loading(self): return self._preparing or self._reading
    @Property(str, notify=changed)
    def status(self): return self._status
    @Property(str, notify=changed)
    def authMessage(self): return AUTH_MESSAGE if self._auth_required else ''
    @Property(bool, notify=changed)
    def stale(self):
        updated = self._snapshot().get('_received', 0.)
        return bool(updated) and (self._error or not self.server.connected or time.time()-updated > 120)
    @Property(str, notify=changed)
    def updatedLabel(self):
        updated = self._snapshot().get('_received', 0.)
        if not updated: return 'No usage snapshot yet'
        prefix = 'Last known' if self.stale else 'Updated'
        return prefix + ' ' + datetime.fromtimestamp(updated).astimezone().strftime('%H:%M:%S')

    @Property(str, notify=changed)
    def scope(self):
        return self._snapshot().get('normalModelSlug') or 'Codex account'

    def _snapshot(self):
        selected = next((s for key, s in self._snapshots.items()
                         if self._model and (key == self._model or s.get('normalModelSlug') == self._model)), None)
        return selected or self._snapshots.get('codex') or self._default_snapshot or {}

    @Property('QVariantList', notify=changed)
    def windows(self):
        snapshot = self._snapshot()
        values = [snapshot.get('primary'), snapshot.get('secondary')]
        now = time.time()
        return [quota_window(next((v for v in values if isinstance(v, dict) and v.get('windowDurationMins') == duration), None), duration, now)
                for duration in (300, 10080)]

    @Slot(bool)
    def setVisible(self, value):
        self._visible = value
        self.settings.setValue('showUsageLimits', value)
        if value:
            self.clock.start()
            if self.server.connected: self.refresh()
        else:
            self.clock.stop()
            self.poll.stop()
        self.changed.emit()

    def set_model(self, model):
        self._model = model
        self.changed.emit()

    def require_sign_in(self, message=''):
        self._usage_epoch += 1
        self._reading = False
        self._auth_required = self._error = True
        self._status = AUTH_MESSAGE
        self.poll.stop()
        self.changed.emit()
        return AUTH_MESSAGE

    def prepare(self, callback):
        """Refresh managed auth before thread/routing discovery, never replay tasks."""
        self._generation += 1
        self._usage_epoch += 1
        generation = self._generation
        self._snapshots, self._default_snapshot, self._updated = {}, None, 0.
        self._reading = False
        self._preparing = True
        self._status = 'Refreshing the existing Codex session...'
        self.changed.emit()

        def returned(result, error):
            if self._closing or generation != self._generation or not self.server.connected:
                return
            self._preparing = False
            if error and authorization_error(error):
                callback(self.require_sign_in(error))
                return
            if isinstance(result, dict) and result.get('requiresOpenaiAuth') and result.get('account') is None:
                callback(self.require_sign_in())
                return
            # Older/provider-specific servers may not expose account/read.
            # Let their actual task response decide auth; never invent a login.
            self._auth_required = self._error = False
            account = result.get('account') if isinstance(result, dict) else None
            kind = account.get('type') if isinstance(account, dict) else None
            self._quota_supported = kind not in ('apiKey', 'amazonBedrock') and not (
                isinstance(result, dict) and result.get('requiresOpenaiAuth') is False and account is None)
            self._status = 'Reading Codex usage...' if self._visible else 'Usage panel hidden.'
            if self._visible: self.refresh()
            self.changed.emit()
            callback(None)

        self.server.request('account/read', {'refreshToken': True}, returned, 30000)

    @Slot()
    def refresh(self):
        if self._closing or not self._visible or self._preparing or self._reading or self._auth_required or not self.server.connected:
            return
        if not self._quota_supported:
            self._status = 'Subscription quotas are unavailable for this API-key/provider account.'
            self.changed.emit()
            return
        generation = self._generation
        usage_epoch = self._usage_epoch
        self._reading = True
        self._status = 'Reading Codex usage...'
        self.poll.start()
        self.changed.emit()

        def returned(result, error):
            if self._closing or generation != self._generation or usage_epoch != self._usage_epoch or not self.server.connected:
                return
            self._reading = False
            if error:
                if authorization_error(error):
                    self.require_sign_in(error)
                else:
                    self._error = True
                    self._status = 'Usage unavailable: ' + str(error)[:220]
                    self.changed.emit()
                return
            if not self.update(result):
                self._error = True
                self._status = 'Codex did not provide subscription quotas for this account/provider.'
                self.changed.emit()

        self.server.request('account/rateLimits/read', {'excludeResetCreditDetails': True}, returned, 15000)

    def update(self, value):
        if not isinstance(value, dict): return False
        snapshot, buckets = value.get('rateLimits'), value.get('rateLimitsByLimitId')
        supplied = False
        if isinstance(buckets, dict):
            for key, item in list(buckets.items())[:32]:
                if isinstance(key, str) and len(key) <= 256 and isinstance(item, dict):
                    self._snapshots[key] = clean_snapshot(item)
                    supplied = True
        if isinstance(snapshot, dict):
            clean = clean_snapshot(snapshot)
            key = snapshot.get('limitId')
            if isinstance(key, str) and key and len(key) <= 256:
                self._snapshots[key] = clean
            # A named model bucket must not replace the common Codex bucket.
            if not key or key == 'codex':
                self._default_snapshot = clean
            supplied = True
        if supplied:
            while len(self._snapshots) > 32:
                oldest = next(k for k in self._snapshots if k != 'codex')
                self._snapshots.pop(oldest)
            self._updated = time.time()
            self._error = False
            self._status = ('Live Codex usage; refreshes every minute and on account updates.'
                            if any(w['known'] for w in self.windows)
                            else 'Codex did not provide 5-hour/weekly limits for this account/provider.')
            self.changed.emit()
        return supplied

    def notification(self, method, params):
        if method == 'account/rateLimits/updated':
            if not self._auth_required: self.update(params)
            return True
        if method == 'account/updated':
            self._usage_epoch += 1
            self._reading = False
            self._snapshots, self._default_snapshot, self._updated = {}, None, 0.
            self.refresh()
            self.changed.emit()
            return True
        return False

    def disconnected(self):
        self._generation += 1
        self._usage_epoch += 1
        self._preparing = self._reading = False
        self.poll.stop()
        if not self._auth_required: self._status = 'Codex disconnected; usage is not live.'
        self.changed.emit()

    def close(self):
        self._closing = True
        self.poll.stop()
        self.clock.stop()
        self._generation += 1
