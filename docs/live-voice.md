# Live dictation and incremental speech

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
No automatic provider fallback or microphone opening is added.

Preferences > Speech independently selects local neural, online Microsoft or
legacy system speech. With automatic speech enabled, all assistant messages,
including progress/commentary, enter one ordered queue as complete sentences or
lines arrive. The remaining fragment is flushed when the message ends. Code
fences, raw URLs and reasoning/tool payloads are not read. Completed messages
are not replayed at turn completion; opening history remains silent. A manual
Read action replaces pending speech. Stop speech mutes subsequent chunks of the
current turn; a new task resets that mute. Starting dictation waits for playback
and microphone handoff before capture.

Existing online speech sends queued spoken text to Microsoft; local neural
speech remains on the computer after voice downloads. Queue capacity is bounded
(256 fragments / 64,000 queued characters); exceeding it stops with a visible
error instead of growing indefinitely. Long text chunks retain the existing
speech sanitizer/length bound. This is sentence-level audio generation; playback
can lag text depending on the selected voice, CPU, downloads and network.

Install/update with the existing voice extra. No dependency or platform setup
change is required. Verification uses simulated model/service results, real Qt
processes/QML and fake audio playback. It is not a Windows microphone benchmark
or a live online service latency/accuracy test.
