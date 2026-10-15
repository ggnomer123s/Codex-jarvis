"""Single GUI instance and same-user activation through local Qt IPC."""
import hashlib
from pathlib import Path

from PySide6.QtCore import QObject, QLockFile, QStandardPaths, QTimer, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class Instance(QObject):
    activated = Signal()

    def __init__(self, parent=None, *, namespace=None):
        super().__init__(parent)
        identity = namespace or str(Path.home()) + '|jarvis-desktop'
        self.name = 'jarvis-' + hashlib.sha256(identity.encode()).hexdigest()[:24]
        self.lock = QLockFile(str(Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation)) / (self.name + '.lock')))
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        self.server.newConnection.connect(self._incoming)

    def contact(self, activate=True):
        socket = QLocalSocket()
        socket.connectToServer(self.name)
        if not socket.waitForConnected(400):
            return False
        socket.write(b'activate\n' if activate else b'ping\n')
        socket.waitForBytesWritten(400)
        socket.disconnectFromServer()
        return True

    def claim(self, activate=True):
        if self.contact(activate):
            return False
        if not self.lock.tryLock(0):
            if self.contact(activate):
                return False
            raise RuntimeError('JARVIS is already starting. Retry in a moment.')
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            self.lock.unlock()
            raise RuntimeError('Could not create the local JARVIS activation socket.')
        return True

    def _incoming(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            buffer = bytearray()

            def read(socket=socket, buffer=buffer):
                buffer.extend(bytes(socket.readAll()))
                if len(buffer) > 64:
                    socket.abort()
                elif b'\n' in buffer:
                    if bytes(buffer) == b'activate\n':
                        self.activated.emit()
                    socket.disconnectFromServer()

            socket.readyRead.connect(read)
            socket.disconnected.connect(socket.deleteLater)
            timer = QTimer(socket)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda socket=socket: socket.abort())
            timer.start(1500)
            read()

    def close(self):
        self.server.close()
        self.lock.unlock()
