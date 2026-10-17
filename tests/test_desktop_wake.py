"""Wake-name, bounded audio and startup tests without models or microphones."""
from array import array
from pathlib import Path
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from tigo_gui.wake import contains_wake_name, PhraseBuffer, WakeListener, audio_rms, normalize_phrase
from tigo_gui.autostart import set_autostart, MARKER, RUN_NAME


class TestWakeName(unittest.TestCase):
    def test_exact_russian_english_case_punctuation(self):
        for text in ['Hey, TIGO!', '\u0422\u0438\u0433\u043e, open the app', 'hello tigo please', '\uff34\uff49\uff47\uff4f']:
            self.assertTrue(contains_wake_name(text, False), text)

    def test_similar_names_and_split_words(self):
        for text in ['teego', 'tiggo', 'tygo', 'tido', 'tiga', '\u0442\u0438\u0434\u043e', '\u0442\u0438\u0433\u0430', 'ti go', '\u0442\u0438 \u0433\u043e', '\u0442\u0438\u0433\u0433\u043e']:
            self.assertTrue(contains_wake_name(text), text)
            self.assertFalse(contains_wake_name(text, False), text)

    def test_mixed_latin_cyrillic_name_from_multilingual_asr(self):
        for text in ['\u0422igo.', 'T\u0438go', 'Ti\u0433o', 'Tig\u043e', '\u0422\u0438g\u043e']:
            self.assertTrue(contains_wake_name(text, False), text)
        for text in ['\u0422ime', '\u0442\u043e\u0433\u043e', '\u0442\u0438\u0445\u043e', '\u0422iger', 'a\u0422igo']:
            self.assertFalse(contains_wake_name(text), text)

    def test_unrelated_words_and_substrings_do_not_wake(self):
        for text in ['', 'hello there', 'service', 'time', 'taco', 'togo', 'tiger', 'atigocode',
                     '\u0422\u0430\u0439\u0433\u0430', '\u0421\u0438\u0433\u0430',
                     '\u0442\u043e\u0433\u043e', '\u0442\u0438\u0445\u043e', 'jarvis',
                     '\u0434\u0436\u0430\u0440\u0432\u0438\u0441', 'javascript']:
            self.assertFalse(contains_wake_name(text), text)


class TestPhraseBuffer(unittest.TestCase):
    @staticmethod
    def buffer():
        # Inject speech decisions, not a hardware/model-dependent DC waveform.
        return PhraseBuffer(classifier=lambda frame, rate: any(frame))

    def test_silence_and_short_noise_do_not_transcribe(self):
        buffer = self.buffer()
        for _ in range(200):
            self.assertIsNone(buffer.feed(bytes(2048)))
        self.assertIsNone(buffer.feed(array('h', [2000] * 1024).tobytes()))
        self.assertFalse(any(buffer.feed(bytes(2048)) for _ in range(20)))

    def test_quiet_short_name_reaches_recognition_and_framing_is_exact(self):
        seen = []
        def classify(frame, rate):
            seen.append((len(frame), rate))
            return any(frame)
        buffer = PhraseBuffer(classifier=classify)
        # 180 ms at -60 dBFS: the previous .01 RMS gate discarded it.
        speech = array('h', [32, -32] * 1440).tobytes()
        raw = bytes(6400) + speech + bytes(32000)
        phrases = [buffer.feed(raw[p:p+2048]) for p in range(0, len(raw), 2048)]
        self.assertEqual(sum(x is not None for x in phrases), 1)
        self.assertIn(speech, next(x for x in phrases if x))
        self.assertTrue(all(x == (640, 16000) for x in seen))
        self.assertLess(len(buffer.pending), 640)

    def test_speech_flushes_after_pause_and_continuous_speech_is_bounded(self):
        buffer = self.buffer()
        raw = array('h', [2000] * 1024).tobytes()
        for _ in range(8):
            self.assertIsNone(buffer.feed(raw))
        results = [buffer.feed(bytes(2048)) for _ in range(12)]
        self.assertEqual(sum(x is not None for x in results), 1)
        buffer.reset()
        results = [buffer.feed(raw) for _ in range(200)]
        phrases = [x for x in results if x]
        self.assertGreaterEqual(len(phrases), 3)
        self.assertTrue(all(len(x) <= 128000 for x in phrases))
        self.assertLessEqual(len(buffer.parts), 200)

    def test_separated_clicks_cannot_accumulate_into_speech(self):
        buffer = self.buffer()
        for _ in range(20):
            self.assertIsNone(buffer.feed(array('h', [2000] * 320).tobytes()))
            for _ in range(12):
                self.assertIsNone(buffer.feed(bytes(2048)))

    def test_gain_is_bounded_no_clipping_and_silence_unchanged(self):
        self.assertEqual(normalize_phrase(bytes(1000)), bytes(1000))
        quiet = array('h', [32, -32] * 1600).tobytes()
        louder = normalize_phrase(quiet)
        self.assertAlmostEqual(audio_rms(louder) / audio_rms(quiet), 12)
        loud = array('h', [-32768, 32767] * 320).tobytes()
        self.assertEqual(normalize_phrase(loud), loud)
        spike = array('h', [100] * 1600 + [30000]).tobytes()
        self.assertLessEqual(max(array('h', normalize_phrase(spike))), 32000)


