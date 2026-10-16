"""Same-user emergency-stop IPC entry point. Never starts a new GUI/task."""
from PySide6.QtCore import QCoreApplication
from .activation import Instance


def main():
    app = QCoreApplication([])
    instance = Instance(app)
    return 0 if instance.contact(activate=False, takeover=True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
