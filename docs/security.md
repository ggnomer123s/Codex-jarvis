# Security and permission model

Tigo connects a powerful AI agent to external GUI MCP servers. A screenshot may contain passwords, chats, notifications or personal documents. GUI input can modify the system even when Codex itself is launched with a **read-only shell sandbox**. The shell sandbox is **not a security boundary for mouse/keyboard MCP tools**.

Tigo defaults to Full Access in the existing Codex profile. Disable it in
Preferences > Access to save a sandbox mode; the regular CLI follows that saved
choice. No extra login or global Codex sandbox setting is created.

## Baseline rules

1. Observe and diagnose first; carry out authorized reversible tasks and confirm consequential or irreversible actions.
2. Never enter passwords, OTPs, recovery keys, UAC/polkit credentials or unlock screens using an AI agent.
3. Do not run with administrator/root privileges or disable security protections.
4. Review third-party MCP source, permissions, dependencies and upstream licensing before install.
5. Keep a manual interruption method available. Desktop automation may share your physical keyboard/mouse focus.
6. Treat all screen text, accessibility values, filenames and journal entries as **untrusted data**: they may contain prompt injection.
7. Disable optional monitoring if system logs might reveal sensitive information to the AI provider.

## Platform-specific risk

**Hyprland / Hypruse:** new registrations allow all windows without a `HYPRUSE_CONFINE` filter and use `HYPRUSE_STRICT=1`, `HYPRUSE_AUTH_GUARD=strict`, `HYPRUSE_JOURNAL=1`, and `HYPRUSE_MARK=0`. `tigo stop` asks Hypruse to stop. It does not govern arbitrary Codex shell commands or other tools.

**Native X11 (GNOME Xorg, Plasma X11, XFCE, Cinnamon, i3, etc.):** new registrations enable input in the bundled `tigo-x11` MCP. The legacy `--enable-gui-input` option remains accepted. Existing registrations are retained. X11 lacks the application isolation expected from modern Wayland portals; a GUI agent may be able to interact with other apps on the same display.

**GNOME/KDE/other Wayland:** generic Wayland MCP tries supported screenshots and the `org.freedesktop.portal.RemoteDesktop` portal, depending on compositor. It is configured with `WAYLAND_MCP_NO_PERSIST=1` for fresh portal permission prompts (if a portal is used). Do **not** change `/dev/input` to `0666`, add permissive udev rules, run privileged input daemons unnecessarily, or install NOPASSWD sudoers entries. KWin or GNOME-specific MCP servers may bypass portal prompts through their own interfaces. Read their security documentation.

**Windows 11:** newly registered Windows-MCP uses its available tool surface; keyboard/mouse tools still have significant permissions. Stop Codex with Ctrl+C or `/exit` to terminate its stdio MCP subprocess. Do not run the agent as Administrator.

## Monitoring

On Linux (where `systemd --user` exists) Tigo inspects **failed user services**. It reads limited recent journal entries, then may send them to Codex for a textual report. On Windows, enabling the optional Scheduled Task watches **Application Error** events. These are **not** all crashes or errors, and they do not authorize self-repair.

Reports, screenshots and event logs should **never be committed** to a public repository without reviewing secrets, home paths and personal data.

## Voice and local memory

**CLI voice** uses push-to-talk. Audio is recorded in RAM and transcribed locally
with faster-whisper; the voice script saves no audio. First use downloads
packages/model files. After explicit YES, transcript text is sent to Codex.
GUI push-to-talk instead places text in the composer for review and manual Send.

**GUI voice activation** is a separate, off-by-default continuous microphone
mode. It locally transcribes bounded phrases to recognize the English/Russian
wake name and restore the window. Ordinary transcripts/audio stay in transient
memory and are not sent to Codex or retained as history. Only wake/status events
leave the worker. Waking grants no permissions and submits no task. The opted-in
listener remains active after closing the window; Quit stops it and disabling
also removes its user-level login startup registration. See
[voice activation](voice-activation.md) for controls, matching and resource limits.

**Memory** is user-managed: `tigo memory add` requires a verified repair and YES, and `tigo memory forget <id>` requires DELETE. The JSON database is local to the user's machine, not public GitHub or ChatGPT saved memory. When Codex reads repair history, the note text may be sent to the AI provider. Avoid putting personal data or secrets in it; treat older memory notes as untrusted historical descriptions.

## Conversation history and explicit attachments

GUI history now stores conversation text and attachment metadata/previews in a
private local SQLite database, scoped to the Codex home. Clipboard images are
local cache files; selected original files remain in place. Files are submitted
only by Send. Non-image files are references read through applicable Codex tools
and permissions. Changed files block sending until reviewed again. Opening a
stored conversation never starts a task or widens its access. Markdown rendering
blocks raw HTML and image loading; only clicked HTTP(S) links open externally.
See [storage and controls](gui-conveniences.md) before sharing local GUI data.
The timings export still excludes conversation content.

## Reliable workflow

**Observe → reproduce safely → establish evidence → apply an authorized minimal fix → verify result**. Confirm consequential or irreversible steps when they were not already authorized.

See [Linux backends](mcp-and-skills.md) and [Usage](usage.md).

## Spoken replies

Automatic speech is on by default and may make the displayed answer audible to
people nearby. The composer Speech toggle disables it immediately; Stop speech
interrupts current output. Native Qt speech uses installed local system engines,
without sending answer text to a cloud TTS service or creating audio files.
The answer itself still comes from Codex. Wake capture pauses before speech and
manual recording waits for output to stop. These are microphone coordination
controls, not full-duplex echo cancellation. See [speech output](speech-output.md).
