"""Real local Git histories: checks never checkout/reset/stash user work."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from tigo_gui import update_worker as worker


class TestUpdateInspection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tigo updates ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote, self.source, self.repo = (self.root / name for name in ('remote.git', 'source', 'checkout'))
        self.run_git(self.root, 'init', '--bare', str(self.remote))
        self.run_git(self.root, 'init', '-b', 'main', str(self.source))
        for directory in ('gui', 'scripts'):
            (self.source / directory).mkdir()
        (self.source / 'gui/pyproject.toml').write_text('[project]\nversion="1.0.0"\n')
        (self.source / 'changes.md').write_text('# Changes\n\n## 2026-10-17\n\nInitial.\n')
        for name in ('update-linux.sh', 'update-cachyos.sh', 'update-windows.ps1'):
            (self.source / 'scripts' / name).write_text('# synthetic installer fixture\n')
        self.commit(self.source, 'initial')
        self.run_git(self.source, 'remote', 'add', 'origin', str(self.remote))
        self.run_git(self.source, 'push', 'origin', 'main')
        self.run_git(self.root, 'clone', '--branch', 'main', str(self.remote), str(self.repo))
        self.old = self.run_git(self.repo, 'rev-parse', 'HEAD')
        self.new = self.advance()
        patch = mock.patch.object(worker, 'ORIGINS', {self.run_git(self.repo, 'remote', 'get-url', 'origin')})
        patch.start()
        self.addCleanup(patch.stop)

    def run_git(self, path, *args):
        result = subprocess.run(['git', '-C', str(path), *args], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, path, message):
        self.run_git(path, 'add', '-A')
        self.run_git(path, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', message)

    def advance(self, version='1.1.0'):
        (self.source / 'gui/pyproject.toml').write_text('[project]\nversion="' + version + '"\n')
        self.commit(self.source, version)
        self.run_git(self.source, 'push', 'origin', 'main')
        return self.run_git(self.source, 'rev-parse', 'HEAD')

    def test_check_fetches_notes_without_changing_working_files(self):
        before = (self.repo / 'gui/pyproject.toml').read_bytes()
        data = worker.inspect(self.repo)
        self.assertEqual(data['state'], 'available')
        self.assertEqual(data['version'], '1.1.0')
        self.assertEqual(data['commits'], 1)
        self.assertEqual(data['revision'], self.new)
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), self.old)
        self.assertEqual((self.repo / 'gui/pyproject.toml').read_bytes(), before)

    def test_dirty_checkout_is_rejected_and_user_file_is_retained(self):
        file = self.repo / 'my-work.txt'
        file.write_text('unfinished work')
        with self.assertRaisesRegex(ValueError, 'Local changes'):
            worker.inspect(self.repo)
        self.assertEqual(file.read_text(), 'unfinished work')
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), self.old)

    def test_other_branch_or_origin_is_rejected(self):
        self.run_git(self.repo, 'checkout', '-b', 'feature')
        with self.assertRaisesRegex(ValueError, 'Select main'):
            worker.inspect(self.repo)
        self.run_git(self.repo, 'checkout', 'main')
        self.run_git(self.repo, 'remote', 'set-url', 'origin', 'https://example.invalid/unrelated')
        with self.assertRaisesRegex(ValueError, 'origin'):
            worker.inspect(self.repo)

    def test_current_ahead_and_diverged_are_distinguished(self):
        worker.inspect(self.repo)
        self.run_git(self.repo, 'merge', '--ff-only', self.new)
        self.assertEqual(worker.inspect(self.repo)['state'], 'current')
        (self.repo / 'local.txt').write_text('local commit')
        self.commit(self.repo, 'local')
        self.assertEqual(worker.inspect(self.repo)['state'], 'ahead')
        self.advance('1.2.0')
        with self.assertRaisesRegex(ValueError, 'diverged'):
            worker.inspect(self.repo)
        self.assertEqual((self.repo / 'local.txt').read_text(), 'local commit')

    def test_prepared_bundle_uses_reviewed_commit_without_applying_it(self):
        bundle = self.root / 'update bundle'
        result = worker.prepare(self.repo, self.new, bundle, 'linux')
        self.assertEqual(result['revision'], self.new)
        self.assertTrue((bundle / 'runner.py').exists())
        self.assertEqual((bundle / 'update-linux.sh').read_text(), '# synthetic installer fixture\n')
        self.assertEqual(self.run_git(self.repo, 'rev-parse', 'HEAD'), self.old)

    def test_remote_change_after_review_requires_new_check(self):
        self.advance('1.2.0')
        bundle = self.root / 'unused bundle'
        with self.assertRaisesRegex(ValueError, 'changed'):
            worker.prepare(self.repo, self.new, bundle, 'linux')
        self.assertFalse(bundle.exists())

    def test_network_failure_does_not_expose_credential_output(self):
        with mock.patch('subprocess.run', return_value=subprocess.CompletedProcess([], 1, b'', b'secret-token-example')):
            with self.assertRaisesRegex(ValueError, 'Git could not complete') as error:
                worker.git(self.repo, 'fetch', 'origin', 'main')
        self.assertNotIn('secret-token-example', str(error.exception))
