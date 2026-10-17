# Voice activation and hands-free requests

Preferences > Wake configures the background listener. Local Whisper is the
default; Online Google Web Speech is a separate explicit choice without a
personal API key. Voice requests use the independent provider in Preferences >
Voice. Listening, automatic recording and automatic sending are separate saved
choices. New settings keep listening, automatic recording and automatic sending
off until enabled.

## Configure the listener

1. Choose a wake provider and language. Online requires a language such as
   Russian; Auto detect is local-only. Local base uses CPU int8 with at most four
   threads; tiny uses fewer resources, small may recognize difficult speech
   better. Models download once and then work offline.
2. Choose the microphone or System default. Use Prepare saved provider / list
   microphones in the Voice tab to populate the list, or enter a device ID/name.
3. Enable Listen for Tigo in the background and Apply voice activation. Optional
   tolerant matching accepts a small explicit set of English/Russian wake-name
   variants and split tokens; exact mode accepts only whole name tokens. An
   eight-second cooldown suppresses duplicate activations.
4. Enable Start listener when I sign in (keep window hidden) for login startup.
   It applies only while background listening is enabled. This starts after
   graphical user sign-in, not at the lock/login screen or as a system service.

Local mode processes bounded speech phrases on this computer. Explicit Online
wake mode sends speech phrases near the microphone to Google over HTTPS,
including phrases without the wake name. The public personal/testing service
can impose limits or become unavailable; it is not the paid Cloud Speech API.
Unintelligible speech is ignored; connection/service failures stop the listener
with an error and require retrying settings. No account or personal API key is
needed. Select Local to avoid uploading wake audio.

Ordinary wake transcripts are discarded: not displayed, logged, sent to Codex
or saved in settings/history. Only wake/status events leave the worker. Audio
buffers/queues are bounded in RAM; online audio already received by the service
cannot be recalled. This is speech transcription, not speaker identification or
a dedicated low-power wake-word model. Speech from media/another person may
activate it; recognition can miss names.

## Short names and microphone diagnostics

Wake capture uses the existing local WebRTC detector in 20 ms frames, rather
than a fixed loudness cutoff. At least 160 ms of detected speech qualifies;
about 660 ms of silence finishes a phrase. A phrase is capped at four seconds,
with 240 ms of pre-roll/overlap to retain the beginning of a name. Bounded gain
(up to 12x, without clipping) helps quiet speech before either transcription
provider. This runs locally even when Online is selected.

Exact matching accepts whole Tigo tokens, their Russian spelling and mixed
Latin/Cyrillic name letters emitted by multilingual recognition. Tolerant mode
also accepts a finite set of observed spellings, including Tido/Tiga and their
Russian equivalents. It does not accept arbitrary one-letter edits or ordinary
similar words such as time, tiger or the Russian words for quiet/taiga. Tolerant
mode can still wake on another person's speech or an accepted name variant.

While listening, the bottom of Preferences > Wake shows a microphone meter,
speech detection, a phrase count and a content-free recognition result:

- An empty meter while speaking suggests the wrong/muted microphone or missing
  OS microphone permission. Check the selected device and system input level.
- A moving meter without speech phrases suggests noise, very quiet/short speech
  or insufficient pause. Say Tigo clearly, then pause for about one second.
- Increasing phrases with no name match means capture reached recognition. Set
  Russian or English explicitly; try Local small and tolerant matching.
- An unclear result means the online service did not understand the phrase.
  A service error stops listening; Apply voice activation retries the worker.

The meter and result do not expose/save recordings or transcripts; counters are
in-memory and reset on listener restart. Pausing clears the live meter. Recognition
is not guaranteed in noise or for every voice. After updating, Quit Tigo and
launch it again: hiding the window leaves the old listener running.

## Wake, record and send

Enable Start recording a request after Tigo wakes. Say Tigo, wait for the window
and listening indicator, then dictate the request. The listener closes its
microphone before the dictation worker records, and pauses while a task runs or
Tigo speaks. The wake phrase is not used as the command; words spoken before
command recording begins are not recovered. Default behavior still places the
recognized text in the composer for review and Send.

For hands-free sending, enable Send voice requests automatically after a speech
pause in Wake or Voice. This setting saves immediately and applies to all voice
requests, including manually started recordings. Local WebRTC VAD identifies
speech and waits for the selected 1.2 / 1.6 / 2.4 / 3.2-second pause (default 1.6).
The VAD runs locally for both transcription providers. Then the normal Codex
request path submits the recognized text once, without pressing Send. Background
voices/noise and transcription errors can affect it; leave it off for review.

- Eight seconds without detected speech cancels without transcription/upload or
  a request. Capture is capped at 60 seconds.
- Manual Stop or the 60-second cap keeps the transcript for review. Only a
  detected speech-ending pause qualifies for automatic sending.
- Existing/edited drafts, attachments, another running task or interrupted
  worker completion prevent automatic sending; the transcript is kept in the
  composer. Draft contents and existing attachments are not sent by this mode.
- Escape/Cancel stops recording/transcription and ignores late results. A task
  already submitted uses normal Stop; completed actions are not undone.
- Ordinary wake transcripts never submit commands. Automatic recording and
  sending each require their own opt-in; enabling wake listening alone restores
  the window only. The CLI `tigo voice` retains explicit YES confirmation.

## Background startup, close and quit

Login startup runs the current environment's Python with `-m tigo_gui
--background` and keeps the main window hidden, even when no tray is available
or the listener reports an error. A normal app launch restores the existing
instance. When available, the tray shows status and Open/Disable/Quit actions.
Closing an already-open window keeps listening in the tray, or minimizes without
a tray. Quit Tigo stops all workers; disabling listening removes its owned login
entry. A checked startup option applies again at next sign-in.

Registration is per-user without elevation:

- Linux: `$XDG_CONFIG_HOME/autostart/tigo-voice.desktop`, default
  `~/.config/autostart/tigo-voice.desktop`.
- Windows: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, value
  `TigoVoiceActivation`, using the environment's pythonw.exe.

Unrelated entries are preserved. Keep the checkout/environment in place and
reapply Wake settings after moving them. Minimal Linux compositors must consume
XDG autostart; bare Hyprland may require an explicit exec-once entry in your own
configuration. Tigo does not edit compositor settings automatically:

```ini
exec-once = "/absolute/path/to/Tigo/gui/.venv/bin/python" -m tigo_gui --background
```

Manual background launch uses `bash scripts/tigo-gui-linux.sh --background` or
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File
.\scripts\tigo-gui-windows.ps1 -Background`. Without saved listener opt-in it
exits without opening a microphone. Same-user local IPC prevents two Tigo
instances; no network listener is exposed.

## Installation and verification limits

The voice extra includes locked webrtcvad-wheels for local endpoint detection
and SpeechRecognition for keyless online transcription; platform updaters check
their imports. No new audio drivers, personal keys or system service are needed.
Existing microphones/OS permissions and native desktop ownership guards apply.
See [dictation](voice-input.md) and [installation](install-desktop.md).

Tests use simulated audio/model/service results, real Qt processes, the actual
QML and isolated startup files/registry fixtures. A synthetic audio check uses
the real WebRTC detector. Real microphone accuracy, system-login startup and
native tray/focus behavior still require target-desktop verification.
