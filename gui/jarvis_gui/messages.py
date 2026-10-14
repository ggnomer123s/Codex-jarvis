"""Incremental chat updates: streaming never resets every QML chat delegate."""
from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt


class Messages(QAbstractListModel):
    ROLE = Qt.ItemDataRole.UserRole + 1
    TEXT = ROLE + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []

    def roleNames(self):
        return {self.ROLE: QByteArray(b"messageRole"), self.TEXT: QByteArray(b"messageText")}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.items):
            return None
        return self.items[index.row()].get("role" if role == self.ROLE else "text")

    def append(self, role, text):
        row = len(self.items)
        self.beginInsertRows(QModelIndex(), row, row)
        self.items.append({"role": role, "text": text})
        self.endInsertRows()
        return row

    def update(self, row, text):
        if 0 <= row < len(self.items):
            self.items[row]["text"] = text
            index = self.index(row)
            self.dataChanged.emit(index, index, [self.TEXT])

    def clear(self):
        self.beginResetModel()
        self.items.clear()
        self.endResetModel()
