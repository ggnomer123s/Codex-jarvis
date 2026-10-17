"""Bounded provisional transcription with overlapping recognition windows."""


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
