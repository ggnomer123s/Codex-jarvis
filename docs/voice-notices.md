# Neural speech sources and notices

Voice assets download separately rather than being committed as binaries.
The catalog and pinned archive sizes/SHA-256 values live in
`gui/jarvis_gui/speech_models.py`.

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx): Apache-2.0 runtime;
  [official TTS models](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models).
- [Piper](https://github.com/rhasspy/piper): source voice architecture and model
  collection. Current Piper implementations have separate licensing; JARVIS
  uses sherpa-onnx inference rather than the `piper-tts` Python package.
- Dmitri, Denis and Joe model cards identify
  [Nabu Casa voice datasets](https://github.com/NabuCasa/voice-datasets) and state
  **CC0 for the datasets**, with fine-tuning from Lessac medium. Keep their cards
  with cached weights. Dataset statements do not relicense every dependency or
  imply an actor's endorsement.
- Packages include eSpeak NG phonemization data. eSpeak NG has
  [GPL-3.0 licensing and notices](https://github.com/espeak-ng/espeak-ng).
  Neural inference uses text-to-phoneme conversion, rather than eSpeak's old
  synthetic speech waveform. Respect upstream obligations when redistributing
  bundled binaries/data instead of installing upstream dependencies.
- [ONNX Runtime](https://github.com/microsoft/onnxruntime) uses MIT licensing.
  Qt, Python and audio components retain their respective upstream licenses.

These provenance notes do not change project source licensing or grant
permission to clone a person's identity or voice.
