"""Bounded provisional transcription and sentence-level speech assembly."""
import re
from .speech_text import spoken_text


def join_overlap(left, right):
    a, b = left.split(), right.split()
    norm = lambda words: [word.casefold().strip('.,!?;:') for word in words]
    for size in range(min(32, len(a), len(b)), 0, -1):
        if norm(a[-size:]) == norm(b[:size]):
            return ' '.join(a + b[size:])
    return ' '.join(a + b)


class LiveTranscript:
    def __init__(self):
        self.window = None
        self.stable = self.partial = ''

    def update(self, window, text):
        if self.window != window:
            self.stable = join_overlap(self.stable, self.partial)
            self.window = window
        self.partial = text
        return join_overlap(self.stable, text)[-60000:]


class SpeechSentences:
    def __init__(self):
        self.buffer = ''
        self.fence = ''

    def feed(self, text, final=False):
        self.buffer += text
        result = []
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            self._line(line, result)
        if final:
            self._line(self.buffer, result)
            self.buffer = ''
        elif not self.fence and not re.match(r'^\s*[`~]', self.buffer):
            # Wait for balanced inline markup before exposing a partial URL/code.
            if self.buffer.count('`') % 2 == 0 and self.buffer.count('[') == self.buffer.count(']') and self.buffer.count('(') == self.buffer.count(')'):
                ends = list(re.finditer(r'[.!?\u2026][\"\u00bb\u201d]*\s+', self.buffer))
                if ends:
                    cut = ends[-1].end()
                    self._line(self.buffer[:cut], result)
                    self.buffer = self.buffer[cut:]
        return result

    def _line(self, line, result):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            if not self.fence:
                self.fence = marker[1]
            elif marker[1][0] == self.fence[0] and len(marker[1]) >= len(self.fence):
                self.fence = ''
        elif not self.fence:
            clean = spoken_text(line)
            if clean:
                result.append(clean)
