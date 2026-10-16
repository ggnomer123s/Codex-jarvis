#!/usr/bin/env python3
"""Check real pinned models and CPU synthesis without speakers or a microphone."""
import json
import time
import numpy as np
from tigo_gui.neural_worker import chunks, load_voice
from tigo_gui.speech_models import DEFAULTS


def main():
    for key in DEFAULTS:
        start = time.monotonic()
        model = load_voice(key, lambda message: print(message, flush=True))
        load_time = time.monotonic()-start
        # Escapes keep managed scripts English-only; synthesis still checks Russian.
        text = ('\u041a \u0432\u0430\u0448\u0438\u043c \u0443\u0441\u043b\u0443\u0433\u0430\u043c, \u043d\u0430\u0441\u0442\u0430\u0432\u043d\u0438\u043a. \u0421\u0438\u0441\u0442\u0435\u043c\u044b \u0433\u043e\u0442\u043e\u0432\u044b.'
                if key.startswith('ru') else 'At your service, mentor. All systems are ready.')
        for mode in ('first', 'warm'):
            start = time.monotonic()
            duration, peak = 0, 0
            for part in chunks(text):
                audio = model.generate(part, sid=0, speed=1.)
                samples = np.asarray(audio.samples)
                assert audio.sample_rate == 22050, audio.sample_rate
                assert samples.size and np.isfinite(samples).all(), 'Empty or invalid neural audio'
                duration += samples.size/audio.sample_rate
                peak = max(peak, float(np.max(np.abs(samples))))
            assert 1 < duration < 30 and peak > .01, (duration, peak)
            print(json.dumps(dict(voice=key, mode=mode, load_seconds=round(load_time, 3),
                                  synthesis_seconds=round(time.monotonic()-start, 3),
                                  audio_seconds=round(duration, 3), peak=round(peak, 3))), flush=True)
        del model
    print('Real Russian/English CPU synthesis passed. Physical playback was not exercised.')


if __name__ == '__main__':
    main()
