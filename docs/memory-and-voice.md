# JARVIS Memory and voice input

Two opt-in features that work across **Linux desktop environments and Windows 11** without requiring new GUI-MCP permissions.

## Memory: locally saved, user-confirmed fixes

Memory is a JSON database, **not a ChatGPT/Codex account memory**. It stores only repairs the user explicitly records. JARVIS can consult those notes during later troubleshooting, but they are **historical information**, not commands, and may be outdated.

| Command | Action |
|---|---|
| `jarvis memory add` | Interactively record an already-verified repair |
| `jarvis memory list` | Display confirmed fixes |
| `jarvis memory search dolphin` | Find relevant history |
| `jarvis memory forget <id>` | Delete one entry after confirming DELETE |

Example:

~~~text
$ jarvis memory add
Problem/symptom: Dolphin opens slowly after login
Verified solution: Corrected an invalid user configuration file, then confirmed restart was successful
OS/app/version context (optional): KDE on X11
Review before saving: ...
Save this verified fix locally? Type YES: YES
Saved locally with ID a1b2c3d4e5f6
~~~

This is illustrative, **not** a diagnosis of your computer.

Data locations:
- Linux: `~/.local/share/jarvis-codex/memory/confirmed-fixes.json`
- Windows: `%LOCALAPPDATA%\jarvis-codex\memory\confirmed-fixes.json`

The CLI uses a per-user directory (mode 0700 on Unix) and writes JSON atomically with 0600 permissions on Unix. Windows uses normal user-profile NTFS access controls. No synchronization, remote storage or automatic upload is configured. No unattended recording of screenshots, logs, voice, or conversations.

To erase every saved fix, close Codex and delete the local `confirmed-fixes.json` file. The file is not stored in GitHub.

A note is saved only after you type `YES`; deleting one requires `DELETE`. Historic notes are user-authored and may become outdated, so JARVIS should verify every proposed repair.

**Privacy:** Never save credentials, API tokens, SSH keys, private screenshots or raw logs. Codex may read notes during troubleshooting, which can expose note contents to the Codex model provider.

## Voice: opt-in local push-to-talk

~~~sh
jarvis voice
~~~

1. The launcher starts a local recorder, but **nothing is recorded until you press Enter**.
2. Press Enter to start; speak in Russian or English; press Enter again to stop.
3. [faster-whisper](https://github.com/SYSTRAN/faster-whisper) transcribes audio **locally** on CPU using INT8 inference.
4. Review the recognized text. Typing `YES` opens Codex with the dictated request. Other answers cancel.

**Audio is not uploaded to Codex.** The text you approve **is** sent to Codex. Audio samples are held in RAM, and no WAV recording is saved. First run downloads Python dependencies and a multilingual Whisper model; subsequently cached files can run without network access.

Default model: multilingual **base**. For better (but heavier) recognition:

Fish:

~~~fish
set -x JARVIS_VOICE_MODEL small
jarvis voice
~~~

Bash/Zsh:

~~~bash
JARVIS_VOICE_MODEL=small jarvis voice
~~~

PowerShell:

~~~powershell
$env:JARVIS_VOICE_MODEL = 'small'
jarvis voice
~~~

For Russian speech, you can set `JARVIS_VOICE_LANGUAGE=ru` (PowerShell: `$env:JARVIS_VOICE_LANGUAGE = 'ru'`) to avoid automatic language detection.

### Microphone dependencies

- **Debian/Ubuntu/Mint:** `sudo apt install libportaudio2`
- **Fedora:** `sudo dnf install portaudio`
- **Arch/EndeavourOS/CachyOS:** `sudo pacman -S --needed portaudio`
- **openSUSE:** use `zypper search portaudio` and install the available runtime package.
- **Windows 11:** sounddevice wheels normally bundle PortAudio DLLs; permit microphone access for desktop applications in Windows privacy settings.

Python dependencies are launched in an isolated uv environment. JARVIS does not automatically install operating-system packages or grant microphone permissions.

**This is not a wake-word system or a continuous voice conversation.** One recording becomes one Codex interactive session. The microphone never runs as a background daemon.

### Troubleshooting

- **PortAudio library not found:** install the runtime.
- **No input device:** check microphone and PulseAudio/PipeWire or Windows microphone permissions.
- **Invalid sample rate:** some devices cannot record directly at 16 kHz; use a compatible input or adapt the recorder with resampling.
- **Transcription failed:** check model download, disk cache, uv and available RAM.
- **No speech detected:** verify the mic and record longer than one second.
- **Poor recognition:** use multilingual small and set a language hint. Review the transcript before YES.

Upstream: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [python-sounddevice](https://github.com/spatialaudio/python-sounddevice).
