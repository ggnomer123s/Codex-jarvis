"""Isolated microphone/transcription worker; JSON stdout, commands on stdin.

Audio remains in memory. The GUI can stop this process during recording,
model downloads or transcription without freezing the window.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import threading

MAX_SECONDS = 60
SAMPLE_RATE = 16000
OUTPUT_LOCK = threading.Lock()


def emit(kind: str, **fields):
    with OUTPUT_LOCK:
        print(json.dumps({"type": kind, **fields}), flush=True)


def dependencies_available() -> bool:
    return all(importlib.util.find_spec(name) is not None
               for name in ("numpy", "sounddevice", "faster_whisper"))


def main() -> int:
    if not dependencies_available():
        emit("error", message="Voice packages are missing. Launch with the voice extra; see docs/desktop-app.md.")
        return 2
    stop = threading.Event()
    cancelled = threading.Event()

    def commands():
        for line in sys.stdin:
            if line.strip() == "cancel":
                cancelled.set()
            if line.strip() in ("stop", "cancel"):
                stop.set()
                return
        cancelled.set()
        stop.set()

    threading.Thread(target=commands, daemon=True).start()
    try:
        import numpy as np
        import sounddevice as sd

        buffers = []
        count = 0

        def callback(indata, frames, time_info, status):
            nonlocal count
            if count >= SAMPLE_RATE * MAX_SECONDS:
                stop.set()
                return
            raw = bytes(indata)[:(SAMPLE_RATE * MAX_SECONDS - count) * 2]
            buffers.append(raw)
            count += len(raw) // 2
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            level = min(1.0, float(np.sqrt(np.mean(samples * samples))) * 8)
            emit("level", value=level)
            if count >= SAMPLE_RATE * MAX_SECONDS:
                stop.set()

        with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                               blocksize=1024, callback=callback):
            emit("recording")
            stop.wait(MAX_SECONDS)
        if cancelled.is_set():
            return 0
        if count < SAMPLE_RATE:
            emit("error", message="Recording too short. Speak for at least one second.")
            return 1
        audio = np.frombuffer(b"".join(buffers), dtype=np.int16).astype(np.float32) / 32768.0
        buffers.clear()
        emit("transcribing")
        from faster_whisper import WhisperModel
        # Cached by faster-whisper; first use downloads the multilingual model.
        model = WhisperModel(os.environ.get("JARVIS_VOICE_MODEL", "base"),
                             device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio, beam_size=3, vad_filter=True,
                                       language=os.environ.get("JARVIS_VOICE_LANGUAGE") or None,
                                       condition_on_previous_text=False)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        if text:
            emit("transcript", text=text)
            return 0
        emit("error", message="No speech detected. Try again closer to the microphone.")
        return 1
    except Exception as exc:
        emit("error", message=f"Voice unavailable: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
