# JARVIS character and local neural speech

Updating the GUI installer refreshes `jarvis-desktop/SKILL.md` and the managed
Codex `AGENTS.md` block, preserving personal instructions. Start a new
conversation to load them. JARVIS treats the user as mentor: calm, respectful,
concise and occasionally dryly witty, using the user's language.

## New default in 0.7.0

Spoken answers now use **Piper/VITS neural voices through sherpa-onnx on CPU**,
rather than Windows SAPI or Linux eSpeak speech output.

| Voice | Language | Selection |
| --- | --- | --- |
| Dmitri Neural | Russian | Automatic for Russian text |
| Denis Neural | Russian | Alternate in Preferences > Speech |
| Joe Neural | English | Automatic for English text |

These trained voices preserve natural pitch; no actor clone is included.
Automatic selects one language for the whole reply; mixed-language pronunciation
depends on that voice. Other languages can use explicitly selected installed
voices in **System voices (legacy)** mode. Multilingual Whisper transcription
remains a separate feature.

On the first update to 0.7.0, old system voice IDs and rate/pitch settings reset
to Automatic and neutral rate/pitch. Saved Speech off and volume are preserved.
After migration, selected mode, voice and sliders persist.

## Installation and downloads

Ordinary GUI installers and launchers install the locked `voice` extra, including
sherpa-onnx, its native core, sounddevice, NumPy and filelock. Windows needs no
Russian language pack, speech component or separate TTS UAC prompt. Linux uses
PortAudio for playback; distro dependency recipes include it. CPU inference
needs no GPU, API key, account or Torch installation.

The dependency-aware CachyOS/Windows updaters preload Dmitri and Joe. Ordinary
GUI installation downloads a chosen model on first speech use, showing progress
in Preferences > Speech. Each archive is about **67 MB**, unpacking to about
**81 MB**. Denis downloads only when selected. Downloads use the official
k2-fsa/sherpa-onnx GitHub release, checking pinned size and SHA-256 before bounded
extraction. Interrupted or invalid downloads are replaced on the next attempt.
Cached voices need no network for subsequent synthesis.

- Linux cache: `${XDG_CACHE_HOME:-~/.cache}/jarvis/voices`.
- Windows cache: `%LOCALAPPDATA%\jarvis\voices`.

To download default voices from a prepared checkout, in Bash or PowerShell:

```bash
uv run --project gui --frozen --extra voice python -m jarvis_gui.speech_models
```

Append a model ID, such as `ru_RU-denis-medium`, to download only that voice.
With JARVIS closed, removing a voice cache directory forces a new verified
download. Model cards remain alongside weights. See [voice notices](voice-notices.md).

## Controls

- **Speech on/off** saves automatic reading; default is on.
- **Read** on an assistant message also works when automatic reading is off.
- **Stop speech**, a new request, recording or app shutdown interrupts speech.
  Escape stops output when no task or recording has priority.
- **Preferences > Speech** selects **Neural (recommended)** or explicit legacy
  system output, an available voice, rate and volume. Neural mode preserves
  natural pitch; the pitch slider applies only to system voices.
- **Test voice** applies displayed settings and speaks a sample. Save keeps
  changes; the automatic checkbox and engine selection apply immediately.
  **Refresh voices** recreates an idle engine and refreshes its catalog.

Automatic speech reads only the current successful completed final answer.
Streamed fragments, commentary, errors, canceled turns and restored history stay
silent. Code fences, images, raw URLs and Markdown are removed from the spoken
copy, limited to 6,000 characters. Chat text stays unchanged.

## Responsiveness, microphone and privacy

Downloads, loading, inference and playback run in an owned subprocess. The GUI
stays responsive. Speech starts after the first bounded phrase synthesizes,
without waiting for the entire answer. At most two successfully used models
remain warm. Stop kills an active worker, so the next reply reloads from disk;
successful completion keeps it warm. PCM stays in memory. No reply text is sent
to a TTS service and speech recordings are not saved.

Wake capture must acknowledge pause or exit before playback starts. It stays
paused through output and a 300 ms quiet tail. Recording interrupts output and
waits for the worker to stop before opening the mic. Late callbacks cannot start
canceled speech/recording. This is coordinated turn-taking, not full-duplex echo
cancellation. Model requests still use Codex as before.

Missing dependencies, unavailable speakers, download/checksum failures and
worker errors appear in chat/settings without resending the Codex task.
First-use preparation has a two-minute inactivity deadline, refreshed by
progress; an utterance has a ten-minute overall bound. Check audio output,
volume and initial-download network access. Speech errors leave text chat usable.
Legacy system mode needs an installed Windows speech voice or Linux Speech
Dispatcher/eSpeak NG and libpulse. No mock engine is a production fallback.

The user requested no further test runs and will check sound on their machines.
Earlier local CPU synthesis and process/QML checks preceded that instruction;
Windows hardware and audible quality have not been checked in this cloud.
See [changes.md](../changes.md) for the recorded scope.
