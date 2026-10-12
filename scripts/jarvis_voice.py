#!/usr/bin/env python3
"""Push-to-talk local speech-to-text for the JARVIS CLI.

Audio samples live only in RAM, Whisper runs locally, stdout holds ONLY transcript.
First run downloads an open multilingual Whisper model into the user's model cache.
"""
from __future__ import annotations

import os
import sys


def main():
    try:
        import numpy as np
        import sounddevice as sd
    except Exception as exc:
        print(f"Audio dependency error: {exc}", file=sys.stderr)
        print("Install PortAudio (e.g. libportaudio2, portaudio) and check microphone access.", file=sys.stderr)
        return 2

    model_name = os.environ.get("JARVIS_VOICE_MODEL", "base")
    language = os.environ.get("JARVIS_VOICE_LANGUAGE") or None
    sample_rate = 16000
    buffers: list[bytes] = []

    def callback(indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        buffers.append(bytes(indata))

    try:
        print("JARVIS local push-to-talk (no background listening).", file=sys.stderr)
        input("Press Enter to START microphone recording... ")
        print("Recording. Press Enter to STOP.", file=sys.stderr)
        with sd.RawInputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocksize=2048,
            callback=callback,
        ):
            input()
    except (EOFError, KeyboardInterrupt):
        print("\nRecording cancelled.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Microphone error: {exc}", file=sys.stderr)
        return 2

    raw = b"".join(buffers)
    if len(raw) < sample_rate * 2:  # fewer than 1 second of mono int16 samples
        print("Recording too short.", file=sys.stderr)
        return 1
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    del buffers
    del raw

    print(f"Transcribing locally with multilingual Whisper model '{model_name}'...", file=sys.stderr)
    print("The first run may download model files; later runs use the cache.", file=sys.stderr)
    try:
        from faster_whisper import WhisperModel
        engine = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, info = engine.transcribe(
            audio,
            beam_size=3,
            vad_filter=True,
            language=language,
            condition_on_previous_text=False,
        )
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as exc:
        print(f"Transcription failed: {exc}", file=sys.stderr)
        return 2

    if not transcript:
        print("No speech detected. Nothing will be sent to Codex.", file=sys.stderr)
        return 1
    # stdout is captured by the launcher; it displays text for confirmation.
    print(transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
