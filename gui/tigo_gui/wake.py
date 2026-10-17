"""Explicit local/online background transcription and wake-name detection.

Only wake/status events leave this process. Audio and ordinary transcripts are
bounded, transient memory; nothing is submitted to Codex or written to history.
"""
from __future__ import annotations

import argparse
from array import array
from collections import deque
import json
import math
import os
import queue
import re
import sys
import threading
import time
import unicodedata

from .preferences import LANGUAGES, valid_voice_model
from .transcription import UnrecognizedSpeech

SAMPLE_RATE = 16000
COOLDOWN = 8.0
# Escapes keep managed source English-only, including wake-name fixtures.
NAMES = ("tigo", "\u0442\u0438\u0433\u043e")
# Four-letter names are too short for arbitrary one-edit matching: it would
# activate on ordinary words such as "time", "taco" or Russian "togo".
ALIASES = (*NAMES, "teego", "tiggo", "tygo", "\u0442\u0438\u0433\u0433\u043e")


def contains_wake_name(text, fuzzy=True):
    words = re.findall(r"[a-z\u0430-\u044f\u0451]+", unicodedata.normalize("NFKC", str(text)[:4000]).casefold())[:300]
    if any(word in NAMES for word in words):
        return True
    if not fuzzy:
        return False
    if any(word in ALIASES for word in words):
        return True
    return any(a + b in NAMES for a, b in zip(words, words[1:]))


class PhraseBuffer:
    """Energy-gated phrases: 0.65 s silence or 4 s maximum, 256 ms overlap."""

    def __init__(self, threshold=0.01):
        self.threshold = threshold
        self.reset()

    def reset(self):
        self.pre = deque(maxlen=4)
        self.parts = []
        self.duration = self.silence = self.voiced = 0.0

    def feed(self, raw):
        samples = array('h', raw)
        if sys.byteorder != 'little':
            samples.byteswap()
        if not samples:
            return None
        duration = len(samples) / SAMPLE_RATE
        speech = math.sqrt(sum(x * x for x in samples) / len(samples)) / 32768 >= self.threshold
        if not self.parts:
            if not speech:
                self.pre.append(raw)
                return None
            self.parts = list(self.pre)
            self.duration = sum(len(x) for x in self.parts) / (SAMPLE_RATE * 2)
        self.parts.append(raw)
        self.pre.append(raw)
        self.duration += duration
        self.voiced += duration if speech else 0
        self.silence = 0 if speech else self.silence + duration
        if self.silence >= 0.65 or self.duration >= 4.0:
            result = b''.join(self.parts) if self.voiced >= 0.25 else None
            self.parts = []
            self.duration = self.silence = self.voiced = 0
            return result
        return None


