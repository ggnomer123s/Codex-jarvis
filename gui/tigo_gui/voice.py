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
from .live_text import LiveTranscript

MAX_SECONDS = 60
SAMPLE_RATE = 16000
OUTPUT_LOCK = threading.Lock()


class VoiceWorker:
    """One explicit provider, many recordings; bounded audio/preview queues."""

    def __init__(self, model_name, device="cpu", *, model_factory=None, output=None, provider="local"):
        # Imports are local so text-only installations can still load the UI.
        import numpy as np
        import sounddevice as sd
        self.provider = provider
        self.model_name, self._model_factory = model_name, model_factory
        self._used_fallback = False
        if provider == "local" and model_factory is None:
            from faster_whisper import WhisperModel
            model_factory = WhisperModel
        self.np, self.sd = np, sd
        self.output = output or emit
        started = time.monotonic()
        self.model = (model_factory(model_name, device=device,
                                   compute_type="int8" if device == "cpu" else "int8_float16")
                      if provider == "local" else None)
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
            auto_stop, silence_ms = value.get("auto_stop", False), value.get("silence_ms", 1600)
            if type(value.get('local_fallback', True)) is not bool:
                self.output('error', id=recording_id, message='Invalid local fallback option.')
                self.output('idle', id=recording_id)
                return True
            if not isinstance(recording_id, str) or not recording_id or len(recording_id) > 128 or language not in dict(LANGUAGES) or type(beam) is not int or beam not in (1, 3, 5) or type(auto_stop) is not bool or type(silence_ms) is not int or not 800 <= silence_ms <= 4000:
                self.output("error", id=recording_id, message="Invalid recording options.")
                self.output("idle", id=recording_id)
                return True
            self.recording_id = recording_id
            self.stop.clear()
            self.cancelled.clear()
            self.thread = threading.Thread(target=self._record, args=({**value, "language": language, "beam": beam},), daemon=True)
            self.thread.start()
        return True

    def _transcribe(self, raw, language, beam, *, allow_fallback=True):
        if self.provider == "online":
            try:
                from .transcription import transcribe_online
                return transcribe_online(raw, language)
            except (RuntimeError, ValueError, ImportError):
                if not allow_fallback or self.cancelled.is_set():
                    raise
                self._used_fallback = True
                self.output('fallback', id=self.recording_id,
                            message='Online speech failed; recognizing the same recording locally. First use may download Whisper.')
        audio = self.np.frombuffer(raw, dtype=self.np.int16).astype(self.np.float32) / 32768.0
        with self._model_lock:
            if self.model is None:
                factory = self._model_factory
                if factory is None:
                    from faster_whisper import WhisperModel
                    factory = WhisperModel
                # CPU fallback works even when no CUDA runtime is installed.
                self.model = factory(self.model_name, device='cpu', compute_type='int8')
            if self.cancelled.is_set():
                return ''
            segments, _ = self.model.transcribe(audio, beam_size=beam, vad_filter=True,
                                                task="transcribe", language=None if language == "auto" else language,
                                                condition_on_previous_text=False)
            return " ".join(segment.text.strip() for segment in segments).strip()

    def _record(self, options):
        recording_id = options["id"]
        self._used_fallback = False
        frames = queue.Queue(maxsize=64)
        overflow = threading.Event()
        buffers = []
        count = 0
        started = time.monotonic()
        endpoint = None
        end_reason = "manual"
        # Preview only processes newly captured chunks, never a growing full buffer.
        previews = queue.Queue(maxsize=1)
        preview_done = threading.Event()
        live = LiveTranscript()

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
                    window, raw = previews.get(timeout=.1)
                except queue.Empty:
                    continue
                if self.cancelled.is_set() or preview_done.is_set():
                    return
                try:
                    text = self._transcribe(raw, options["language"], 1, allow_fallback=False)
                    if text and not self.cancelled.is_set() and not preview_done.is_set():
                        self.output("preview", id=recording_id, text=live.update(window, text))
                except Exception:
                    # Preview is optional; the final transcription reports errors.
                    pass

        preview_thread = None
        if options.get("preview"):
            preview_thread = threading.Thread(target=preview_worker, daemon=True)
            preview_thread.start()
        preview_raw = bytearray()
        preview_window = 0
        preview_samples = 0
        last_preview = time.monotonic()
        last_speech = time.monotonic()
        try:
            if options.get("auto_stop"):
                from .voice_endpoint import SpeechEndpoint
                endpoint = SpeechEndpoint(options.get("silence_ms", 1600))
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
                        if endpoint and not endpoint.started and time.monotonic() - started >= 8:
                            end_reason = "no_speech"
                            break
                        if time.monotonic() - started >= MAX_SECONDS:
                            break
                        continue
                    raw = raw[:(SAMPLE_RATE * MAX_SECONDS - count) * 2]
                    if not raw:
                        continue
                    buffers.append(raw)
                    count += len(raw) // 2
                    if endpoint:
                        reason = endpoint.feed(raw)
                        if reason:
                            end_reason = reason
                            self.output("speech_end", id=recording_id, reason=reason)
                            break
                    samples = self.np.frombuffer(raw, dtype=self.np.int16).astype(self.np.float32) / 32768.0
                    level = min(1.0, float(self.np.sqrt(self.np.mean(samples * samples))) * 8)
                    self.output("level", id=recording_id, value=level)
                    now = time.monotonic()
                    if level > .08:
                        last_speech = now
                    if preview_thread:
                        preview_raw.extend(raw)
                        preview_samples += len(raw) // 2
                        # Re-decode the current bounded window to revise partial words.
                        # Online is keyless phrase HTTP, not a persistent streaming API.
                        if preview_samples >= SAMPLE_RATE * 1.2:
                            try:
                                previews.put_nowait((preview_window, bytes(preview_raw)))
                                preview_samples = 0
                                last_preview = now
                                if len(preview_raw) >= SAMPLE_RATE * 8 * 2:
                                    preview_raw = bytearray(preview_raw[-SAMPLE_RATE * 2:])
                                    preview_window += 1
                            except queue.Full:
                                # Keep one fresh bounded window while inference is busy.
                                if len(preview_raw) > SAMPLE_RATE * 10 * 2:
                                    preview_raw = bytearray(preview_raw[-SAMPLE_RATE * 8 * 2:])
                                    preview_window += 1
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
            if end_reason == "no_speech":
                raise RuntimeError("No speech detected within eight seconds. Recording cancelled without sending a request.")
            if count >= SAMPLE_RATE * MAX_SECONDS:
                end_reason = "limit"
            if count < SAMPLE_RATE:
                raise RuntimeError("Recording too short. Speak for at least one second.")
            capture_ms = round((time.monotonic() - started) * 1000, 1)
            self.output("transcribing", id=recording_id)
            transcribe_started = time.monotonic()
            text = self._transcribe(b"".join(buffers), options["language"], options.get("beam", 3),
                                    allow_fallback=options.get('local_fallback', True))
            if self.cancelled.is_set():
                return
            if not text:
                raise RuntimeError("No speech detected. Try again closer to the microphone.")
            self.output("transcript", id=recording_id, text=text, endReason=end_reason, fallback=self._used_fallback,
                        timings={"captureMs": capture_ms, "transcribeMs": round((time.monotonic() - transcribe_started) * 1000, 1)})
        except Exception as exc:
            if not self.cancelled.is_set():
                self.output("error", id=recording_id, message=f"Voice unavailable: {exc}")
        finally:
            preview_done.set()
            buffers.clear()
            preview_raw.clear()
            self.output("idle", id=recording_id)


