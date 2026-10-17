"""Run the Tigo desktop window on Linux or Windows 11."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

from PySide6.QtCore import QObject, QMetaObject, QSettings, QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .backend import Backend
from .activation import Instance
from .screen_overlay import ScreenOverlay


def main() -> int:
    parser = argparse.ArgumentParser(description="Tigo desktop console")
    parser.add_argument("--smoke-test", action="store_true", help="Load the actual UI, then exit without sending a request")
    parser.add_argument("--background", action="store_true", help="Start hidden if voice activation is enabled")
    parser.add_argument("--screenshot", type=Path, help="Save a window image before the smoke-test exits")
    tabs = ["intelligence", "voice", "access", "runtime", "automation", "wake", "speech"]
    parser.add_argument("--settings-tab", choices=tabs, help="Show a preferences tab during the smoke test")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Tigo")
    app.setOrganizationName("Tigo")
    app.setDesktopFileName("tigo-gui")
    instance = None
    if not args.smoke_test:
        instance = Instance(app)
        try:
            if not instance.claim(activate=not args.background):
                return 0
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        app.aboutToQuit.connect(instance.close)
    root = Path(__file__).parent
    app.setWindowIcon(QIcon(str(root / "ui" / "icon.svg")))
    smoke_directory = tempfile.TemporaryDirectory(prefix="tigo-gui-smoke-") if args.smoke_test else None
    settings = QSettings(str(Path(smoke_directory.name) / "settings.ini"), QSettings.Format.IniFormat) if smoke_directory else None
    tray_available = not args.smoke_test and QSystemTrayIcon.isSystemTrayAvailable()
    backend = Backend(settings, start_hidden=args.background and not args.smoke_test, tray_available=tray_available)
    if not args.smoke_test:
        # Refresh the owned login entry to the current package/interpreter.
        try:
            backend.wake.register(backend.wake.enabled and backend.wake.autostart)
        except (OSError, ValueError, ImportError) as exc:
            backend._show_notice('Voice startup registration needs attention: ' + str(exc))
    if args.background and not args.smoke_test and not backend.wake.enabled:
        backend.shutdown()
        instance.close()
        return 0
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", backend)
    engine.load(QUrl.fromLocalFile(str(root / "ui" / "Main.qml")))
    if not engine.rootObjects():
        return 1
    app.aboutToQuit.connect(backend.shutdown)
    window = engine.rootObjects()[0]

    def show_window():
        window.showNormal()
        window.raise_()
        window.requestActivate()

    if not args.smoke_test:
        instance.activated.connect(show_window)
        backend.updater.quitRequested.connect(app.quit)
        instance.controlRequested.connect(backend.takeControl)
        overlay = ScreenOverlay(backend, app)
        app.aboutToQuit.connect(overlay.close)
        backend.wake.activated.connect(show_window)
        tray = QSystemTrayIcon(app.windowIcon(), app)
        menu = QMenu()
        menu.addAction("Open Tigo", show_window)
        menu.addAction("Disable voice activation", backend.wake.disable)
        menu.addSeparator()
        menu.addAction("Quit Tigo", app.quit)
        tray.setContextMenu(menu)
        tray.activated.connect(lambda reason: show_window() if reason == QSystemTrayIcon.Trigger else None)

        def sync_wake():
            app.setQuitOnLastWindowClosed(not backend.wake.enabled)
            tray.setToolTip("Tigo: " + backend.wake.status[:180])
            tray.setVisible(tray_available and backend.wake.enabled)
            if (not backend.wake.enabled and not window.isVisible()) or backend.wake.state == "error":
                show_window()

        backend.wake.changed.connect(sync_wake)
        sync_wake()
        if args.background and not tray_available:
            window.showMinimized()
        QTimer.singleShot(0, backend.wake.start)
    if args.smoke_test:
        if args.settings_tab:
            window = engine.rootObjects()[0]
            QMetaObject.invokeMethod(window.findChild(QObject, "preferences"), "open")
            window.findChild(QObject, "preferenceTabs").setProperty("currentIndex", tabs.index(args.settings_tab))
        def finish():
            window = engine.rootObjects()[0]
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                if not QQuickWindow.grabWindow(window).save(str(args.screenshot)):
                    app.exit(2)
                    return
            print("Tigo UI loaded successfully.")
            app.quit()
        QTimer.singleShot(1200, finish)
    return app.exec()
