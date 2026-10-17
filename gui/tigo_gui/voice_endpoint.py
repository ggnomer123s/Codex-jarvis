"""Local speech-end detection on bounded 20 ms mono PCM frames."""
from __future__ import annotations


class SpeechEndpoint:
    RATE = 16000
    FRAME_BYTES = 640
    FRAME_MS = 20

    def __init__(self, silence_ms=1600, *, classifier=None):
        if type(silence_ms) is not int or not 800 <= silence_ms <= 4000:
            raise ValueError('Speech pause must be between 800 and 4000 milliseconds.')
        if classifier is None:
            import webrtcvad
            classifier = webrtcvad.Vad(2).is_speech
        self.classify = classifier
        self.silence_ms = silence_ms
        self.pending = bytearray()
        self.elapsed = self.voiced = self.quiet = 0
        self.started = False
        self.reason = ''

    def feed(self, raw):
        if self.reason:
            return self.reason
        self.pending.extend(raw)
        offset = 0
        while len(self.pending) - offset >= self.FRAME_BYTES:
            frame = bytes(self.pending[offset:offset + self.FRAME_BYTES])
            offset += self.FRAME_BYTES
            speech = self.classify(frame, self.RATE)
            self.elapsed += self.FRAME_MS
            if speech:
                self.voiced += self.FRAME_MS
                self.quiet = 0
                if self.voiced >= 240:
                    self.started = True
            else:
                self.quiet += self.FRAME_MS
                # Isolated noise pulses do not accumulate into a command.
                if not self.started and self.quiet >= 300:
                    self.voiced = 0
            if self.started and self.quiet >= self.silence_ms:
                self.reason = 'silence'
                break
            if not self.started and self.elapsed >= 8000:
                self.reason = 'no_speech'
                break
        del self.pending[:offset]
        return self.reason