class Audio:
    def astype(self, _): return self
    def __truediv__(self, _): return self


class TestWakeWorker(unittest.TestCase):
    def worker(self,provider="local"):
        events = []
        model = mock.Mock()
        model.transcribe.return_value = ([types.SimpleNamespace(text='hey tigo')], None)
        np = types.SimpleNamespace(frombuffer=lambda *a, **k: Audio(), int16=int, float32=float)
        with mock.patch.dict(sys.modules, {'numpy': np, 'sounddevice': types.SimpleNamespace()}):
            worker = WakeListener('base', 'ru', model_factory=mock.Mock(return_value=model),
                                  output=lambda kind, **data: events.append({'type': kind, **data}),provider=provider)
        return worker, model, events

    def wait(self, condition):
        deadline = time.monotonic() + 2
        while not condition() and time.monotonic() < deadline:
            time.sleep(.005)
        self.assertTrue(condition())

    def test_online_wake_uses_selected_language_and_discards_ordinary_transcripts(self):
        worker, model, events = self.worker('online')
        self.assertIsNone(worker.model)
        with mock.patch('tigo_gui.transcription.transcribe_online',side_effect=['ordinary private words','Tigo']) as transcribe:
            worker.jobs.put((0,b'\0'*16000));worker.jobs.put((0,b'\0'*16000))
            thread=threading.Thread(target=worker._infer);thread.start()
            self.wait(lambda:any(e['type'] == 'wake' for e in events))
            worker.command({'command':'shutdown'});thread.join(1)
        model.transcribe.assert_not_called()
        self.assertEqual([e for e in events if e['type'] == 'wake'],[{'type':'wake'}])
        self.assertTrue(all(set(e) <= {'type', 'result'} for e in events))
        self.assertEqual(transcribe.call_args.args,(b'\0'*32000,'ru'))

    def test_unintelligible_online_phrase_does_not_disable_listener(self):
        from tigo_gui.transcription import UnrecognizedSpeech
        worker, _, events = self.worker('online')
        with mock.patch('tigo_gui.transcription.transcribe_online',side_effect=[UnrecognizedSpeech('unclear'),'Tigo']):
            worker.jobs.put((0,b'\0'*32000));worker.jobs.put((0,b'\0'*32000))
            thread=threading.Thread(target=worker._infer);thread.start()
            self.wait(lambda:any(e['type'] == 'wake' for e in events))
            worker.command({'command':'shutdown'});thread.join(1)
        self.assertFalse(worker.failed)
        self.assertEqual([e for e in events if e['type'] == 'wake'],[{'type':'wake'}])
        self.assertTrue(all(set(e) <= {'type', 'result'} for e in events))

    def test_repeated_speech_cooldown_and_no_transcript_ipc(self):
        worker, model, events = self.worker()
        worker.jobs.put((0, bytes(16000)))
        worker.jobs.put((0, bytes(16000)))
        thread = threading.Thread(target=worker._infer)
        thread.start()
        self.wait(lambda: len([e for e in events if e['type'] == 'recognition']) == 2)
        worker.command({'command': 'shutdown'})
        thread.join(1)
        self.assertEqual([e for e in events if e['type'] == 'wake'], [{'type': 'wake'}])
        self.assertEqual([e['result'] for e in events if e['type'] == 'recognition'], ['matched', 'matched'])
        self.assertEqual(model.transcribe.call_args.kwargs['language'], 'ru')
        self.assertFalse(thread.is_alive())

    def test_quiet_short_phrase_is_amplified_for_both_providers(self):
        quiet = array('h', [32, -32] * 1440).tobytes()
        raw = bytes(6400) + quiet + bytes(32000)
        for provider in ('local', 'online'):
            with self.subTest(provider=provider):
                buffer = PhraseBuffer(classifier=lambda frame, rate: any(frame))
                phrases = [buffer.feed(raw[p:p+2048]) for p in range(0, len(raw), 2048)]
                phrase = next(p for p in phrases if p)
                worker, _, events = self.worker(provider)
                received = []
                worker.np = types.SimpleNamespace(int16=int, float32=float,
                    frombuffer=lambda raw, **kw: received.append(raw) or Audio())
                def online(raw, language):
                    received.append(raw)
                    return '\u0422\u0438\u0433\u043e'
                with mock.patch('tigo_gui.transcription.transcribe_online', side_effect=online):
                    worker.jobs.put((0, phrase))
                    thread = threading.Thread(target=worker._infer); thread.start()
                    self.wait(lambda: any(e['type'] == 'wake' for e in events))
                    worker.command({'command': 'shutdown'}); thread.join(1)
                self.assertEqual(max(array('h', received[0])), 384)
                self.assertTrue(all(set(e) <= {'type', 'result'} for e in events))

    def test_pausing_during_inference_discards_late_recognition(self):
        worker, model, events = self.worker()
        entered, release = threading.Event(), threading.Event()
        def infer(*args, **kwargs):
            entered.set(); release.wait(2)
            return [types.SimpleNamespace(text='tigo')], None
        model.transcribe.side_effect = infer
        worker.jobs.put((0, bytes(16000)))
        thread = threading.Thread(target=worker._infer)
        thread.start()
        self.assertTrue(entered.wait(1))
        worker.command({'command': 'pause', 'token': 'manual'})
        release.set()
        self.wait(worker.jobs.empty)
        worker.command({'command': 'shutdown'})
        thread.join(1)
        self.assertEqual(events, [])

    def test_late_online_failure_after_pause_does_not_stop_listener(self):
        worker, _, events = self.worker('online')
        entered, release, returned = threading.Event(), threading.Event(), threading.Event()
        def recognize(*args):
            entered.set();release.wait(2);returned.set()
            raise RuntimeError('late service failure')
        with mock.patch('tigo_gui.transcription.transcribe_online',side_effect=recognize):
            worker.jobs.put((0,b'\0'*32000))
            thread=threading.Thread(target=worker._infer);thread.start()
            self.assertTrue(entered.wait(1))
            worker.command({'command':'pause','token':'dictation'})
            release.set();self.assertTrue(returned.wait(1))
            worker.command({'command':'shutdown'});thread.join(1)
        self.assertFalse(worker.failed)
        self.assertEqual(events,[])

    @staticmethod
    def buffer_for_pause():
        return PhraseBuffer(classifier=lambda frame, rate: False)

    def test_pause_acknowledges_microphone_closed(self):
        worker, _, events = self.worker()
        closed = threading.Event()
        class Stream:
            def __init__(self, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): closed.set()
        worker.sd = types.SimpleNamespace(RawInputStream=Stream)
        worker._commands = lambda: None
        def output(kind, **data):
            events.append({'type': kind, **data})
            if kind == 'listening': worker.command({'command': 'pause', 'token': 'test'})
            if kind == 'paused':
                self.assertTrue(closed.is_set())
                worker.command({'command': 'shutdown'})
        worker.output = output
        with mock.patch('tigo_gui.wake.PhraseBuffer', side_effect=self.buffer_for_pause):
            self.assertEqual(worker.run(), 0)
        self.assertEqual([e['type'] for e in events], ['listening', 'paused'])
        self.assertEqual(events[-1]['token'], 'test')


