"""Visible, nonexclusive desktop activity indicator with a human stop button."""
import json
import math
import os
from pathlib import Path
import sys

from PySide6.QtCore import QObject, QProcess, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import QBoxLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .control_hotkey import ControlHotkey, SHORTCUT


def labels(ru, shortcut, *, platform=None):
    windows = (platform or sys.platform) == 'win32'
    if ru:
        return ('\u0422\u0438\u0433\u043e \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442 \u0441 \u044d\u043a\u0440\u0430\u043d\u043e\u043c',
                ('Ctrl+Alt+Shift+Backspace \u2014 \u0432\u0435\u0440\u043d\u0443\u0442\u044c \u0432\u0432\u043e\u0434 Windows-MCP\n' if windows else '') +
                (SHORTCUT + ' \u2014 \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443' if shortcut else '\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443, \u0447\u0442\u043e\u0431\u044b \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443'),
                '\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435')
    return ('Tigo uses the screen',
            ('Ctrl+Alt+Shift+Backspace to return Windows-MCP input\n' if windows else '') +
            (SHORTCUT + ' to stop the current task' if shortcut else
             'Use Return control to stop the current task'), 'Return control')


class ControlBanner(QFrame):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor('#54cbd2'))
        painter.setBrush(QColor('#10212f'))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 16, 16)


