"""Load and interact with the production QML window, using a fake CLI."""
from pathlib import Path
import sys
import tempfile
import time
import unittest

from PySide6.QtCore import QObject, QMetaObject, QSettings, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from jarvis_gui.backend import Backend
import jarvis_gui

APP = QApplication.instance() or QApplication([])


class TestWindow(unittest.TestCase):
    def test_real_window_submit_chat_and_compact_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "codex.py"
            script.write_text("import json,sys; text=sys.stdin.read(); print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Received: '+text}}))")
            settings = QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat)
            settings.setValue("folder", folder)
            backend = Backend(settings, codex_command=[sys.executable, str(script)])
            engine = QQmlApplicationEngine()
            warnings = []
            engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
            engine.rootContext().setContextProperty("bridge", backend)
            engine.load(QUrl.fromLocalFile(str(Path(jarvis_gui.__file__).parent / "ui/Main.qml")))
            try:
                self.assertTrue(engine.rootObjects(), warnings)
                window = engine.rootObjects()[0]
                composer = window.findChild(QObject, "composer")
                button = window.findChild(QObject, "sendButton")
                composer.setProperty("text", "Check the workspace")
                APP.processEvents()
                self.assertTrue(button.property("enabled"))
                self.assertTrue(QMetaObject.invokeMethod(button, "clicked"))
                deadline = time.monotonic() + 5
                while backend.busy and time.monotonic() < deadline:
                    QTest.qWait(20)
                self.assertFalse(backend.busy)
                self.assertEqual(backend.messages[-1]["text"], "Received: Check the workspace")
                self.assertEqual(composer.property("text"), "")
                popup = window.findChild(QObject, "preferences")
                self.assertTrue(QMetaObject.invokeMethod(popup, "open"))
                QTest.qWait(100)
                model = window.findChild(QObject, "modelChoice")
                model.setProperty("editText", "test-model")
                language = window.findChild(QObject, "languageChoice")
                language.setProperty("currentIndex", 1)
                QTest.qWait(50)
                self.assertEqual(language.property("currentValue"), "ru")
                self.assertEqual(model.property("editText"), "test-model")
                tabs = window.findChild(QObject, "preferenceTabs")
                for index in (1, 2, 0):
                    tabs.setProperty("currentIndex", index)
                    QTest.qWait(50)
                tabs.setProperty("currentIndex", 2)
                access = window.findChild(QObject, "accessChoice")
                access.setProperty("currentIndex", 2)
                QTest.qWait(50)
                full_button = window.findChild(QObject, "fullAccessButton")
                self.assertFalse(full_button.property("enabled"))
                window.findChild(QObject, "fullRiskAccepted").setProperty("checked", True)
                window.findChild(QObject, "fullAcknowledgement").setProperty("text", "ENABLE FULL ACCESS")
                APP.processEvents()
                self.assertTrue(full_button.property("enabled"))
                # Verify the form without running an installer on the test host.
                self.assertFalse(backend.fullAccess)
                self.assertTrue(QMetaObject.invokeMethod(popup, "close"))
                window.setWidth(1060)
                window.setHeight(760)
                QTest.qWait(150)
                image = QQuickWindow.grabWindow(window)
                self.assertFalse(image.isNull())
                self.assertEqual(image.width(), 1060 * window.devicePixelRatio())
                self.assertEqual(warnings, [])
            finally:
                backend.shutdown()
                for window in engine.rootObjects():
                    window.close()
                engine.deleteLater()
                backend.deleteLater()
                APP.processEvents()


if __name__ == "__main__":
    unittest.main()
