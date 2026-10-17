"""Keyless personal-use Google Web Speech dictation over HTTPS.

Uses SpeechRecognition's built-in public service configuration. No personal
API key/account or automatic retries. PCM/FLAC/response stay bounded in RAM.
The public service is not Google Cloud and has no availability guarantee.
"""
from __future__ import annotations

import urllib.error
import urllib.request

LANGUAGE_TAGS = {"ru": "ru-RU", "en": "en-US", "uk": "uk-UA", "de": "de-DE",
                 "fr": "fr-FR", "es": "es-ES", "it": "it-IT", "pt": "pt-PT",
                 "pl": "pl-PL", "tr": "tr-TR", "ar": "ar-SA", "zh": "zh-CN",
                 "ja": "ja-JP", "ko": "ko-KR", "hi": "hi-IN"}
ENDPOINT = "https://www.google.com/speech-api/v2/recognize"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Speech service redirected; audio was not forwarded.")


def transcribe_online(pcm, language, *, opener=None):
    if language not in LANGUAGE_TAGS:
        raise ValueError("Select a speech language for online dictation. Auto detect is available locally.")
    if not isinstance(pcm, bytes) or len(pcm) % 2 or not 32000 <= len(pcm) <= 16000 * 60 * 2:
        raise ValueError("Dictation must contain 1 to 60 seconds of mono 16 kHz PCM audio.")
    from speech_recognition import AudioData, UnknownValueError
    from speech_recognition.recognizers.google import create_request_builder, OutputParser
    try:
        # The library supplies its personal/testing service configuration; users
        # do not provide an API key. Explicit HTTPS replaces its legacy HTTP URL.
        builder = create_request_builder(endpoint=ENDPOINT, language=LANGUAGE_TAGS[language])
        request = builder.build(AudioData(pcm, 16000, 2))
        send = opener or urllib.request.build_opener(NoRedirect()).open
        with send(request, timeout=45) as response:
            raw = response.read(262145)
        if len(raw) > 262144:
            raise ValueError("Online transcription response is too large.")
        text = OutputParser(show_all=False, with_confidence=False).parse(raw.decode("utf-8"))
        if not isinstance(text, str) or not text.strip() or len(text) > 60000:
            raise ValueError("Online transcription returned no usable speech text.")
        return text.strip()
    except UnknownValueError:
        raise RuntimeError("Online service could not recognize speech. Try again or select Local Whisper.") from None
    except urllib.error.HTTPError as exc:
        code = exc.code
        exc.close()
        raise RuntimeError(f"Google Web Speech is unavailable (HTTP {code}). No retry was sent; select Local Whisper.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("Online transcription connection failed or timed out. Select Local Whisper to work offline.") from None
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise RuntimeError("Online transcription returned an invalid response. Select Local Whisper or try a shorter recording.") from None
