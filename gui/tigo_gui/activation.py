"""Single GUI instance and same-user activation through local Qt IPC."""
import hashlib
from pathlib import Path
import time

from PySide6.QtCore import QObject, QLockFile, QStandardPaths, QTimer, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class Instance(QObject):
    activated = Signal()
    controlRequested = Signal()

    def __init__(self, parent=None, *, namespace=None):
        super().__init__(parent)
        # Stable upgrade identity prevents two versions capturing the microphone.
        identity = namespace or str(Path.home()) + '|jarvis-desktop'
        self.name = 'jarvis-' + hashlib.sha256(identity.encode()).hexdigest()[:24]
        self.lock = QLockFile(str(Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation)) / (self.name + '.lock')))
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        self.server.newConnection.connect(self._incoming)

    def contact(self, activate=True, *, takeover=False):
        socket = QLocalSocket()
        socket.connectToServer(self.name)
        if not socket.waitForConnected(400):
            return False
        socket.write(b'take-control\n' if takeover else (b'activate\n' if activate else b'ping\n'))
        socket.waitForBytesWritten(400)
        # Windows named-pipe data can be lost when the writer disconnects before
        # the owner reads it. Do not treat connection alone as delivery.
        reply = bytearray()
        deadline = time.monotonic() + 1.5
        while b'\n' not in reply and len(reply) <= 64:
            remaining = int((deadline - time.monotonic()) * 1000)
            if remaining <= 0:
                break
            if not socket.bytesAvailable() and not socket.waitForReadyRead(remaining):
                break
            reply.extend(bytes(socket.readAll()))
        socket.disconnectFromServer()
        return bytes(reply) == b'ok\n'

    def claim(self, activate=True):
        if self.contact(activate):
            return False
        if not self.lock.tryLock(0):
            if self.contact(activate):
                return False
            raise RuntimeError('Tigo is already starting. Retry in a moment.')
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            self.lock.unlock()
            raise RuntimeError('Could not create the local Tigo activation socket.')
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
                    message = bytes(buffer)
                    buffer.clear()
                    if message == b'activate\n':
                        self.activated.emit()
                    elif message == b'take-control\n':
                        self.controlRequested.emit()
                    if message in (b'activate\n', b'ping\n', b'take-control\n'):
                        socket.write(b'ok\n')
                        socket.flush()
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