class TestWakeAutostart(unittest.TestCase):
    def test_linux_enable_update_disable_and_quoted_paths(self):
        with tempfile.TemporaryDirectory(prefix='wake with spaces ') as folder:
            path = Path(folder) / 'autostart/tigo-voice.desktop'
            command = ['/path with spaces/100%/python', '-m', 'tigo_gui', '--background']
            set_autostart(True, command, platform='linux', config_home=folder)
            text = path.read_text()
            self.assertIn(MARKER, text)
            self.assertIn('"/path with spaces/100%%/python"', text)
            set_autostart(True, ['/new/python', *command[1:]], platform='linux', config_home=folder)
            self.assertIn('/new/python', path.read_text())
            set_autostart(False, command, platform='linux', config_home=folder)
            self.assertFalse(path.exists())

    def test_owned_legacy_startup_is_replaced_but_unrelated_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            old = Path(folder) / 'autostart/jarvis-voice.desktop'
            old.parent.mkdir()
            old.write_text('# JARVIS-CODEX MANAGED: voice activation\nExec=old\n')
            set_autostart(True, ['/new/python', '-m', 'tigo_gui', '--background'], platform='linux', config_home=folder)
            self.assertFalse(old.exists())
            self.assertTrue((old.parent / 'tigo-voice.desktop').exists())
            old.write_text('unrelated application')
            set_autostart(False, platform='linux', config_home=folder)
            self.assertEqual(old.read_text(), 'unrelated application')

    def test_linux_unmanaged_files_and_symlinks_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'autostart/tigo-voice.desktop'
            path.parent.mkdir()
            path.write_text('unrelated application')
            for enabled in (True, False):
                with self.assertRaises(ValueError):
                    set_autostart(enabled, platform='linux', config_home=folder)
            self.assertEqual(path.read_text(), 'unrelated application')
            if sys.platform != 'win32':
                path.unlink(); path.symlink_to(Path(folder) / 'other')
                with self.assertRaises(ValueError):
                    set_autostart(True, platform='linux', config_home=folder)

    def test_windows_legacy_startup_is_retired_after_registering_tigo(self):
        def query(key, name):
            if name == 'JarvisVoiceActivation':
                return ('pythonw.exe -m jarvis_gui --background', 1)
            raise FileNotFoundError
        registry = types.SimpleNamespace(HKEY_CURRENT_USER='current-user', REG_SZ=1,
                                         CreateKey=mock.MagicMock(), QueryValueEx=mock.Mock(side_effect=query),
                                         SetValueEx=mock.Mock(), DeleteValue=mock.Mock())
        with mock.patch.dict(sys.modules, {'winreg': registry}):
            set_autostart(True, ['pythonw.exe', '-m', 'tigo_gui', '--background'], platform='win32')
        self.assertEqual(registry.SetValueEx.call_args.args[1], RUN_NAME)
        self.assertEqual(registry.DeleteValue.call_args.args[-1], 'JarvisVoiceActivation')

    def test_windows_registers_only_current_user_and_removes_owned_value(self):
        registry = types.SimpleNamespace(HKEY_CURRENT_USER='current-user', REG_SZ=1,
                                         CreateKey=mock.MagicMock(), QueryValueEx=mock.Mock(side_effect=FileNotFoundError),
                                         SetValueEx=mock.Mock(), DeleteValue=mock.Mock())
        with mock.patch.dict(sys.modules, {'winreg': registry}):
            set_autostart(True, ['C:\\Program Files\\Python\\pythonw.exe', '-m', 'tigo_gui', '--background'], platform='win32')
            self.assertEqual(registry.CreateKey.call_args.args[0], 'current-user')
            self.assertIn('"C:\\Program Files\\Python\\pythonw.exe"', registry.SetValueEx.call_args.args[-1])
            registry.QueryValueEx.side_effect = None
            registry.QueryValueEx.return_value = (registry.SetValueEx.call_args.args[-1], 1)
            set_autostart(False, platform='win32')
            self.assertEqual(registry.DeleteValue.call_args.args[-1], RUN_NAME)
            registry.QueryValueEx.return_value = ('unrelated.exe', 1)
            with self.assertRaises(ValueError): set_autostart(True, platform='win32')


if __name__ == '__main__':
    unittest.main()
