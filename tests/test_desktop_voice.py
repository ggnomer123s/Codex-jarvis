"""Voice-worker lifecycle with simulated audio; no hardware or model download."""
import contextlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gui"))
from tigo_gui import voice


class AudioArray:
    def astype(self, dtype):
        return self

    def __truediv__(self, value):
        return self

    def __mul__(self, other):
        return self


class TestDesktopVoice(unittest.TestCase):
    def run_worker(self, frames=16000, transcript="A reviewed request", microphone_error=None, argv=()):
        class Stream:
            def __init__(self, **kwargs):
                self.callback = kwargs["callback"]

            def __enter__(self):
                if microphone_error:
                    raise RuntimeError(microphone_error)
                self.callback(b"\0" * frames * 2, frames, None, None)
                return self

            def __exit__(self, *args):
                return False

        numpy = types.SimpleNamespace(frombuffer=lambda *args, **kwargs: AudioArray(),
                                      int16=int, float32=float, sqrt=lambda n: 0.1, mean=lambda a: 0.01)
        engine = mock.Mock()
        engine.transcribe.return_value = ([types.SimpleNamespace(text=transcript)], None)
        model = mock.Mock(return_value=engine)
        output = io.StringIO()
        modules = {"numpy": numpy, "sounddevice": types.SimpleNamespace(RawInputStream=Stream),
                   "faster_whisper": types.SimpleNamespace(WhisperModel=model)}
        with mock.patch.object(voice, "dependencies_available", return_value=True), \
                mock.patch.dict(sys.modules, modules), mock.patch.object(sys, "stdin", io.StringIO("stop\n")), \
                contextlib.redirect_stdout(output):
            code = voice.main(argv)
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        return code, events, model

    def test_recording_then_local_transcription(self):
        code, events, model = self.run_worker()
        self.assertEqual(code, 0)
        self.assertEqual([e["type"] for e in events], ["level", "recording", "transcribing", "transcript"])
        self.assertEqual(events[-1]["text"], "A reviewed request")
        self.assertEqual(model.call_args.kwargs["device"], "cpu")

    def test_short_recording_does_not_load_a_model(self):
        code, events, model = self.run_worker(frames=1024)
        self.assertEqual(code, 1)
        self.assertEqual(events[-1]["type"], "error")
        model.assert_not_called()

    def test_microphone_error_is_reported(self):
        code, events, model = self.run_worker(microphone_error="Microphone permission denied")
        self.assertEqual(code, 2)
        self.assertIn("permission denied", events[-1]["message"])
        model.assert_not_called()

    def test_empty_transcription_is_not_submitted(self):
        code, events, _ = self.run_worker(transcript="")
        self.assertEqual(code, 1)
        self.assertEqual(events[-1]["type"], "error")

    def test_russian_and_medium_model_are_forwarded_to_local_whisper(self):
        code, events, model = self.run_worker(argv=["--language", "ru", "--model", "medium"], transcript="\u041f\u0440\u0438\u0432\u0435\u0442")
        self.assertEqual(code, 0)
        self.assertEqual(model.call_args.args[0], "medium")
        self.assertEqual(model.return_value.transcribe.call_args.kwargs["language"], "ru")
        self.assertEqual(events[-1]["text"], "\u041f\u0440\u0438\u0432\u0435\u0442")

    def test_auto_language_uses_whisper_detection(self):
        _, _, model = self.run_worker(argv=["--language", "auto", "--model", "tiny"])
        self.assertIsNone(model.return_value.transcribe.call_args.kwargs["language"])

    def test_invalid_language_fails_before_microphone_is_opened(self):
        code, events, model = self.run_worker(argv=["--language", "invalid"])
        self.assertEqual(code, 2)
        self.assertEqual(events[0]["type"], "error")
        model.assert_not_called()


class TestPersistentVoice(unittest.TestCase):
    def worker(self, cancel=False):
        events = []
        holder = {}

        class Stream:
            def __init__(self, **kwargs):
                self.callback = kwargs['callback']

            def __enter__(self):
                self.callback(b'\0' * 32000, 16000, None, None)
                return self

            def __exit__(self, *args):
                return False

        numpy = types.SimpleNamespace(frombuffer=lambda *a, **kw: AudioArray(), int16=int,
                                      float32=float, sqrt=lambda n: .1, mean=lambda a: .01)
        sd = types.SimpleNamespace(RawInputStream=Stream, query_devices=lambda: [{'name':'Test microphone','max_input_channels':1}])
        engine = mock.Mock()
        engine.transcribe.return_value = ([types.SimpleNamespace(text='review me')], None)
        factory = mock.Mock(return_value=engine)

        def output(kind, **values):
            events.append({'type':kind, **values})
            if kind == 'level':
                holder['worker'].stop.set()
                if cancel:
                    holder['worker'].cancelled.set()

        with mock.patch.dict(sys.modules, {'numpy':numpy,'sounddevice':sd}):
            worker = voice.VoiceWorker('base', model_factory=factory, output=output)
        holder['worker'] = worker
        return worker, factory, events

    def test_one_model_serves_two_recordings_and_keeps_russian(self):
        worker, factory, events = self.worker()
        for recording_id in ('recording-1','recording-2'):
            worker.command({'command':'record','id':recording_id,'language':'ru','beam':1})
            worker.thread.join(2)
            self.assertFalse(worker.thread.is_alive())
        factory.assert_called_once()
        self.assertEqual(factory.return_value.transcribe.call_count, 2)
        self.assertEqual(factory.return_value.transcribe.call_args.kwargs['language'], 'ru')
        self.assertEqual(factory.return_value.transcribe.call_args.kwargs['beam_size'], 1)
        self.assertEqual([e['id'] for e in events if e['type']=='transcript'], ['recording-1','recording-2'])
        self.assertEqual(worker.devices()[0]['id'], '0')

    def test_cancelled_recording_does_not_produce_transcript(self):
        worker, factory, events = self.worker(cancel=True)
        worker.command({'command':'record','id':'abandoned','language':'ru'})
        worker.thread.join(2)
        self.assertFalse(any(e['type']=='transcript' for e in events))
        factory.return_value.transcribe.assert_not_called()
        self.assertEqual(events[-1]['type'], 'idle')

    def test_stop_for_old_recording_cannot_stop_a_new_recording(self):
        worker, _, _ = self.worker()
        worker.recording_id = 'current'
        worker.command({'command':'stop','id':'old'})
        self.assertFalse(worker.stop.is_set())
        worker.command({'command':'stop','id':'current'})
        self.assertTrue(worker.stop.is_set())


if __name__ == "__main__":
    unittest.main()
