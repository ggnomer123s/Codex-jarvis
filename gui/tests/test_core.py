"""Exercise the production core's timing, retained artwork and pause behavior."""
from pathlib import Path
import unittest

from PySide6.QtCore import QObject, QMetaObject, Q_ARG
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import tigo_gui


APP = QApplication.instance() or QApplication([])


class TestCore(unittest.TestCase):
    def setUp(self):
        self.engine = QQmlApplicationEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda items: self.warnings.extend(str(x) for x in items))
        ui = (Path(tigo_gui.__file__).parent / 'ui').as_uri()
        self.engine.loadData(('''import QtQuick
import "%s" as Tigo
Window {
    visible: true; width: 440; height: 440; color: "#0b131b"
    Tigo.Orb { anchors.centerIn: parent; width: 360; height: 360; animate: false }
}''' % ui).encode())
        self.assertTrue(self.engine.rootObjects(), self.warnings)
        self.window = self.engine.rootObjects()[0]
        self.core = self.window.findChild(QObject, 'activityCore')
        QTest.qWait(120)

    def tearDown(self):
        self.assertEqual(self.warnings, [])
        self.window.close()
        self.engine.deleteLater()
        APP.processEvents()

    def advance(self, seconds):
        self.assertTrue(QMetaObject.invokeMethod(self.core, 'advance', Q_ARG('QVariant', seconds)))

    def test_continuous_rotation_and_frame_rate_independent_audio(self):
        self.core.setProperty('stage', 'acting')
        self.core.setProperty('phase', 359.9)
        self.advance(0.02)
        self.assertAlmostEqual(self.core.property('phase'), 361.26, places=5)
        # Long event-loop stalls must not teleport the artwork on resume.
        self.advance(10.0)
        self.assertAlmostEqual(self.core.property('phase'), 364.66, places=5)
        self.core.setProperty('listening', True)
        self.core.setProperty('targetLevel', 0.9)
        for _ in range(6):
            self.advance(1 / 60)
        sixty_hz = self.core.property('level')
        self.core.setProperty('level', 0.0)
        for _ in range(12):
            self.advance(1 / 120)
        self.assertAlmostEqual(self.core.property('level'), sixty_hz, places=6)
        self.assertGreater(sixty_hz, 0.7)

    def test_animation_reuses_artwork_and_dial_but_updates_overlay(self):
        texture = self.window.findChild(QObject, 'coreTexture')
        dial = self.window.findChild(QObject, 'coreDial')
        overlay = self.window.findChild(QObject, 'activityArtwork')
        counts = {'texture': 0, 'dial': 0, 'overlay': 0}
        texture.painted.connect(lambda: counts.__setitem__('texture', counts['texture'] + 1))
        dial.painted.connect(lambda: counts.__setitem__('dial', counts['dial'] + 1))
        overlay.painted.connect(lambda: counts.__setitem__('overlay', counts['overlay'] + 1))
        self.core.setProperty('animate', True)
        QTest.qWait(240)
        self.assertTrue(self.core.property('animationRunning'))
        self.assertGreater(self.core.property('elapsed'), 0)
        self.assertGreater(counts['overlay'], 2)
        self.assertEqual(counts['texture'], 0)
        self.assertEqual(counts['dial'], 0)
        # All state-specific effects still load and render without QML warnings.
        for stage in ('planning', 'acting', 'recording', 'speaking', 'verifying',
                      'complete', 'failed', 'connecting', 'transcribing', 'stopping'):
            self.core.setProperty('stage', stage)
            QTest.qWait(25)
        frame = QQuickWindow.grabWindow(self.window)
        self.assertFalse(frame.isNull())

    def test_hidden_and_stopped_core_pause_without_resetting_orientation(self):
        self.core.setProperty('animate', True)
        QTest.qWait(80)
        self.core.setProperty('visible', False)
        phase = self.core.property('phase')
        QTest.qWait(80)
        self.assertFalse(self.core.property('animationRunning'))
        self.assertEqual(self.core.property('phase'), phase)
        self.core.setProperty('visible', True)
        QTest.qWait(80)
        self.assertGreater(self.core.property('phase'), phase)
        self.core.setProperty('stage', 'stopped')
        phase = self.core.property('phase')
        QTest.qWait(80)
        self.assertFalse(self.core.property('animationRunning'))
        self.assertEqual(self.core.property('phase'), phase)
