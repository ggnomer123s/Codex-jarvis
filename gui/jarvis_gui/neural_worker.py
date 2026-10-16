"""Warm CPU TTS subprocess: bounded chunks, transient PCM and local playback."""
from collections import OrderedDict
import json
import re
import sys
from .speech_models import VOICES, ensure_voice


def chunks(text, limit=240):
    # Short first audio; do not wait for a complete long answer to synthesize.
    for sentence in re.split(r'(?<=[.!?\n])\s+', text.strip()):
        while len(sentence) > limit:
            end = sentence.rfind(' ', 0, limit+1)
            if end < limit//3:
                end = limit
            yield sentence[:end]
            sentence = sentence[end:].lstrip()
        if sentence:
            yield sentence


def load_voice(key, progress=lambda s: None):
    import sherpa_onnx
    path = ensure_voice(key, progress=progress)
    progress('Loading ' + VOICES[key]['name'] + ' on CPU.')
    config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(path/(key+'.onnx')), tokens=str(path/'tokens.txt'),
                data_dir=str(path/'espeak-ng-data')),
            num_threads=2, provider='cpu'),
        max_num_sentences=1)
    if not config.validate():
        raise ValueError('The neural voice configuration is invalid. Reinstall the voice model.')
    return sherpa_onnx.OfflineTts(config)


def main():
    for stream in (sys.stdin, sys.stdout):
        stream.reconfigure(encoding='utf-8')
    models = OrderedDict()
    def emit(kind, token, **values):
        print(json.dumps({'type': kind, 'id': token, **values}), flush=True)
    for line in sys.stdin:
        token = ''
        try:
            request = json.loads(line)
            token, key = request['id'], request['voice']
            if key not in VOICES:
                raise ValueError('Unknown neural voice.')
            text = str(request['text'])[:6000]
            speed = max(.7, min(1.4, float(request['speed'])))
            volume = max(0, min(1, float(request['volume'])))
            if key not in models:
                # Keep the two active language models warm, with bounded memory.
                if len(models) >= 2:
                    models.popitem(last=False)
                models[key] = load_voice(key, lambda s: emit('preparing', token, message=s))
            models.move_to_end(key)
            import numpy as np
            import sounddevice as sd
            model = models[key]
            output = None
            try:
                emit('preparing', token, message='Synthesizing the first phrase locally.')
                for part in chunks(text):
                    audio = model.generate(part, sid=0, speed=speed)
                    samples = np.asarray(audio.samples, dtype=np.float32)
                    if not samples.size:
                        continue
                    if output is None:
                        output = sd.OutputStream(samplerate=audio.sample_rate, channels=1, dtype='float32')
                        output.start()
                        emit('speaking', token)
                    output.write(np.clip(samples * volume, -1, 1))
                if output is None:
                    raise ValueError('The neural model did not produce audio.')
                output.stop()  # Drain the device before releasing microphone ownership.
            finally:
                if output is not None:
                    output.close()
            emit('done', token)
        except Exception as exc:
            # Missing dependencies/download/device failures leave text chat usable.
            emit('error', token, message=type(exc).__name__ + ': ' + str(exc)[:500])


if __name__ == '__main__':
    main()
