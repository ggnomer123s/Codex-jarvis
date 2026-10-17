"""Load and interact with the production QML window, using a fake CLI."""
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

from PySide6.QtCore import QObject, QMetaObject, QSettings, QUrl, Q_ARG, QPointF, QPoint, Qt, QMimeData, Property
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tigo_gui.backend import Backend
from fake_speech import Engine
import tigo_gui

APP = QApplication.instance() or QApplication([])


class WindowsLayoutBackend(Backend):
    """Render the Windows-only access panel on either CI operating system."""
    @Property(bool, constant=True)
    def windowsDesktop(self): return True


class TestWindow(unittest.TestCase):
    def test_real_window_submit_chat_and_compact_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "codex.py"
            script = Path(__file__).with_name("fake_app_server.py")
            settings = QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat)
            settings.setValue('speech/enabled', False)
            settings.setValue("folder", folder)
            Path(settings.fileName()).with_suffix(".access").write_text("read-only\n")
            full_home = root / "full-profile"
            full_home.mkdir()
            (full_home / "AGENTS.md").write_text("Test full profile")
            (full_home / "backend.txt").write_text("none")
            backend = WindowsLayoutBackend(settings, codex_command=[sys.executable, "-u", str(script), "windows-control-user", str(root / "requests.jsonl")], codex_home_override=full_home, speech_engine_factory=Engine)
            engine = QQmlApplicationEngine()
            warnings = []
            engine.warnings.connect(lambda items: warnings.extend(str(item) for item in items))
            engine.rootContext().setContextProperty("bridge", backend)
            engine.load(QUrl.fromLocalFile(str(Path(tigo_gui.__file__).parent / "ui/Main.qml")))
            try:
                self.assertTrue(engine.rootObjects(), warnings)
                window = engine.rootObjects()[0]
                self.assertEqual(window.property("title"), "Tigo - Personal intelligence")
                self.assertEqual(window.findChild(QObject, "brandMonogram").property("text"), "T")
                self.assertEqual(window.findChild(QObject, "brandTitle").property("text"), "Tigo")
                composer = window.findChild(QObject, "composer")
                button = window.findChild(QObject, "sendButton")
                composer.setProperty("text", "Check the workspace")
                inline_model = window.findChild(QObject, "inlineModel")
                inline_model.setProperty("editText", "test-model")
                self.assertTrue(QMetaObject.invokeMethod(inline_model, "accepted"))
                QTest.qWait(40)
                self.assertEqual(backend.model, "test-model")
                self.assertEqual(composer.property("text"), "Check the workspace")
                inline_effort = window.findChild(QObject, "inlineEffort")
                choice = next(i for i, item in enumerate(backend.reasoningOptions) if item["code"] == "high")
                inline_effort.setProperty("currentIndex", choice)
                self.assertTrue(QMetaObject.invokeMethod(inline_effort, "activated", Q_ARG(int, choice)))
                QTest.qWait(40)
                self.assertEqual(backend.effort, "high")
                APP.processEvents()
                self.assertTrue(button.property("enabled"))
                self.assertTrue(QMetaObject.invokeMethod(button, "clicked"))
                smaller = window.findChild(QObject, "conversationFontSmaller")
                larger = window.findChild(QObject, "conversationFontLarger")
                self.assertTrue(backend.busy)
                self.assertTrue(QMetaObject.invokeMethod(larger, "clicked"))
                self.assertEqual(backend.conversationFontSize, 16)
                self.assertTrue(QMetaObject.invokeMethod(smaller, "clicked"))
                deadline = time.monotonic() + 5
                while backend.busy and time.monotonic() < deadline:
                    QTest.qWait(20)
                self.assertFalse(backend.busy)
                self.assertEqual(backend.messages[-1]["text"], "Check the workspace")
                self.assertEqual(composer.property("text"), "")
                self.assertEqual(backend.conversationFontSize, 14)
                history, pid = list(backend.messages), backend.process.processId()
                composer.setProperty("text", "Keep this draft")
                self.assertTrue(QMetaObject.invokeMethod(smaller, "clicked"))
                self.assertEqual(backend.conversationFontSize, 12)
                self.assertFalse(smaller.property("enabled"))
                for _ in range(8):
                    self.assertTrue(QMetaObject.invokeMethod(larger, "clicked"))
                QTest.qWait(80)
                self.assertEqual(backend.conversationFontSize, 28)
                self.assertFalse(larger.property("enabled"))
                # ListView delegates belong to its visual tree, not the window's QObject tree.
                items = [window.findChild(QObject, "conversation").property("contentItem")]
                bodies = []
                while items:
                    item = items.pop()
                    items.extend(item.childItems())
                    if item.objectName() == "conversationMessageBody":
                        bodies.append(item)
                self.assertGreaterEqual(len(bodies), 2)
                self.assertTrue(all(body.property("font").pixelSize() == 28 for body in bodies))
                self.assertEqual(backend.messages, history)
                self.assertEqual(backend.process.processId(), pid)
                self.assertEqual(composer.property("text"), "Keep this draft")
                settings.sync()
                reopened = Backend(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat), codex_home_override=full_home)
                try:
                    self.assertEqual(reopened.conversationFontSize, 28)
                finally:
                    reopened.shutdown()
                    reopened.deleteLater()
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
                for index in (1, 2, 3, 4, 5, 6):
                    tabs.setProperty("currentIndex", index)
                    QTest.qWait(50)
                auto_speech = window.findChild(QObject, 'autoSpeechToggle')
                auto_speech.setProperty('checked', True)
                self.assertTrue(QMetaObject.invokeMethod(auto_speech, 'clicked'))
                self.assertTrue(backend.speaker.enabled)
                self.assertTrue(QMetaObject.invokeMethod(window.findChild(QObject, 'testSpeechButton'), 'clicked'))
                self.assertTrue(backend.speaker.active)
                self.assertIn('наставник', backend.speaker._engine.spoken[-1])
                backend.speaker.stop()
                QTest.qWait(350)
                backend.speaker.setEnabled(False)
                tabs.setProperty("currentIndex", 2)
                QTest.qWait(50)
                control_check = window.findChild(QObject, 'desktopControlCheckButton')
                self.assertTrue(control_check.property('visible'))
                self.assertTrue(QMetaObject.invokeMethod(control_check, 'clicked'))
                deadline = time.monotonic()+5
                while backend.busy and time.monotonic()<deadline: QTest.qWait(10)
                self.assertFalse(backend.busy)
                self.assertIn('You currently own', backend.desktopControlStatus)
                self.assertIn('7.5 s', window.findChild(QObject, 'desktopControlStatus').property('text'))
                toggle = window.findChild(QObject, "fullAccessToggle")
                self.assertTrue(toggle.property("enabled"))
                self.assertIsNone(window.findChild(QObject, "fullAcknowledgement"))
                self.assertFalse(backend.fullAccess)
                with mock.patch("tigo_gui.backend.elevated", return_value=False):
                    toggle.setProperty("checked", True)
                    self.assertTrue(QMetaObject.invokeMethod(toggle, "clicked"))
                    APP.processEvents()
                self.assertTrue(backend.fullAccess)
                self.assertTrue(toggle.property("checked"))
                toggle.setProperty("checked", False)
                self.assertTrue(QMetaObject.invokeMethod(toggle, "clicked"))
                APP.processEvents()
                self.assertFalse(backend.fullAccess)
                self.assertFalse(toggle.property("checked"))
                self.assertTrue(QMetaObject.invokeMethod(popup, "close"))
                window.setWidth(1060)
                window.setHeight(760)
                QTest.qWait(150)
                image = QQuickWindow.grabWindow(window)
                self.assertFalse(image.isNull())
                self.assertEqual(image.width(), 1060 * window.devicePixelRatio())
                for control in (inline_model, inline_effort, button, smaller, larger):
                    position = control.mapToScene(QPointF(0, 0))
                    self.assertLessEqual(position.x() + control.width(), window.width())
                    self.assertLessEqual(position.y() + control.height(), window.height())
                pane = window.findChild(QObject, "chatPane")
                core = window.findChild(QObject, "corePanel")
                old_width = pane.width()
                handle = pane.mapToScene(QPointF(0, 0))
                drag_start = QPoint(round(handle.x()) - 4, 300)
                QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, drag_start)
                QTest.mouseMove(window, drag_start + QPoint(90, 0), 40)
                QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, drag_start + QPoint(90, 0))
                QTest.qWait(80)
                self.assertLess(pane.width(), old_width)
                self.assertEqual(backend.chatWidth, round(pane.width()))
                full_chat = window.findChild(QObject, "chatOnlyButton")
                self.assertTrue(QMetaObject.invokeMethod(full_chat, "clicked"))
                QTest.qWait(50)
                self.assertTrue(backend.chatOnly)
                self.assertFalse(core.property("visible"))
                self.assertAlmostEqual(pane.width(), window.width(), delta=2)
                self.assertTrue(composer.property("visible"))
                self.assertTrue(QMetaObject.invokeMethod(full_chat, "clicked"))
                self.assertTrue(QMetaObject.invokeMethod(window.findChild(QObject, "coreVisibilityButton"), "clicked"))
                QTest.qWait(50)
                self.assertFalse(core.property("visible"))
                self.assertFalse(backend.showCore)
                self.assertEqual(composer.property("text"), "Keep this draft")
                backend._message("assistant", "# Result\n\n- **Verified**\n\n```python\nprint('ready')\n```\n")
                QTest.qWait(100)
                items = [window.findChild(QObject, "conversation").property("contentItem")]
                copy_code = None
                read_message = None
                while items:
                    item = items.pop()
                    items.extend(item.childItems())
                    if item.objectName() == "copyCodeButton" and item.property("visible"):
                        copy_code = item
                    if item.objectName() == 'readMessageButton' and item.property('visible'):
                        read_message = item
                self.assertIsNotNone(copy_code)
                self.assertTrue(QMetaObject.invokeMethod(copy_code, "clicked"))
                self.assertEqual(APP.clipboard().text(), "print('ready')\n")
                self.assertIsNotNone(read_message)
                before_read_pid = backend.process.processId()
                self.assertTrue(QMetaObject.invokeMethod(read_message, 'clicked'))
                self.assertTrue(backend.speaker.active)
                self.assertEqual(backend.stage, 'speaking')
                self.assertEqual(backend.process.processId(), before_read_pid)
                self.assertTrue(QMetaObject.invokeMethod(window.findChild(QObject, 'stopSpeechButton'), 'clicked'))
                QTest.qWait(350)
                self.assertFalse(backend.speaker.active)
                attached_file = root / "drop fixture.txt"
                attached_file.write_text("Review before sending", encoding="utf-8")
                before_drop_pid = backend.process.processId()
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(str(attached_file))])
                enter = QDragEnterEvent(QPointF(500, 400), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                APP.sendEvent(window, enter)
                drop = QDropEvent(QPointF(500, 400), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                APP.sendEvent(window, drop)
                APP.processEvents()
                self.assertEqual(len(backend.attachments), 1)
                self.assertEqual(backend.attachments[0]['name'], 'drop fixture.txt')
                self.assertEqual(backend.process.processId(), before_drop_pid)
                backend.removeAttachment(0)
                history_popup = window.findChild(QObject, "historyPopup")
                self.assertTrue(QMetaObject.invokeMethod(history_popup, "open"))
                QTest.qWait(200)
                self.assertTrue(history_popup.property("opened"))
                self.assertTrue(QMetaObject.invokeMethod(history_popup, "close"))
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
