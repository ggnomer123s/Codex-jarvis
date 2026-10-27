# Codex account recovery and live limits

GUI 0.15.0 displays **5 hours** and **Weekly** remaining usage directly above
the composer, with progress bars, reset times and a last-update timestamp.
It starts a read-only Codex connection when a visible panel opens; no prompt,
thread or desktop action is submitted to discover usage.

The panel reads native `account/rateLimits/read` metadata every 60 seconds and
processes `account/rateLimits/updated` notifications immediately. Countdown text
refreshes every 15 seconds. Window durations must be 300 and 10080 minutes;
unknown windows, absent subscription data and API/provider limitations display
Unavailable. A selected model's reported bucket takes precedence over the common
Codex bucket. Buckets are not mixed and percentages are not guessed. Expired
reset timestamps do not reset a displayed allowance without fresh server data.
Disconnected/failed/old snapshots are marked as last known. Data stays in RAM.

**Hide:** press the panel's X. This saves `showUsageLimits=false` and stops quota
polling. **Restore:** use Limits beside Attach files or enable **Preferences >
Runtime > Show Codex usage limits above the composer**. Manual Refresh reads
metadata only. Percentages do not grant permission to use a model or workspace.

## Workspace routing unauthorized (401)

This is a Codex authentication/workspace-routing refusal, not missing filesystem
Full Access. Before starting a thread/turn, Tigo asks native `account/read` to
refresh the existing session token. Revoked/invalid credentials or denied
workspace access still require sign-in/account repair; the GUI cannot grant it.

A refusal produces one actionable error and a sign-in banner rather than repeated
raw error cards. Further submissions stay in the composer until account recovery.
Use **Sign in to Codex**, complete device sign-in in the existing Codex home,
then review/resend the failed request. Successful login reconnects the owned
app-server while retaining the chat and thread pointer. No task is replayed,
no other model is substituted, and no credentials are copied or fabricated.
If refusal persists, update the installed Codex CLI and check the selected
ChatGPT workspace/account permissions. Full Access and Administrator/root do
not override this server-side decision.

## Voice error on the screenshot

The online recognition service can receive audio but fail to identify words.
Final dictation now has an optional default-on local CPU Whisper fallback using
the same recording. A recovered transcript always requires review and Send.
See [dictation recovery](voice-input.md#online-recognition-recovery-0150).

This patch was reviewed statically without test/GUI/CI runs at the user's
standing request. Live login recovery, actual quota values and microphone
recognition on the user's computer have not been verified in this cloud.
