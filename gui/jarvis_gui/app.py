"""Run the JARVIS desktop window on Linux or Windows 11."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

from PySide6.QtCore import QSettings, QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication

from .backend import Backend


def main() -> int:
    parser = argparse.ArgumentParser(description="JARVIS desktop console")
    parser.add_argument("--smoke-test", action="store_true", help="Load the actual UI, then exit without sending a request")
    parser.add_argument("--screenshot", type=Path, help="Save a window image before the smoke-test exits")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("JARVIS")
    app.setOrganizationName("Jarvis")
    root = Path(__file__).parent
    app.setWindowIcon(QIcon(str(root / "ui" / "icon.svg")))
    smoke_directory = tempfile.TemporaryDirectory(prefix="jarvis-gui-smoke-") if args.smoke_test else None
    settings = QSettings(str(Path(smoke_directory.name) / "settings.ini"), QSettings.Format.IniFormat) if smoke_directory else None
    backend = Backend(settings)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", backend)
    engine.load(QUrl.fromLocalFile(str(root / "ui" / "Main.qml")))
    if not engine.rootObjects():
        return 1
    app.aboutToQuit.connect(backend.shutdown)
    if args.smoke_test:
        def finish():
            window = engine.rootObjects()[0]
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                if not QQuickWindow.grabWindow(window).save(str(args.screenshot)):
                    app.exit(2)
                    return
            print("JARVIS UI loaded successfully.")
            app.quit()
        QTimer.singleShot(1200, finish)
    return app.exec()
