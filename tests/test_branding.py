"""Upgrade fixtures: retain data, access choices and personal instructions."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'gui'))
from tigo_gui.access import access_file
from tigo_gui.compat import environment
from tigo_gui.speech_models import cache_root


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class TestBrandUpgrade(unittest.TestCase):
    def test_saved_access_and_history_stay_in_the_existing_private_store(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch('pathlib.Path.home', return_value=Path(folder)):
            base = Path(folder) / ('AppData/Local' if os.name == 'nt' else '.local/share')
            with mock.patch.dict(os.environ, {'LOCALAPPDATA': str(base)}):
                old = base / 'jarvis-codex'
                old.mkdir(parents=True)
                (old / 'access-mode').write_text('read-only\n')
                (old / 'conversations.sqlite3').write_bytes(b'private-history-fixture')
                (base / 'tigo-codex').mkdir()  # Installer assets must not hide old state.
                self.assertEqual(access_file(), old / 'access-mode')
                self.assertEqual((old / 'conversations.sqlite3').read_bytes(), b'private-history-fixture')
                (base / 'tigo-codex/access-mode').write_text('workspace-write\n')
                self.assertEqual(access_file(), base / 'tigo-codex/access-mode')

    def test_new_environment_wins_and_old_environment_still_works(self):
        with mock.patch.dict(os.environ, {'JARVIS_GUI_CODEX': '/old/codex'}, clear=True):
            self.assertEqual(environment('GUI_CODEX'), '/old/codex')
            os.environ['TIGO_GUI_CODEX'] = '/new/codex'
            self.assertEqual(environment('GUI_CODEX'), '/new/codex')

    def test_verified_voice_cache_is_reused_without_download(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {'XDG_CACHE_HOME': folder, 'LOCALAPPDATA': folder}):
            old = Path(folder) / 'jarvis/voices'
            old.mkdir(parents=True)
            self.assertEqual(cache_root(), old)
            current = Path(folder) / 'tigo/voices'
            current.mkdir(parents=True)
            self.assertEqual(cache_root(), current)

    def test_old_rules_and_memory_markers_are_replaced_once_with_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            agents = Path(folder) / 'AGENTS.md'
            original = ('Personal instructions\n<!-- JARVIS-CODEX RULES START -->\nold rules\n<!-- JARVIS-CODEX RULES END -->\n'
                        '<!-- JARVIS-CODEX MEMORY START -->\nold memory guidance\n<!-- JARVIS-CODEX MEMORY END -->\nKeep this too\n')
            agents.write_text(original)
            sync = module('sync_agents').sync
            template = ROOT / 'config/tigo-agents.md'
            self.assertTrue(sync(agents, template))
            self.assertFalse(sync(agents, template))
            text = agents.read_text()
            self.assertNotIn('JARVIS-CODEX', text)
            self.assertEqual(text.count('<!-- TIGO-CODEX RULES START -->'), 1)
            self.assertEqual(text.count('<!-- TIGO-CODEX MEMORY START -->'), 1)
            self.assertIn('Personal instructions', text)
            self.assertIn('Keep this too', text)
            self.assertEqual(next(Path(folder).glob('AGENTS.md.backup.*')).read_text(), original)

    @unittest.skipIf(os.name == 'nt', 'Linux entry point fixture')
    def test_owned_old_menu_is_retired_and_launchers_forward_with_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            bin_dir = home / '.local/bin'
            bin_dir.mkdir(parents=True)
            (bin_dir / 'jarvis').write_text('# JARVIS-CODEX MANAGED\nold launcher\n')
            (bin_dir / 'tigo').write_text('new launcher')
            menu = home / '.local/share/applications'
            menu.mkdir(parents=True)
            (menu / 'jarvis-gui.desktop').write_text('# JARVIS-CODEX MANAGED\nName=JARVIS\n')
            (menu / 'tigo-gui.desktop').write_text('Name=Tigo\n')
            migrate = module('migrate_brand').migrate
            migrate(home)
            self.assertIn('/tigo', (bin_dir / 'jarvis').read_text())
            self.assertIn('old launcher', (bin_dir / 'jarvis.pre-tigo').read_text())
            self.assertFalse((menu / 'jarvis-gui.desktop').exists())
            (bin_dir / 'jarvis').write_text('personal command')
            migrate(home)
            self.assertEqual((bin_dir / 'jarvis').read_text(), 'personal command')
