# Live dictation and complete-message speech

Preferences > Voice selects Local Whisper or keyless Online Google Web Speech.
Enable **Live text while recording (provisional)** and save. This defaults on for
new settings; an existing saved off choice is preserved. While recording,
partial recognition replaces the provisional part of the composer. Final
recognition corrects it once. Cancel restores the original draft when the user
has not edited it; edits stop automatic replacements and prevent automatic send.
Only a final transcript may qualify for the existing speech-pause send opt-in.

Local mode uses the existing Whisper worker, decoding bounded rolling windows
approximately every 1.2 seconds of captured audio when CPU capacity permits.
The current window's text can change; adjacent windows merge overlapping words.
The final full recording is recognized separately. No new model is required.

Online live text sends partial audio windows over HTTPS while recording, then
the completed recording for final correction. No personal API key is required.
This is repeated phrase recognition through the existing public service, not a
persistent realtime API. It can be slower, limited or unavailable. Disable Live
text to send audio only after recording. Cancel ignores late responses, but
cannot recall audio already uploaded. Ordinary wake recognition stays separate.
Final online dictation can use the saved local Whisper fallback in 0.15.0;
recovered text requires review. No additional microphone opening is added.

Preferences > Speech independently selects local neural, online Microsoft or
legacy system speech. With automatic speech enabled, each completed assistant
message card (the block with **Copy** and **Read**) enters one ordered speech
queue as a whole. This includes progress/commentary and the final answer.
Speech starts when that card completes, without waiting for the entire task.
Incoming text deltas update chat only; words, wrapped lines and individual
sentences are not separate automatic speech jobs. The completed card text is
authoritative, using the same speaking copy as **Read**. Code fences, raw URLs
and reasoning/tool payloads are not read.

Each card is queued once. Turn completion does not replay messages; opening
history stays silent. A manual Read action replaces pending speech. Stop speech
clears the queue and mutes subsequent cards of the current turn; a new task resets
that mute. A failed/canceled task stops pending speech; already played progress
cannot be recalled. Starting dictation waits for playback and microphone handoff
before capture. A card that never completes is not automatically read.

Existing online speech sends the spoken card text to Microsoft; local neural
speech remains on the computer after voice downloads. Queue capacity is bounded
(256 messages / 64,000 queued characters); exceeding it stops with a visible
error. Each card retains the Read action's existing 6,000-character speaking-copy
limit, with a notice directing the listener to chat for longer text. Synthesis
workers can internally process bounded audio phrases; they receive one whole
card job. Playback can lag text depending on the voice, CPU, downloads and network.

Queued messages start at the next event-loop opportunity when the engine is
quiet, without a fixed 300 ms pause or another microphone reservation between
messages. The 300 ms speaker tail remains at the end before microphone release.
Stop/Cancel still clear queued speech. Synthesis/network and speaker latency
remain; removing the scheduling gap does not eliminate them.

Install/update with the existing voice extra. No dependency or platform setup
change is required. Verification uses simulated model/service results, real Qt
processes/QML and fake audio playback. It is not a Windows microphone benchmark
or a live online service latency/accuracy test.
