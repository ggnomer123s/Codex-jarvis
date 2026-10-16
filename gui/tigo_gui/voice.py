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
import argparse
import queue
import time
from .preferences import LANGUAGES, valid_voice_model

MAX_SECONDS = 60
SAMPLE_RATE = 16000
OUTPUT_LOCK = threading.Lock()


class VoiceWorker:
    """One multilingual model, many recordings; bounded audio/preview queues."""

    def __init__(self, model_name, device="cpu", *, model_factory=None, output=None):
        # Imports are local so text-only installations can still load the UI.
        import numpy as np
        import sounddevice as sd
        if model_factory is None:
            from faster_whisper import WhisperModel
            model_factory = WhisperModel
        self.np, self.sd = np, sd
        self.output = output or emit
        started = time.monotonic()
        self.model = model_factory(model_name, device=device,
                                   compute_type="int8" if device == "cpu" else "int8_float16")
        self.load_ms = round((time.monotonic() - started) * 1000, 1)
        self._model_lock = threading.Lock()
        self.stop = threading.Event()
        self.cancelled = threading.Event()
        self.thread = None
        self.recording_id = ""

    def devices(self):
        try:
            return [{"id": str(i), "label": str(item["name"])[:160]}
                    for i, item in enumerate(self.sd.query_devices()) if item.get("max_input_channels", 0) > 0][:100]
        except Exception:
            return []

    def command(self, value):
        command, recording_id = value.get("command"), value.get("id", "")
        if command == "shutdown":
            self.cancelled.set()
            self.stop.set()
            return False
        if command in ("stop", "cancel"):
            if recording_id == self.recording_id:
                if command == "cancel":
                    self.cancelled.set()
                self.stop.set()
        elif command == "record":
            if self.thread and self.thread.is_alive():
                self.output("error", id=recording_id, message="A recording is already active.")
                self.output("idle", id=recording_id)
                return True
            language = value.get("language", "auto")
            beam = value.get("beam", 3)
            if not isinstance(recording_id, str) or not recording_id or len(recording_id) > 128 or language not in dict(LANGUAGES) or type(beam) is not int or beam not in (1, 3, 5):
                self.output("error", id=recording_id, message="Invalid recording options.")
                self.output("idle", id=recording_id)
                return True
            self.recording_id = recording_id
            self.stop.clear()
            self.cancelled.clear()
            self.thread = threading.Thread(target=self._record, args=({**value, "language": language, "beam": beam},), daemon=True)
            self.thread.start()
        return True

    def _transcribe(self, raw, language, beam):
        audio = self.np.frombuffer(raw, dtype=self.np.int16).astype(self.np.float32) / 32768.0
        with self._model_lock:
            segments, _ = self.model.transcribe(audio, beam_size=beam, vad_filter=True,
                                                task="transcribe", language=None if language == "auto" else language,
                                                condition_on_previous_text=False)
            return " ".join(segment.text.strip() for segment in segments).strip()

    def _record(self, options):
        recording_id = options["id"]
        frames = queue.Queue(maxsize=64)
        overflow = threading.Event()
        buffers = []
        count = 0
        started = time.monotonic()
        # Preview only processes newly captured chunks, never a growing full buffer.
        previews = queue.Queue(maxsize=1)
        preview_done = threading.Event()
        preview_text = []

        def callback(indata, nframes, time_info, status):
            # The realtime callback does not run numpy, JSON or model inference.
            if status:
                overflow.set()
                return
            try:
                frames.put_nowait(bytes(indata))
            except queue.Full:
                overflow.set()

        def preview_worker():
            while not preview_done.is_set():
                try:
                    raw = previews.get(timeout=.1)
                except queue.Empty:
                    continue
                if self.cancelled.is_set() or preview_done.is_set():
                    return
                try:
                    text = self._transcribe(raw, options["language"], 1)
                    if text and not self.cancelled.is_set() and not preview_done.is_set():
                        preview_text.append(text)
                        self.output("preview", id=recording_id, text=" ".join(preview_text))
                except Exception:
                    # Preview is optional; the final transcription reports errors.
                    pass

        preview_thread = None
        if options.get("preview"):
            preview_thread = threading.Thread(target=preview_worker, daemon=True)
            preview_thread.start()
        preview_raw = bytearray()
        last_preview = time.monotonic()
        last_speech = time.monotonic()
        try:
            mic = options.get("microphone", "")
            device = int(mic) if mic and str(mic).isdigit() else (mic or None)
            with self.sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=1024,
                                        device=device, callback=callback):
                self.output("recording", id=recording_id)
                while not self.stop.is_set() and count < SAMPLE_RATE * MAX_SECONDS:
                    if overflow.is_set():
                        raise RuntimeError("Audio input overflowed. Retry with preview disabled or a smaller model.")
                    try:
                        raw = frames.get(timeout=.05)
                    except queue.Empty:
                        if time.monotonic() - started >= MAX_SECONDS:
                            break
                        continue
                    raw = raw[:(SAMPLE_RATE * MAX_SECONDS - count) * 2]
                    buffers.append(raw)
                    count += len(raw) // 2
                    samples = self.np.frombuffer(raw, dtype=self.np.int16).astype(self.np.float32) / 32768.0
                    level = min(1.0, float(self.np.sqrt(self.np.mean(samples * samples))) * 8)
                    self.output("level", id=recording_id, value=level)
                    now = time.monotonic()
                    if level > .08:
                        last_speech = now
                    if preview_thread:
                        preview_raw.extend(raw)
                        if now - last_preview >= 8 or (now - last_preview >= 2 and now - last_speech >= .7):
                            try:
                                previews.put_nowait(bytes(preview_raw))
                                preview_raw.clear()
                                last_preview = now
                            except queue.Full:
                                pass
            # Include frames queued just before the user's stop request.
            if overflow.is_set():
                raise RuntimeError("Audio input overflowed. Retry with preview disabled or a smaller model.")
            while not frames.empty() and count < SAMPLE_RATE * MAX_SECONDS:
                raw = frames.get_nowait()[:(SAMPLE_RATE * MAX_SECONDS - count) * 2]
                buffers.append(raw)
                count += len(raw) // 2
            preview_done.set()
            if self.cancelled.is_set():
                return
            if count < SAMPLE_RATE:
                raise RuntimeError("Recording too short. Speak for at least one second.")
            capture_ms = round((time.monotonic() - started) * 1000, 1)
            self.output("transcribing", id=recording_id)
            transcribe_started = time.monotonic()
            text = self._transcribe(b"".join(buffers), options["language"], options.get("beam", 3))
            if self.cancelled.is_set():
                return
            if not text:
                raise RuntimeError("No speech detected. Try again closer to the microphone.")
            self.output("transcript", id=recording_id, text=text,
                        timings={"captureMs": capture_ms, "transcribeMs": round((time.monotonic() - transcribe_started) * 1000, 1)})
        except Exception as exc:
            if not self.cancelled.is_set():
                self.output("error", id=recording_id, message=f"Voice unavailable: {exc}")
        finally:
            preview_done.set()
            buffers.clear()
            preview_raw.clear()
            self.output("idle", id=recording_id)


