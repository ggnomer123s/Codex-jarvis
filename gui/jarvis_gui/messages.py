"""Incremental chat updates: streaming never resets every QML chat delegate."""
from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt
from .presentation import message_blocks


class Messages(QAbstractListModel):
    ROLE = Qt.ItemDataRole.UserRole + 1
    TEXT = ROLE + 1
    BLOCKS = TEXT + 1
    ATTACHMENTS = BLOCKS + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._blocks = {}

    def roleNames(self):
        return {self.ROLE: QByteArray(b"messageRole"), self.TEXT: QByteArray(b"messageText"),
                self.BLOCKS: QByteArray(b"messageBlocks"), self.ATTACHMENTS: QByteArray(b"messageAttachments")}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.items):
            return None
        item = self.items[index.row()]
        if role == self.BLOCKS:
            if index.row() not in self._blocks:
                self._blocks[index.row()] = message_blocks(item['text'], item['role'] == 'assistant')
            return self._blocks[index.row()]
        if role == self.ATTACHMENTS:
            return item.get('attachments', [])
        return item.get("role" if role == self.ROLE else "text")

    def append(self, role, text, attachments=None):
        row = len(self.items)
        self.beginInsertRows(QModelIndex(), row, row)
        self.items.append({"role": role, "text": text})
        if attachments:
            self.items[-1]['attachments'] = attachments
        self.endInsertRows()
        return row

    def update(self, row, text):
        if 0 <= row < len(self.items):
            self.items[row]["text"] = text
            self._blocks.pop(row, None)
            index = self.index(row)
            self.dataChanged.emit(index, index, [self.TEXT, self.BLOCKS])

    def clear(self):
        self.beginResetModel()
        self.items.clear()
        self._blocks.clear()
        self.endResetModel()
