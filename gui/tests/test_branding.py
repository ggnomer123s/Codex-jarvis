"""QSettings upgrade is isolated and preserves voice, model and wake choices."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from PySide6.QtCore import QSettings
from tigo_gui.compat import desktop_settings


class TestSettingsUpgrade(unittest.TestCase):
    def test_copy_missing_preferences_once_without_overwriting_tigo_choices(self):
        with tempfile.TemporaryDirectory() as folder:
            old = QSettings(str(Path(folder) / 'old.ini'), QSettings.IniFormat)
            new = QSettings(str(Path(folder) / 'new.ini'), QSettings.IniFormat)
            for key, value in {'model': 'chosen-model', 'speech/enabled': False,
                               'wake/enabled': True, 'wake/model': 'small'}.items():
                old.setValue(key, value)
            new.setValue('model', 'new-choice')
            with mock.patch('PySide6.QtCore.QSettings', side_effect=lambda brand, app: new if brand == 'Tigo' else old):
                migrated = desktop_settings()
                self.assertEqual(migrated.value('model'), 'new-choice')
                self.assertFalse(migrated.value('speech/enabled'))
                self.assertTrue(migrated.value('wake/enabled'))
                self.assertEqual(migrated.value('wake/model'), 'small')
                old.setValue('wake/model', 'tiny')
                self.assertEqual(desktop_settings().value('wake/model'), 'small')
