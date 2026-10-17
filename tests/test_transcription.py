"""Keyless HTTPS dictation framing/error behavior; no audio upload or API key."""
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'gui'))
from tigo_gui import transcription


class TestKeylessTranscription(unittest.TestCase):
    def modules(self):
        class UnknownValueError(Exception): pass
        def build(audio):
            self.assertEqual(audio, (b'\0'*32000, 16000, 2))
            return Request(transcription.ENDPOINT, data=b'fixture-flac')
        self.builder = mock.Mock(side_effect=lambda **kw: types.SimpleNamespace(build=build))
        class Parser:
            def __init__(self, **kwargs): pass
            def parse(self, raw): return json.loads(raw)['text']
        return {'speech_recognition': types.SimpleNamespace(AudioData=lambda *v:v, UnknownValueError=UnknownValueError),
                'speech_recognition.recognizers':types.ModuleType('speech_recognition.recognizers'),
                'speech_recognition.recognizers.google':types.SimpleNamespace(create_request_builder=self.builder, OutputParser=Parser)}

    def test_selected_language_and_https_without_user_credentials(self):
        modules = self.modules()
        def send(request, timeout):
            self.assertEqual(timeout, 45)
            self.assertTrue(request.full_url.startswith('https://www.google.com/'))
            self.assertNotIn('Authorization', request.headers)
            return io.BytesIO(json.dumps({'text':'  Recognized speech.  '}).encode())
        with mock.patch.dict(sys.modules, modules):
            self.assertEqual(transcription.transcribe_online(b'\0'*32000, 'ru', opener=send), 'Recognized speech.')
        self.builder.assert_called_once_with(endpoint=transcription.ENDPOINT, language='ru-RU')

    def test_invalid_audio_or_auto_language_never_sends(self):
        send = mock.Mock()
        for audio, lang in ((b'\0'*32000,'auto'), (b'\0','ru'), (b'\0'*1920002,'en')):
            with self.assertRaises(ValueError): transcription.transcribe_online(audio, lang, opener=send)
        send.assert_not_called()

    def test_http_and_network_errors_are_redacted_without_retry(self):
        modules = self.modules()
        for error in (HTTPError('https://secret.invalid/?key=private', 429, 'private', {}, None), URLError('private')):
            send = mock.Mock(side_effect=error)
            with mock.patch.dict(sys.modules, modules), self.assertRaises(RuntimeError) as caught:
                transcription.transcribe_online(b'\0'*32000, 'ru', opener=send)
            self.assertNotIn('private', str(caught.exception))
            send.assert_called_once()

    def test_oversized_malformed_and_empty_responses_fail(self):
        modules = self.modules()
        for raw in (b'x'*262145, b'not json', b'{"text":""}'):
            with mock.patch.dict(sys.modules, modules), self.assertRaises(RuntimeError):
                transcription.transcribe_online(b'\0'*32000,'en',opener=lambda *a,**kw:io.BytesIO(raw))

    def test_redirect_is_not_followed(self):
        with self.assertRaises(RuntimeError):
            transcription.NoRedirect().redirect_request(None,None,302,'',{},'http://other.invalid')
