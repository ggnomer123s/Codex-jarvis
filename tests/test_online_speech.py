"""Online transport contracts use fake streams; no real service or user text."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from tigo_gui.online_worker import synthesize, phrases, MAX_MP3_BYTES


class TestOnlineTransport(unittest.IsolatedAsyncioTestCase):
    async def test_short_sentences_stay_together_and_long_speech_is_bounded(self):
        short = 'Hello, mentor. I am Tigo. Let us check my voice.'
        self.assertEqual(list(phrases(short)), [short])
        long = 'A clear sentence for a voice preview. '*100
        parts = list(phrases(long))
        self.assertTrue(all(0 < len(part) <= 240 for part in parts))
        self.assertEqual(' '.join(parts), ' '.join(long.split()))

    async def test_collects_only_audio_and_bounds_speed(self):
        calls = []
        class Client:
            def __init__(self, *args, **kwargs): calls.append((args, kwargs))
            async def stream(self):
                yield {'type': 'WordBoundary', 'text': 'fixture'}
                yield {'type': 'audio', 'data': b'abc'}
                yield {'type': 'audio', 'data': b'def'}
        raw = await synthesize('A test phrase.', 'en-US-AriaNeural', 9., factory=Client)
        self.assertEqual(raw, b'abcdef')
        self.assertEqual(calls, [(('A test phrase.', 'en-US-AriaNeural'), {'rate': '+30%'})])

    async def test_invalid_voice_and_oversized_text_cannot_contact_a_service(self):
        def forbidden(*args, **kwargs): self.fail('Invalid input contacted a service')
        for text, voice, speed in [('hello', 'https://untrusted.invalid', 1.), ('a'*241, 'en-US-AriaNeural', 1.),
                                   ('hello', 'en-US-AriaNeural', float('nan'))]:
            with self.assertRaises(ValueError):
                await synthesize(text, voice, speed, factory=forbidden)

    async def test_empty_or_oversized_service_audio_is_rejected(self):
        class Empty:
            async def stream(self):
                yield {'type': 'metadata'}
        class Oversized:
            async def stream(self):
                yield {'type': 'audio', 'data': b'a'*(MAX_MP3_BYTES+1)}
        for client in (Empty, Oversized):
            with self.assertRaises(ValueError):
                await synthesize('test', 'en-US-AriaNeural', factory=lambda *a, **k: client())

    async def test_service_errors_are_not_retried_or_redirected(self):
        calls = []
        class Failed:
            async def stream(self):
                calls.append(1)
                raise ConnectionError('fixture disconnect')
                yield
        with self.assertRaises(ConnectionError):
            await synthesize('test', 'en-US-AriaNeural', factory=lambda *a, **k: Failed())
        self.assertEqual(calls, [1])