def worker_main(model, device, provider="local"):
    try:
        worker = VoiceWorker(model, device, provider=provider)
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
        emit("error", message=f"Transcription unavailable: {exc}")
        return 2


def emit(kind: str, **fields):
    with OUTPUT_LOCK:
        print(json.dumps({"type": kind, **fields}), flush=True)


def dependencies_available(provider="local") -> bool:
    names = ("numpy", "sounddevice", "webrtcvad", "faster_whisper") if provider == "local" else ("numpy", "sounddevice", "webrtcvad", "speech_recognition")
    return all(importlib.util.find_spec(name) is not None for name in names)


def main(argv=()) -> int:
    parser = argparse.ArgumentParser(description="Local or explicit keyless online Tigo dictation worker")
    from .compat import environment
    parser.add_argument("--language", default=environment("VOICE_LANGUAGE") or "auto")
    parser.add_argument("--model", default=environment("VOICE_MODEL", "base"))
    parser.add_argument("--worker", action="store_true", help="Keep the model loaded; accept JSON recording commands")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--provider", choices=("local", "online"), default="local")
    options = parser.parse_args(argv)
    if options.language not in dict(LANGUAGES) or not valid_voice_model(options.model):
        emit("error", message="Choose Auto detect or a supported language, and a multilingual Whisper model or local model folder.")
        return 2
    if not (dependencies_available() if options.provider == "local" else dependencies_available("online")):
        emit("error", message="Voice packages are missing. Launch with the voice extra; see docs/desktop-app.md.")
        return 2
    if options.worker:
        return worker_main(options.model, options.device, options.provider)
    if options.provider != "local":
        emit("error", message="Online dictation uses the desktop worker; start Tigo GUI and select Online in Voice settings.")
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
