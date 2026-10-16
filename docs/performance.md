# Tigo performance tuning

**Problem:** A GUI request takes minutes because an agent repeatedly captures screenshots, thinks about each tiny action, and calls tools one by one.

**Solution:** optimize for the fewest **model/tool round trips**, not the fastest simulated mouse movement. Hypruse already offers cheap compositor IPC and accessible GUI controls.

## Quick start

After pulling the latest version and rerunning the installer, use:

```sh
tigo           # Fast mode is the default: low reasoning effort
tigo fast      # Same fast mode explicitly
tigo normal    # Respect your existing Codex model/reasoning defaults
tigo deep      # High reasoning effort for difficult or uncertain problems
```

Tigo uses `codex --config model_reasoning_effort=low` for its default fast mode. This is a **per-launch override**, not a rewrite of `~/.codex/config.toml`, and it does not change the model. Model support for reasoning values varies; use `tigo normal` if the selected model rejects `low`.

**Important:** Lower reasoning effort can make an agent faster but less reliable on complicated troubleshooting. Use `tigo deep` or `tigo normal` if accuracy suffers.

The launcher no longer sends an initial auto-executed "inspect the desktop" prompt. You can type your actual task first.

## Fastest Hypruse workflow

| Need | Preferred tool | Reason |
|---|---|---|
| Find Telegram, Dolphin or another window | `desktop` | One semantic list, no screenshot |
| Focus/open/switch workspace | `hypr` / `launch` | Direct compositor IPC |
| Click Save/Search/Settings | `click_ui` by name | Accessibility tree instead of pixel guesses |
| Find accessible controls | `ui` | Text, not images |
| Click several known controls | `sequence` | One model/tool call for multiple safe actions |
| Verify a field after typing | `then='ui'` | Read back current value immediately |
| Verify window switch | `then='desktop'` | Cheap compositor snapshot |
| Wait for a new window | `wait_for` | Real event, no screenshot polling |
| Deal with canvas or non-accessible controls | `screenshot(window=...)` then `zoom` | Image only when genuinely required |

For example, navigating an **already authorized**, non-sensitive set of tabs can take one observation and one verified action sequence. For dialogs that submit, send, install, delete or modify settings, obtain explicit approval and keep the irreversible step separate.

## Don't do these things

- Do **not** screenshot every second or after every pointer move.
- Do **not** perform a separate `desktop` call after `then='desktop'` has already returned the current state.
- Do **not** capture lossless PNG unless pixel accuracy genuinely requires it.
- Do **not** use full-screen screenshots when a window capture will do.
- Do **not** have the agent narrate every intermediary mouse action.
- Do **not** bypass MCP confinement/strict guards or disable approval prompts in the name of speed.

## Quick diagnostic checklist

If a short GUI task still takes unusually long:

1. Check if there is an MCP approval prompt before **every** low-risk observation call. Approve read-only tools individually in your Codex UI where appropriate; don't grant unrestricted desktop/system control.
2. Ask the agent to report a **count** of `desktop`, `ui`, `screenshot`, `sequence`, `click_ui` and other MCP calls on its last task, based on actually available logs, without inventing numbers.
3. Check whether the target app exposes an accessibility tree. Some terminals, games and Electron views may force screenshot fallback.
4. If Codex model deliberation is the bottleneck, try `tigo` (low) versus `tigo normal` on the **same low-risk task**.
5. Verify `HYPRUSE_CONFINE` is not preventing the action. **Never bypass a refusal by switching tools**.
6. Restart Codex after changing Skills or MCP registrations.

`HYPRUSE_JOURNAL=1` can help audit which actions were made. Do not publicly post journals or captures containing private data.

## Validation

The repository's CI runs static checks and memory tests, **not live performance benchmarks**. These changes are expected to lower avoidable round trips, but speed improvements depend on the selected model, application, approvals and network latency. No guaranteed speedup or time estimate is claimed.

See [GUI navigation](gui-navigation.md) and [Security](security.md).

## Desktop GUI runtime

The GUI now uses persistent Codex app-server and local voice workers, streamed
chat, content-free timings, exact checked workflow aliases and optional local
reasoning adaptation. These changes remove repeated initialization paths from
the source; they are not a measured end-to-end benchmark. Use Runtime to compare
cold/warm requests and verify success alongside duration. See [runtime.md](runtime.md)
and [the related-project source review](related-projects.md).