class WakeListener:
    def __init__(self, model, language='auto', microphone='', fuzzy=True, *, model_factory=None, output=None, provider="local"):
        import numpy as np
        import sounddevice as sd
        self.provider = provider
        if provider == "local" and model_factory is None:
            from faster_whisper import WhisperModel
            model_factory = WhisperModel
        self.np, self.sd = np, sd
        self.model = (model_factory(model, device='cpu', compute_type='int8',
                                   cpu_threads=max(1, min(4, (os.cpu_count() or 2) // 2)), num_workers=1)
                      if provider == 'local' else None)
        self.language, self.microphone, self.fuzzy = language, microphone, fuzzy
        self.output = output or emit
        self.allowed = threading.Event()
        self.allowed.set()
        self.shutdown = threading.Event()
        self.jobs = queue.Queue(maxsize=2)
        self.generation = 0
        self.pause_token = ''
        self.last_wake = -COOLDOWN
        self.failed = False

    def command(self, value):
        command = value.get('command')
        if command == 'pause':
            self.generation += 1
            self.pause_token = str(value.get('token', ''))[:100]
            self.allowed.clear()
        elif command == 'resume':
            self.generation += 1
            self.allowed.set()
        elif command == 'shutdown':
            self.generation += 1
            self.shutdown.set()
            self.allowed.set()

    def _commands(self):
        for line in sys.stdin:
            if len(line) > 4096:
                continue
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict):
                self.command(value)
        self.command({'command': 'shutdown'})

    def _infer(self):
        while not self.shutdown.is_set():
            try:
                generation, raw = self.jobs.get(timeout=0.1)
            except queue.Empty:
                continue
            if generation != self.generation or not self.allowed.is_set():
                continue
            try:
                if self.provider == 'online':
                    from .transcription import transcribe_online
                    # Short wake phrases need at least one second for the service.
                    raw = raw + b'\0' * max(0, SAMPLE_RATE * 2 - len(raw))
                    text = transcribe_online(raw, self.language)[:4000]
                else:
                    audio = self.np.frombuffer(raw, dtype=self.np.int16).astype(self.np.float32) / 32768.0
                    segments, _ = self.model.transcribe(audio, language=None if self.language == 'auto' else self.language,
                                                        beam_size=1, vad_filter=True, task='transcribe', condition_on_previous_text=False,
                                                        initial_prompt='Tigo. ' + NAMES[1] + '.')
                    text = ' '.join(s.text.strip() for s in segments
                                    if getattr(s, 'no_speech_prob', 0) < 0.6 and getattr(s, 'avg_logprob', 0) > -1.0)[:4000]
                    del audio, segments
                now = time.monotonic()
                if (not self.shutdown.is_set() and generation == self.generation and self.allowed.is_set()
                        and now - self.last_wake >= COOLDOWN and contains_wake_name(text, self.fuzzy)):
                    self.last_wake = now
                    self.output('wake')
                # Do not send ordinary transcripts over IPC, print or retain them.
                del text, raw
            except UnrecognizedSpeech:
                continue  # Unintelligible speech is not a service outage.
            except Exception as exc:
                if self.shutdown.is_set() or generation != self.generation or not self.allowed.is_set():
                    continue
                self.failed = True
                self.output('error', message='Wake transcription failed: ' + str(exc)[:400])
                self.command({'command': 'shutdown'})

    def run(self):
        threading.Thread(target=self._commands, daemon=True).start()
        threading.Thread(target=self._infer, daemon=True).start()
        paused_token = None
        try:
            while not self.shutdown.is_set():
                if not self.allowed.is_set():
                    if paused_token != self.pause_token:
                        self.output('paused', token=self.pause_token)
                        paused_token = self.pause_token
                    self.allowed.wait(0.1)
                    continue
                paused_token = None
                frames = queue.Queue(maxsize=64)
                overflow = threading.Event()
                phrases = PhraseBuffer()
                generation = self.generation

                def callback(data, nframes, info, status):
                    if status:
                        overflow.set()
                        return
                    try:
                        frames.put_nowait(bytes(data))
                    except queue.Full:
                        overflow.set()

                device = int(self.microphone) if self.microphone.isdigit() else (self.microphone or None)
                with self.sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=1024,
                                            device=device, callback=callback):
                    self.output('listening')
                    while not self.shutdown.is_set() and self.allowed.is_set() and generation == self.generation:
                        if overflow.is_set():
                            raise RuntimeError('Microphone overflow. Choose a smaller model or another microphone.')
                        try:
                            raw = frames.get(timeout=0.1)
                        except queue.Empty:
                            continue
                        phrase = phrases.feed(raw)
                        if phrase:
                            try:
                                self.jobs.put_nowait((generation, phrase))
                            except queue.Full:
                                # Prefer fresh speech to an ever-growing inference backlog.
                                self.output('behind')
                                try:
                                    self.jobs.get_nowait()
                                except queue.Empty:
                                    pass
                                self.jobs.put_nowait((generation, phrase))
                # A paused acknowledgement is emitted only AFTER stream closure.
        except Exception as exc:
            self.failed = True
            self.output('error', message='Wake microphone unavailable: ' + str(exc)[:400])
        finally:
            self.command({'command': 'shutdown'})
        return 2 if self.failed else 0


_output_lock = threading.Lock()


def emit(kind, **values):
    with _output_lock:
        print(json.dumps({'type': kind, **values}), flush=True)


def main():
    parser = argparse.ArgumentParser(description='Local or explicit keyless online Tigo wake listener')
    parser.add_argument('--model', default='base')
    parser.add_argument('--language', default='auto')
    parser.add_argument('--microphone', default='')
    parser.add_argument('--exact', action='store_true')
    parser.add_argument('--provider', choices=('local','online'), default='local')
    args = parser.parse_args()
    if not valid_voice_model(args.model) or args.language not in dict(LANGUAGES) or len(args.microphone) > 200 or (args.provider == 'online' and args.language == 'auto'):
        emit('error', message='Choose a multilingual model, supported language and microphone.')
        return 2
    try:
        emit('loading')
        return WakeListener(args.model, args.language, args.microphone, not args.exact, provider=args.provider).run()
    except Exception as exc:
        emit('error', message='Wake model unavailable: ' + str(exc)[:400])
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
