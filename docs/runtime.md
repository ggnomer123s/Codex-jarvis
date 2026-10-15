# Persistent JARVIS runtime

The desktop GUI uses **Codex app-server over local stdio JSON-RPC** as its only
model transport. It does not switch to OpenCode or silently fall back to
`codex exec`. The terminal `jarvis` launchers remain interactive Codex CLI tools.
Update Codex if the app-server command or required methods are unavailable.
The transport was probed with Codex CLI **0.159.2** on Linux: initialization and
`config/read` succeeded without making an authenticated model request.

## Processes and permissions

The GUI starts its own `codex app-server --listen stdio://` on the first task or
model refresh. It sends `initialize`, `initialized`, `thread/start` or
`thread/resume`, then `turn/start` for model requests. The process and thread stay
loaded between follow-ups. `item/agentMessage/delta` updates a single chat row;
the completed item replaces provisional text with the authoritative response.
Reasoning/tool events are used for activity, not rendered as assistant text.

Thread options explicitly set `approvalPolicy=never` and the selected sandbox:
`read-only`, `workspace-write`, or `danger-full-access`. Unexpected approval,
permission and elicitation requests are declined, never silently accepted.
Full Access is on by default and can be disabled in Preferences > Access. The
saved access flag is shared with regular CLI launchers. All modes use the same
`CODEX_HOME` (default `~/.codex`), existing login and MCP configuration. Switching
access closes the owned process, clears context and starts a new process in the
same home with different sandbox options. The GUI does not attach to a shared
daemon or open an HTTP/WebSocket listening port.

Stop sends `turn/interrupt`. If interruption does not complete, or a task is still
starting, the GUI closes its owned process tree. Direct workflow MCP calls do
not have a per-call interruption method here, so stopping a workflow closes
that connection. Timeouts are not automatic retries: an operation may already
have had effects. Completed actions are never claimed undone.

## Local voice

The GUI's push-to-talk worker loads one multilingual faster-whisper model and handles repeated
JSON recording commands. It opens the microphone only for an explicit recording.
The model unloads after five idle minutes, on model/device/options changes, or at
shutdown. **Preferences > Voice > Prepare saved model / list microphones** can
warm the saved model before recording. First use may need a model download;
an existing converted local model directory supports offline use.

CPU int8 is the default. Optional NVIDIA CUDA uses int8-fp16 and requires a
compatible CTranslate2/CUDA/cuDNN installation. CUDA errors are reported rather
than silently selecting another device. Beam sizes 1, 3 and 5 are available;
compare recognition of names, numbers and application titles before choosing
the fastest value. Russian uses `ru`; Auto uses Whisper language detection.

The realtime audio callback only enqueues PCM into a bounded queue. The worker
calculates levels and emits JSON outside the callback. Audio remains in memory,
is limited to 60 seconds, and is not uploaded or saved by this worker. Overflow
fails explicitly instead of transcribing a silently truncated recording.

Optional provisional text processes new chunks on energy-detected pauses or
longer intervals, with final Whisper VAD filtering. It is **not** true online
Whisper decoding, continuous listening, wake-word detection or speech endpoint
submission. It can cost additional CPU, may revise wording, and stays out of the
composer until the final transcript is ready. Only the reviewed final text is
submitted when the user presses Send. Recording IDs discard stale results.

The separate, opt-in [background wake listener](voice-activation.md) continuously
captures and locally transcribes bounded phrases while enabled. It restores the
window on the English/Russian wake name, without sending speech to Codex. Its
model, language, microphone, fuzzy matching and sign-in startup are configured in
**Preferences > Wake**. Capture pauses before manual voice input and resumes
afterward; stale inference is discarded. Closing the window keeps the opted-in
listener in the tray/minimized. Quit stops workers; disable also removes startup.

## Local spoken output

Qt TextToSpeech uses installed Windows winrt/sapi or Linux speechd/flite engines.
Speech initializes lazily and stays separate from Codex and Whisper. Only the
current successful completed final answer is automatically read; manual Read
also works with automatic speech off. Opening history stays silent.

Wake capture must acknowledge pause (or its process must exit) before speech
starts. A 300 ms cooldown keeps the mic paused through the audio tail. Recording
interrupts speech and waits for quiet; generation/recording IDs reject canceled
callbacks. Shutdown stops owned speech. No full-duplex echo cancellation is
implemented. Settings, voice prerequisites and text limits are described in
[speech output](speech-output.md).

## Fast commands

These commands execute locally without model inference:

| Command | Result |
|---|---|
| `/help` | List local commands |
| `/status` | Connection, desktop MCP inventory and voice timing status |
| `/metrics` | Display content-free timing records |
| `/workflows` | List saved exact command aliases |
| `/open-workspace` | Ask the desktop to open the selected folder |
| `/resume` | Restore the saved conversation for this workspace/profile/model |
| `/new` | Clear the current conversation and its resume pointer |

