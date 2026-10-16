"""Opt-in Microsoft speech: bounded network/audio work outside the GUI thread."""
import asyncio
import io
import json
import math
import sys

from .neural_worker import chunks
from .online_voices import VOICES

MAX_MP3_BYTES = 2_000_000
SAMPLE_RATE = 24000
MAX_SAMPLES = SAMPLE_RATE * 90


def phrases(text):
    """Keep short sentences/abbreviations together for continuous prosody."""
    pending = ''
    for part in chunks(text):
        if pending and len(pending) + len(part) + 1 > 240:
            yield pending
            pending = part
        else:
            pending = (pending + ' ' + part).strip()
    if pending:
        yield pending


async def synthesize(text, voice, speed=1., *, factory=None):
    """Only the chosen online mode calls this function; no disk audio cache."""
    if voice not in VOICES or not text or len(text) > 240 or not math.isfinite(speed):
        raise ValueError('Unsupported online voice or phrase.')
    if factory is None:
        from edge_tts import Communicate
        factory = Communicate
    rate = f'{round((max(.7, min(1.3, speed)) - 1) * 100):+d}%'
    audio = bytearray()
    async with asyncio.timeout(35):
        async for item in factory(text, voice, rate=rate).stream():
            if item['type'] != 'audio':
                continue
            audio.extend(item['data'])
            if len(audio) > MAX_MP3_BYTES:
                raise ValueError('The online audio exceeds its size limit.')
    if not audio:
        raise ValueError('The online service returned no audio.')
    return bytes(audio)


def decode_audio(raw):
    """Decode a bounded MP3 phrase to mono float PCM using the bundled decoder."""
    import av
    import numpy as np
    if not raw or len(raw) > MAX_MP3_BYTES:
        raise ValueError('Invalid online audio size.')
    parts, samples = [], 0
    with av.open(io.BytesIO(raw), format='mp3') as source:
        resampler = av.AudioResampler(format='flt', layout='mono', rate=SAMPLE_RATE)
        for frame in source.decode(audio=0):
            for converted in resampler.resample(frame):
                samples += converted.samples
                if samples > MAX_SAMPLES:
                    raise ValueError('The online audio exceeds its duration limit.')
                parts.append(converted.to_ndarray().reshape(-1))
        for converted in resampler.resample(None):
            samples += converted.samples
            if samples > MAX_SAMPLES:
                raise ValueError('The online audio exceeds its duration limit.')
            parts.append(converted.to_ndarray().reshape(-1))
    if not parts:
        raise ValueError('The online service returned empty audio.')
    pcm = np.concatenate(parts).astype(np.float32)
    if not np.isfinite(pcm).all():
        raise ValueError('The online service returned invalid audio.')
    return pcm


async def speak(text, voice, speed, volume, emit):
    """Prefetch one phrase while playing another, with a bounded queue."""
    import numpy as np
    import sounddevice as sd
    queue = asyncio.Queue(maxsize=1)

    async def produce():
        try:
            for part in phrases(text):
                encoded = await synthesize(part, voice, speed)
                await queue.put(await asyncio.to_thread(decode_audio, encoded))
        except Exception as exc:
            await queue.put(exc)
        else:
            await queue.put(None)

    producer = asyncio.create_task(produce())
    output = None
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
            if output is None:
                output = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32')
                output.start()
                emit('speaking')
            await asyncio.to_thread(output.write, np.clip(item * volume, -1, 1))
        if output is None:
            raise ValueError('No text to speak.')
        await asyncio.to_thread(output.stop)
    finally:
        producer.cancel()
        await asyncio.gather(producer, return_exceptions=True)
        if output is not None:
            output.close()


def main():
    for stream in (sys.stdin, sys.stdout):
        stream.reconfigure(encoding='utf-8')
    for line in sys.stdin:
        token = ''
        def emit(kind, **values):
            print(json.dumps({'type': kind, 'id': token, **values}), flush=True)
        try:
            if len(line) > 32000:
                raise ValueError('Oversized online speech request.')
            request = json.loads(line)
            token, voice = request['id'], request['voice']
            if voice not in VOICES:
                raise ValueError('Unknown online voice.')
            text = str(request['text'])[:6000]
            speed, volume = float(request['speed']), float(request['volume'])
            if not all(math.isfinite(x) for x in (speed, volume)):
                raise ValueError('Invalid online speech options.')
            volume = max(0, min(1, volume))
            emit('preparing', message='Generating online speech with Microsoft. Spoken text is sent to the service.')
            asyncio.run(speak(text, voice, speed, volume, emit))
            emit('done')
        except Exception as exc:
            emit('error', message='Online speech failed (' + type(exc).__name__ + '). '
                 'Check your Internet connection or select Local neural voices. No automatic retry or provider switch was performed.')


if __name__ == '__main__':
    main()
