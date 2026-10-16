# Shared Codex profile and Full Access

Tigo uses **one Codex home**, login and MCP configuration on Linux and Windows
11: the current `CODEX_HOME`, or `~/.codex` if it is unset. The desktop app,
ordinary CLI and compatibility full launchers all reuse it. No credentials are
copied and no extra profile is created.

## Default and settings

Full Access is on by default. In **Preferences > Access**, uncheck **Enable Full
Access** to select the retained read-only or workspace-edit sandbox. This choice
persists after restart and is shared with regular `tigo fast|normal|deep`.
Checking it again changes runtime permissions without installation or sign-in.
The active mode remains visible in the window.

The shared preference is stored at:

- Linux: `~/.local/share/tigo-codex/access-mode`.
- Windows: `%LOCALAPPDATA%\tigo-codex\access-mode`.

Missing preference means `full-access`; valid restricted values are `read-only`
and `workspace-write`. Invalid/unreadable preferences select read-only. Installers
do not reset a saved choice. The global Codex config is not changed to disable
its sandbox for unrelated Codex launches.

Full Access uses `danger-full-access` / approval policy `never` in app-server,
or `--dangerously-bypass-approvals-and-sandbox` for CLI launches. This grants
access available to the current user, not root/Administrator elevation or a
bypass of OS authentication, locked sessions or MCP-specific guards. Switching
GUI access restarts its owned app-server and clears context in the same home.
Run Tigo as a normal user. Existing desktop backend restrictions are preserved.

## Windows desktop ownership

The existing **Enable Full Access** checkbox is on by default. It controls
Codex command/file access. A Windows-MCP message that the user owns the desktop
is a separate, temporary ownership hold; toggling Full Access does not clear it.
No additional always-own-the-desktop checkbox is provided.

1. Open **Preferences > Access > Check desktop control**, or enter the local
   `/desktop-status` command. It reads `ControlStatus` from the configured
   `windows-mcp`, using the owned app-server without a model turn or input call.
2. Read the observed state and remaining wait. This is a snapshot; it does not
   acquire control or keep polling. Clicking the button is itself physical input,
   so seeing an idle wait immediately afterward is expected.
3. Ask Tigo to continue, then leave the mouse and keyboard idle for the service's
   configured interval, normally 10 seconds. Physical input restarts that wait.
   The updated Skill explains waiting and checking ownership with ControlStatus
   before a fresh observation; the tool check itself does not simulate input.

`ready` means no user hold is currently reported, not a guarantee that a future
action will pass every check. `user`, `takeover_pending` and `unavailable` require
pausing desktop actions. File work unrelated to the blocked desktop action may
continue under its existing permissions. Do not repeat actions whose effects
are uncertain or substitute raw input after a refusal.

If ControlStatus is missing, check the installed Windows-MCP version and tool
exclusions. The app reports that limitation without changing registrations,
restarting the service to clear a takeover, or trying an input fallback. Existing
manual takeover, visible control indication, locks and authentication remain.
The app cannot diagnose an unknown third-party screen service from a paraphrased
assistant message alone; these diagnostics apply specifically to Windows-MCP.

Upstream reference checked on 2026-10-16:
[desktop control and policies](https://github.com/CursorTouch/Windows-MCP/blob/c9a307cd8077b7dec07dbe57df1e18ca135ebde7/README.md#desktop-control),
[read-only ControlStatus](https://github.com/CursorTouch/Windows-MCP/blob/c9a307cd8077b7dec07dbe57df1e18ca135ebde7/src/windows_mcp/tools/control_status.py).

## Installation and compatibility

Use the [normal GUI installation/update commands](install-desktop.md).
All Linux distributions use the same `install-linux.sh` implementation for
session/backend detection; Windows uses `install-windows.ps1`. New supported
desktop MCP registrations enable their normal tool surface. Existing registrations
are retained, including any deliberately configured confinement/input restrictions.

The old `install-full-linux.sh` and `install-full-windows.ps1` entry points now
delegate to the ordinary installer. Old acknowledgement arguments are accepted
for command compatibility but are not needed. Old private profile directories
are left untouched and unused; authentication is not automatically migrated.
If your usual Codex home is not signed in, run `codex login` once or use
**Sign in to Codex** in Access settings.

`tigo-full` and `tigo full` remain explicit Full Access aliases using this
same home. They intentionally request Full Access even if the regular launcher's
saved preference is restricted. Their `fast`, `normal`, `deep`, `login`, `status`
and `help` commands remain supported; no automatic startup task is submitted.

| Command | Reasoning | Access |
|---|---|---|
| `tigo` / `tigo fast` | Low | Saved access; initially Full Access |
| `tigo normal` | Configured default | Saved access |
| `tigo deep` | High | Saved access |
| `tigo-full fast` / `normal` / `deep` | Low / configured default / high | Explicit Full Access, same home |

The Windows installer scopes a non-terminating error policy to the expected
`mcp get windows-mcp` existence probe. A missing server triggers registration
instead of a PowerShell 5 `NativeCommandError`; registration failures still stop
installation with an actionable error.

## Composer controls

Select the model and reasoning level at the bottom left of the input area.
Model changes clear prior conversation context but keep your unsent draft.
Reasoning changes apply to the next turn. Choices follow the selected model's
advertised capabilities after the live catalog is loaded. Neither changes the
Codex account, access mode or authentication.
