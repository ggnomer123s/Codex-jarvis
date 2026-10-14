# Related Jarvis, Codex and OpenCode projects

Source review: **2026-10-14**. Public GitHub repository searches included
`jarvis codex`, `jarvis opencode`, `codex voice` and `opencode voice`. The table
records source snapshots, not comparative desktop benchmarks. No competitor
code, models, artwork or dependencies were imported.

| Project and checked source | Useful mechanism | JARVIS decision |
|---|---|---|
| [Big-Guan/jarvis-codex](https://github.com/Big-Guan/jarvis-codex/blob/f4f92aecfc16ff1bf7f1c195ba14ab260a130087/src-tauri/src/lib.rs) | Owned app-server runtime, workspace thread resumption, validated permission profiles, unified STOP | Keep Codex app-server, isolate profiles, persist scoped conversation pointers, use protocol interruption. Its macOS Swift wake helper and experimental cloud Voice/WebRTC path are not a portable replacement for our local Russian STT. |
| [levinjeejan/opencode-jarvis](https://github.com/levinjeejan/opencode-jarvis/blob/55964acce506ab79c64d6c49a8f655141f03e0cc/jarvis/brain.py), [audio](https://github.com/levinjeejan/opencode-jarvis/blob/55964acce506ab79c64d6c49a8f655141f03e0cc/jarvis/audio.py) | Persistent OpenCode sessions, typed text-delta filtering, separate audio/VAD work, explicit states and abort | Adopt typed assistant streaming, separate capture/inference and clear listening/planning/acting states. Preserve Codex rather than introducing an OpenCode runtime. Always-listening, Piper output and full-duplex interruption are separate future features. |
| [renjfk/opencode-voice](https://github.com/renjfk/opencode-voice/blob/14075bf0593ec9cff7f574ee4eb7f47f2ff3d0b5/lib/stt.js) | Microphone/model/language selection, local STT controls, persisted preferences | Add microphone selection, beam/device options and local provisional text. Additional LLM normalization calls are not required: preserve the user's review step and avoid adding another request to every utterance. |
| [QwenAudio/qwen-audio-agent](https://github.com/QwenAudio/qwen-audio-agent/blob/b6a80d45745103aa0f9e4c1fb88be6dee1b7719f/server/src/task/task-store.mjs), [task cards](https://github.com/QwenAudio/qwen-audio-agent/blob/b6a80d45745103aa0f9e4c1fb88be6dee1b7719f/web/src/desktop/desktop-task-cards.js) | Explicit task lifecycle, persistent task state, visible progress; voice frontends separate from backend tasks | Add bounded timing history, task-stage presentation and content-free conversation checkpoints. A distributed gateway, ACP adapter and multiple simultaneous desktop-input agents would add complexity to our current single-desktop path. |
| [JaimeParker/stable-jarvis](https://github.com/JaimeParker/stable-jarvis/blob/cb2c7078e8b76a3125ae504aeb1ffa9c1ee2dc4b/README_en.md) | Reusable research Skills, selected verified knowledge, support for several agent clients | Useful organizational reference for small application-specific workflows and deliberate knowledge capture. It is a research/literature assistant rather than a direct desktop operator. Existing JARVIS repair memory remains user-confirmed; no automatic screen/history collection was added. |

All implementation decisions here
use our own source and existing Codex/MCP/Qt/faster-whisper dependencies.

## Earlier architecture references

- [Microsoft UFO multi-action execution](https://github.com/microsoft/UFO/blob/eae3c0a8d168c47cb10df0652e293e092eda1078/documents/docs/ufo2/core_features/multi_action.md): predict short sequences and validate live state. Our workflows require postconditions and stop instead of promising general rollback.
- [Agent-S3](https://github.com/simular-ai/Agent-S/blob/15776a8dc659658b1963816ea006f7af1978e595/gui_agents/s3/agents/agent_s.py): its main worker removes a hierarchical planning layer. Keep the simple-command path short; use additional reasoning selectively.
- [Windows-MCP](https://github.com/CursorTouch/Windows-MCP/blob/7fb9823aefc2f48704844442d04dafded0043e3f/src/windows_mcp/desktop/service.py): semantic/DOM observations, optional screenshots and stage measurements. This is already our Windows backend; use its installed capabilities rather than duplicating input.
- [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT/blob/ea248716cf1265eac69f5fdfc0acaca5b7047556/RealtimeSTT/audio_recorder.py): separate capture, provisional text and authoritative final transcription. Our chunk preview retains explicit push-to-talk and final review.
- [PolyCast5 AI task](https://github.com/RoboticWorx/PolyCast5/blob/e132f9b0335254d5a50810885be2f75064ad3c55/components/ai/src/ai_task.c): queued execution and generation IDs discard abandoned work. Its Bluetooth keyboard path has no computer-screen observation; the reviewed STT upload sets English. It does not establish local Russian transcription or verified GUI success. Its CC BY-NC-SA source was not copied.

## Implemented scope

The desktop GUI now uses a persistent Codex app-server connection, warm local
Whisper worker, bounded audio queues, typed incremental chat, exact local
commands, user-defined checked desktop workflows, native X11 window waiting,
optional difficulty-based reasoning, task timing export, scoped conversation
resume and state/audio-driven orb effects. See [runtime behavior](runtime.md).

The following remain distinct future projects: automatic execution/replay of
arbitrary interrupted tasks, app-specific Premiere/DaVinci bridges, continuous
screen understanding, wake words, spoken TTS answers and full-duplex speech.
None is necessary to keep the Codex app-server integration and local STT path.
