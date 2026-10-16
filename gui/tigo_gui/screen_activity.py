"""Display desktop-tool activity, never infer OS ownership from model prose."""
from PySide6.QtCore import QObject, Property, QTimer, Signal

from .workflows import SERVERS


def desktop_call(item):
    if not isinstance(item, dict) or item.get('type') != 'mcpToolCall':
        return False
    server = str(item.get('server', '')).casefold()
    tool = str(item.get('tool', '')).casefold()
    if tool in ('controlstatus', 'controlstatus-tool'):
        return False
    return server in SERVERS or any(tool.startswith('mcp__' + name + '__') for name in SERVERS)


class ScreenActivity(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._calls = set()
        self._active = False
        self._tail = QTimer(self)
        self._tail.setSingleShot(True)
        self._tail.setInterval(1200)
        self._tail.timeout.connect(self.clear)

    @Property(bool, notify=changed)
    def active(self):
        return self._active

    def handle_item(self, method, item):
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id']:
            return
        key = item['id']
        if method == 'item/started' and desktop_call(item):
            self._tail.stop()
            self._calls.add(key)
            if not self._active:
                self._active = True
                self.changed.emit()
        elif method == 'item/completed' and key in self._calls:
            self._calls.discard(key)
            if not self._calls:
                self._tail.start()

    def clear(self):
        self._tail.stop()
        self._calls.clear()
        if self._active:
            self._active = False
            self.changed.emit()
