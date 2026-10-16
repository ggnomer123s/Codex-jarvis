"""Content-free metrics and profile-scoped checkpoints, without Qt or network."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gui"))
from tigo_gui.core import thread_options, turn_options
from tigo_gui.runtime import Checkpoints, Profiler


class Settings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


class TestRuntime(unittest.TestCase):
    def test_timing_intervals_and_no_task_content(self):
        now = [10.0]
        profiler = Profiler(clock=lambda: now[0])
        profiler.begin("codex")
        now[0] += .1
        profiler.mark("serverReady")
        profiler.tool_start("tool", "screenshot")
        now[0] += .2
        profiler.tool_end("tool")
        profiler.mark("firstText")
        profiler.finish("completed")
        task = profiler.export()["tasks"][0]
        self.assertEqual(task["durationMs"], 300)
        self.assertEqual(task["tools"][0]["durationMs"], 200)
        self.assertEqual(task["toolCount"], 1)
        self.assertEqual(task["screenshotCount"], 1)
        self.assertNotIn("prompt", task)
        self.assertNotIn("arguments", json.dumps(task))
        self.assertIsNone(profiler.current)

    def test_checkpoint_isolated_by_profile_workspace_model_and_permissions(self):
        settings = Settings()
        points = Checkpoints(settings)
        args = (Path('/tmp/normal'), Path('/tmp/work'), 'read-only', 'model')
        key = points.key(*args)
        points.save(key, 'thread-1', 'interrupted', 2)
        restored = Checkpoints(settings)
        self.assertEqual(restored.get(key)['completedSteps'], 2)
        for changed in [(Path('/tmp/full'), *args[1:]), (args[0], Path('/tmp/other'), *args[2:]),
                        (*args[:2], 'full-access', args[3]), (*args[:3], 'other-model')]:
            self.assertFalse(restored.get(points.key(*changed)))
        restored.forget(key)
        self.assertFalse(Checkpoints(settings).get(key))

    def test_corrupt_checkpoint_data_does_not_crash(self):
        settings = Settings()
        for data in ('[]', 'not json', 'null', '{"key": 42}'):
            settings.setValue('threadCheckpoints', data)
            self.assertFalse(Checkpoints(settings).get('key'))

    def test_app_server_inputs_keep_prompt_as_data_and_access_explicit(self):
        options = thread_options(str(Path(__file__).parent), 'full-access', 'provider/model')
        self.assertEqual(options['sandbox'], 'danger-full-access')
        self.assertEqual(options['approvalPolicy'], 'never')
        self.assertEqual(options['model'], 'provider/model')
        prompt = '--model unsafe; $(literal)'
        value = turn_options('thread', prompt, 'high')
        self.assertEqual(value['input'][0]['text'], prompt)
        self.assertEqual(value['effort'], 'high')
        self.assertNotIn('effort', turn_options('thread', prompt, 'default'))
        with self.assertRaises(ValueError):
            thread_options(str(Path(__file__).parent), 'unsafe')


if __name__ == '__main__':
    unittest.main()
