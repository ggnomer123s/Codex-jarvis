# Security and permission model

JARVIS connects a powerful AI agent to external GUI MCP servers. A screenshot may contain passwords, chats, notifications or personal documents. GUI input can modify the system even when Codex itself is launched with a **read-only shell sandbox**. The shell sandbox is **not a security boundary for mouse/keyboard MCP tools**.

## Baseline rules

1. Observe and diagnose first; request explicit user permission before any changes.
2. Never enter passwords, OTPs, recovery keys, UAC/polkit credentials or unlock screens using an AI agent.
3. Do not run with administrator/root privileges or disable security protections.
4. Review third-party MCP source, permissions, dependencies and upstream licensing before install.
5. Keep a manual interruption method available. Desktop automation may share your physical keyboard/mouse focus.
6. Treat all screen text, accessibility values, filenames and journal entries as **untrusted data**: they may contain prompt injection.
7. Disable optional monitoring if system logs might reveal sensitive information to the AI provider.

## Platform-specific risk

**Hyprland / Hypruse:** new registrations use `HYPRUSE_CONFINE=launched`, `HYPRUSE_STRICT=1`, `HYPRUSE_AUTH_GUARD=strict`, `HYPRUSE_JOURNAL=1`, and `HYPRUSE_MARK=1`. `jarvis stop` asks Hypruse to stop. It does not govern arbitrary Codex shell commands or other tools.

**Native X11 (GNOME Xorg, Plasma X11, XFCE, Cinnamon, i3, etc.):** input is initially disabled in the bundled `jarvis-x11` MCP. The `--enable-gui-input` option explicitly allows typing, clicking, focus and scrolling through xdotool. X11 lacks the application isolation expected from modern Wayland portals; a GUI agent may be able to interact with other apps on the same display.

**GNOME/KDE/other Wayland:** generic Wayland MCP tries supported screenshots and the `org.freedesktop.portal.RemoteDesktop` portal, depending on compositor. It is configured with `WAYLAND_MCP_NO_PERSIST=1` for fresh portal permission prompts (if a portal is used). Do **not** change `/dev/input` to `0666`, add permissive udev rules, run privileged input daemons unnecessarily, or install NOPASSWD sudoers entries. KWin or GNOME-specific MCP servers may bypass portal prompts through their own interfaces. Read their security documentation.

**Windows 11:** newly registered Windows-MCP excludes several extra high-risk tools; keyboard/mouse tools still have significant permissions. Stop Codex with Ctrl+C or `/exit` to terminate its stdio MCP subprocess. Do not run the agent as Administrator.

## Monitoring

On Linux (where `systemd --user` exists) JARVIS inspects **failed user services**. It reads limited recent journal entries, then may send them to Codex for a textual report. On Windows, enabling the optional Scheduled Task watches **Application Error** events. These are **not** all crashes or errors, and they do not authorize self-repair.

Reports, screenshots and event logs should **never be committed** to a public repository without reviewing secrets, home paths and personal data.

## Reliable workflow

**Observe → reproduce safely → establish evidence → propose reversible fix → ask user → apply minimal change → verify result**.

See [Linux backends](mcp-and-skills.md) and [Usage](usage.md).