# Dictation: local and online

Open Preferences > Voice. The provider is separate from speaking voices in
Preferences > Speech. Press the microphone button to start, again to finish.
The final transcript fills the composer; review/edit it and press Send yourself.
No recording submits a task automatically. Capture is limited to 60 seconds.

## Local Whisper (default)

The multilingual faster-whisper model runs on this computer. New GUI settings
use small; existing saved choices and TIGO_VOICE_MODEL are respected. Choose
base/tiny for lower memory use or medium for more demanding speech. A model
folder can be entered for a pre-downloaded converted multilingual model.

The first use downloads model files. After they are cached, recognition works
offline. Choose Russian or another language to reduce detection uncertainty,
or Auto detect for multilingual recognition. CPU int8 is the default; CUDA needs
compatible NVIDIA libraries. The loaded model is retained for five idle minutes.
Optional provisional text uses extra local inference; the final text can differ.
Accuracy depends on microphone, noise, language and model. Audio stays in RAM.

## Online Google Web Speech (no personal API key)

Select Online, choose a speech language and save preferences. No account, API
key or Codex API billing setup is required. The implementation uses
[SpeechRecognition's built-in public personal/testing service configuration](https://github.com/Uberi/speech_recognition/blob/master/speech_recognition/recognizers/google.py),
with an explicit HTTPS endpoint. This is not the paid Google Cloud Speech API;
the upstream shared service can impose limits or stop being available.

Only a completed explicit dictation recording is encoded as FLAC and uploaded
to Google. Recording buffers and the response are kept in RAM; Tigo does not
write an audio file. The service processes the uploaded audio under its own
policies. No online previews or background wake uploads occur. Online mode
requires a chosen language; Auto detect is local-only. The existing microphone
selection works for both providers. There is no automatic fallback upload,
provider switch or request retry after errors. Select Local manually when offline.

The worker is retained between recordings without loading Whisper in online
mode. Cancel closes the owned worker and ignores late results; audio already
received by the provider cannot be recalled. A network error/timeout, unusable
speech or service limit produces an error without sending text to Codex.

## Installation and diagnostics

The normal installer/updater installs `uv sync --project gui --frozen --extra
voice`, including faster-whisper, sounddevice, numpy and SpeechRecognition.
No additional microphone library/PyAudio is used. Bundled FLAC converters cover
supported Windows/Linux x86-64 setups. Other architectures may need a native
`flac` executable; the one-step setup currently targets x86-64.

Preferences > Runtime reports dictation timings. Wake-name listening and the
`tigo voice` CLI remain local Whisper features. No provider choice changes
Codex login, MCP permissions, Full Access or saved speech-output voices.