Opening a folder reports desktop dispatch acceptance, not proof that a file
manager finished opening it. Unknown requests go to Codex. Custom workflow
aliases match the entire trimmed request, case-insensitively; a longer request
containing an alias is not intercepted.

## Checked desktop workflows

Add a JSON array in **Preferences > Automation**, then save preferences. Only
definitions explicitly saved through user settings are loaded; neither model
responses nor files found in a workspace can register a workflow.

Each workflow has a name, exact aliases, and 1 to 5 steps. Each step contains a
desktop MCP `call`, an optional `before` observation, a required `after`
observation and optional `timeoutMs` (500–30000).
`timeoutMs` bounds postcondition verification; individual precondition/action
calls have a separate 30-second RPC limit. The executor dispatches one
action at a time through `mcpServer/tool/call` on the active Codex thread. This
uses its configured desktop MCP, not a new raw input backend. Server-side
confinement, input opt-in, seat and authentication guards remain authoritative.
Shell, registry, filesystem and arbitrary third-party server tools are excluded
from these shortcuts. Existing Codex tools remain available to normal tasks.

For example, on X11, replace **both** `0x1234` values with a window ID you just
observed. This requires existing X11 input permission; it does not enable it:

```json
[
  {
    "name": "Focus editor",
    "aliases": ["focus editor"],
    "steps": [
      {
        "call": {
          "server": "jarvis-x11",
          "tool": "focus_window",
          "arguments": {"window_id": "0x1234"}
        },
        "after": {
          "call": {"server": "jarvis-x11", "tool": "active_window", "arguments": {}},
          "path": ["id"],
          "equals": "0x1234"
        },
        "timeoutMs": 3000
      }
    ]
  }
]
```

Structured checks traverse `structuredContent`, or a single JSON text result,
using `path` keys/array indices and compare one scalar with `equals`. A check
may instead use `contains` to match a nonempty substring in text/structured
output. Prefer exact structured values for identity and state: matching a title
substring alone does not prove focus, save completion or the intended result.
Use current tool schemas and application-specific success conditions. Workflow
definitions store arguments in user settings: do not place credentials there.

A failed precondition, MCP refusal or verification error stops remaining steps.
The executor never repeats the action to make a check pass. It can repeat only
the read-only postcondition at 250 ms intervals until the verification deadline.
Use backend-native `wait_for` / `WaitFor` where available instead of repeated
observations. The X11 backend now exposes bounded `wait_for_window(title,
timeout_ms)` using xdotool synchronous visible-window search and returns window
IDs; it also returns structured active-window identity. Neither injects input.
Accessibility and semantic observations avoid unnecessary screenshot processing;
canvas applications still require an appropriate visual/native adapter.

## Reasoning and conversation checkpoints

**Adapt reasoning to task difficulty** is optional. A local heuristic selects
low effort for simple open/focus/play requests and high effort for diagnostic
keywords or the request following a failed task. It adds no classifier model
call, does not retry the failed request, and respects a model's advertised
reasoning options when the live catalog provides them. Other requests use the
selected preset. This is not a guarantee of correct difficulty classification.

The GUI saves at most 30 thread pointers with status and completed-step count,
scoped to canonical workspace, Codex home, access and model. **Resume previous**
explicitly restores the conversation and displays recent text history. It does
not re-run a prompt or replay any desktop actions. A missing/inaccessible thread
is reported; it does not silently create an unrelated thread. Conversation text
is not copied into QSettings. It now also persists in the separate local SQLite
[conversation history](gui-conveniences.md#history-and-privacy); Codex retains its
own session history. Opening a history entry displays text locally and the next
Send resumes its thread with matching access. Arbitrary task
replay, editor rollback and automatic workflow continuation are not implemented.

## Measurements and limits

**Preferences > Runtime** shows connection/MCP status and the latest task timing.
Export saves the last 30 completed task records and current voice timings as
JSON, without prompts, response text, tool arguments, audio or screenshots.
Records include server/thread readiness offsets, first assistant-text offset,
total duration, execution/tool counts and per-tool intervals. Screenshot counts
are a heuristic count of screenshot/snapshot/zoom tool names, not image bytes
or proof that a snapshot included an image. Intervals can overlap; do not sum
them as if they were independent model/CPU latency measurements.

Connected app-server does not prove account authorization, microphone access or
desktop input readiness. Tests exercise actual Qt processes/QML with simulated
Codex, audio and MCP results. A real app-server handshake/config probe passed on
Linux, but authenticated model calls, NVIDIA execution, live Windows audio and
compositor actions still require target-machine verification. No measured
end-to-end speedup is claimed. Compare identical tasks cold/warm with the same
model, machine, network, access and app state; report latency and successful
outcomes together.

See [related project research](related-projects.md) for the source comparisons.