def overlay_bounds(geometry, available, windows=False, dpr=1.0):
    """Qt logical coordinates; leave the native MCP's 56-physical-pixel glow.

    Windows-MCP also has a top-center ownership notice. Our own banner uses
    the bottom of the work area instead of competing for topmost order there.
    """
    frame = QRect(geometry)
    if windows:
        ratio = dpr if math.isfinite(dpr) and dpr > 0 else 1.0
        inset = min(math.ceil(56 / ratio) + 8, max(0, (min(frame.width(), frame.height()) - 32) // 2))
        frame.adjust(inset, inset, -inset, -inset)
    room = frame.intersected(available) if windows else QRect(geometry)
    if room.isEmpty():
        room = QRect(frame)
    margin = min(16, max(0, (min(room.width(), room.height()) - 1) // 4))
    return frame, room.adjusted(margin, margin, -margin, -margin)


class NativeOverlay:
    """Windows/X11: narrow nonactivating tool windows, no fullscreen input grab."""
    def __init__(self, callback, *, platform=None):
        self.callback = callback
        self.platform = platform or sys.platform
        self.windows = []

    def hide(self):
        for window in self.windows:
            window.close()
            window.deleteLater()
        self.windows.clear()

    def show(self, ru, shortcut):
        self.hide()
        title, hint, action = labels(ru, shortcut, platform=self.platform)
        windows = self.platform == 'win32'
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus
        for screen in QGuiApplication.screens():
            g, room = overlay_bounds(screen.geometry(), screen.availableGeometry(), windows, screen.devicePixelRatio())
            for x, y, w, h in ((g.x(), g.y(), g.width(), 4), (g.x(), g.bottom()-3, g.width(), 4),
                               (g.x(), g.y(), 4, g.height()), (g.right()-3, g.y(), 4, g.height())):
                edge = QFrame(None, flags | Qt.WindowTransparentForInput)
                edge.setObjectName('screenControlEdge')
                edge.setAttribute(Qt.WA_ShowWithoutActivating)
                edge.setStyleSheet('background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #30d4cf,stop:0.5 #78b8ff,stop:1 #ad8dff);')
                edge.setGeometry(x, y, w, h)
                edge.show()
                self.windows.append(edge)
            banner = ControlBanner(None, flags)
            banner.setObjectName('screenControlBanner')
            banner.setAttribute(Qt.WA_ShowWithoutActivating)
            banner.setAttribute(Qt.WA_TranslucentBackground)
            banner.setStyleSheet('''QFrame#screenControlBanner { background:#10212f; border:1px solid #54cbd2; border-radius:16px; }
QLabel { background:transparent; color:#c4d9e6; font-size:12px; border:0; }
QLabel#screenControlTitle { color:#89f2e9; font-size:15px; font-weight:600; }
QPushButton { background:#19505d; color:#e7ffff; border:1px solid #53cbd1; border-radius:10px; padding:10px 15px; }''')
            row = QHBoxLayout(banner)
            row.setContentsMargins(20, 14, 20, 14)
            row.setSpacing(24)
            if windows and room.width() < 640:
                row.setDirection(QBoxLayout.TopToBottom)
                row.setSpacing(12)
            text = QVBoxLayout()
            heading = QLabel(title)
            heading.setObjectName('screenControlTitle')
            heading.setWordWrap(windows)
            text.addWidget(heading)
            hint_label = QLabel(hint)
            hint_label.setObjectName('screenControlHint')
            hint_label.setWordWrap(windows)
            text.addWidget(hint_label)
            row.addLayout(text, 1)
            button = QPushButton(action)
            button.setObjectName('returnControlButton')
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(self.callback)
            row.addWidget(button)
            if windows:
                banner.setFixedWidth(min(720, room.width()))
            banner.adjustSize()
            x = room.x() + (room.width() - banner.width()) // 2
            y = max(room.top(), room.bottom() - banner.height() + 1) if windows else g.y() + 16
            banner.move(x, y)
            banner.show()
            self.windows.append(banner)


class ScreenOverlay(QObject):
    def __init__(self, backend, parent=None, *, hotkey=None):
        super().__init__(parent)
        self.backend = backend
        self.hotkey = hotkey or ControlHotkey(self)
        self.hotkey.start()
        self.hotkey.activated.connect(backend.takeControl)
        self.native = NativeOverlay(backend.takeControl)
        self.process = QProcess(self)
        self.process.started.connect(self._write)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.finished.connect(self._exited)
        self.process.errorOccurred.connect(self._error)
        self._buffer = bytearray()
        self._closing = False
        self._failed = False
        self._state = False
        self._wayland = sys.platform != 'win32' and bool(os.environ.get('WAYLAND_DISPLAY'))
        backend.screen_activity.changed.connect(self.sync)
        QGuiApplication.instance().screenAdded.connect(self._watch_screen)
        QGuiApplication.instance().screenRemoved.connect(self._screens_changed)
        for screen in QGuiApplication.screens():
            self._watch_screen(screen)

    def _watch_screen(self, screen):
        screen.geometryChanged.connect(self._screens_changed)
        screen.availableGeometryChanged.connect(self._screens_changed)
        screen.logicalDotsPerInchChanged.connect(self._screens_changed)
        self._screens_changed()

    def _screens_changed(self, *_):
        if not self._closing and self._state and not self._wayland:
            self.native.show(self.backend.language != 'en', self.hotkey.available)

    def sync(self):
        self._state = self.backend.screen_activity.active
        if self._closing:
            return
        if self._state:
            self.hotkey.verify()
        if not self._wayland:
            if self._state:
                self.native.show(self.backend.language != 'en', self.hotkey.available)
            else:
                self.native.hide()
        elif not self._failed:
            if self.process.state() == QProcess.NotRunning:
                if not self._state:
                    return
                # GI/GTK belong to the distribution interpreter, not uv's venv.
                self.process.start('/usr/bin/python3', [str(Path(__file__).with_name('layer_overlay.py'))])
            else:
                self._write()

    def _write(self):
        if self.process.state() == QProcess.Running:
            data = {'active': self._state, 'ru': self.backend.language != 'en', 'shortcut': self.hotkey.available}
            self.process.write((json.dumps(data) + '\n').encode())

    def _read(self):
        self._buffer.extend(bytes(self.process.readAllStandardOutput()))
        if len(self._buffer) > 8192:
            self.process.kill()
            return
        while b'\n' in self._buffer:
            line, _, rest = self._buffer.partition(b'\n')
            self._buffer[:] = rest
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and event.get('takeover') is True:
                self.backend.takeControl()

    def _exited(self, *_):
        if not self._closing:
            self._failed = True
            self.backend._show_notice('Screen indicator unavailable. On Wayland install GTK4, PyGObject and gtk4-layer-shell with the system Python; see the screen-control guide. Input remains available.')

    def _error(self, error):
        if error == QProcess.FailedToStart:
            self._exited()

    def close(self):
        self._closing = True
        self.native.hide()
        self.hotkey.close()
        self.process.closeWriteChannel()
        if self.process.state() != QProcess.NotRunning and not self.process.waitForFinished(500):
            self.process.kill()
            self.process.waitForFinished(500)