def worker_main(model, device):
    try:
        worker = VoiceWorker(model, device)
        emit("ready", modelLoadMs=worker.load_ms, microphones=worker.devices())
        for line in sys.stdin:
            if len(line) > 10000:
                continue
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and not worker.command(value):
                break
        worker.command({"command": "shutdown"})
        return 0
    except Exception as exc:
        emit("error", message=f"Local model unavailable: {exc}")
        return 2


def emit(kind: str, **fields):
    with OUTPUT_LOCK:
        print(json.dumps({"type": kind, **fields}), flush=True)


def dependencies_available() -> bool:
    return all(importlib.util.find_spec(name) is not None
               for name in ("numpy", "sounddevice", "faster_whisper"))


def main(argv=()) -> int:
    parser = argparse.ArgumentParser(description="Local multilingual Tigo voice worker")
    from .compat import environment
    parser.add_argument("--language", default=environment("VOICE_LANGUAGE") or "auto")
    parser.add_argument("--model", default=environment("VOICE_MODEL", "base"))
    parser.add_argument("--worker", action="store_true", help="Keep the model loaded; accept JSON recording commands")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    options = parser.parse_args(argv)
    if options.language not in dict(LANGUAGES) or not valid_voice_model(options.model):
        emit("error", message="Choose Auto detect or a supported language, and a multilingual Whisper model or local model folder.")
        return 2
    if not dependencies_available():
        emit("error", message="Voice packages are missing. Launch with the voice extra; see docs/desktop-app.md.")
        return 2
    if options.worker:
        return worker_main(options.model, options.device)
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
        model = WhisperModel(options.model,
                             device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio, beam_size=3, vad_filter=True,
                                       task="transcribe",
                                       language=None if options.language == "auto" else options.language,
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
    raise SystemExit(main(sys.argv[1:]))
