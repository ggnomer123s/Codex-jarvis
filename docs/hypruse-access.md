# Hypruse: opt-in access to already open applications

JARVIS uses the upstream [Hypruse](https://github.com/IlyasKhallouki/hypruse) MCP backend on **Hyprland**. By default it registers `HYPRUSE_CONFINE=launched`, meaning it can act only on windows launched by that Hypruse server. A Codex **Full Access** approval does **not** remove this independent Hypruse restriction.

The upstream confinement syntax supports `class:firefox,kitty`. To allow an **already open** Telegram window, use the project's explicit access profile:

```bash
# In your local Codex-jarvis repository:
git pull --ff-only
bash scripts/hypruse-access.sh telegram
```

When prompted, inspect the current registration and type `APPLY` to confirm. This profile sets:

```text
HYPRUSE_CONFINE=class:org.telegram.desktop,kitty
HYPRUSE_STRICT=1
HYPRUSE_AUTH_GUARD=strict
HYPRUSE_JOURNAL=1
HYPRUSE_MARK=1
```

This is **opt-in**: the normal installation keeps the restricted `launched` mode. Restart the Codex/JARVIS session after changing the MCP registration. Telegram class names can vary by package: verify your window's actual class using `hyprctl clients -j` and the `class` field.

## Additional access profiles

```bash
# Show the current Hypruse MCP registration:
bash scripts/hypruse-access.sh status

# Allow only the listed application window classes:
bash scripts/hypruse-access.sh allow org.telegram.desktop firefox

# Restore default confinement to Hypruse-launched windows:
bash scripts/hypruse-access.sh restricted
```

Each state-changing command displays the previous registration, prompts for the exact word `APPLY`, saves a timestamped `~/.codex/config.toml` backup in `~/.codex/jarvis-backups/`, then replaces only the Hypruse MCP entry. If re-registration fails, the script attempts to restore the original file. The new registration uses documented protective flags, but **any customized options in the previous Hypruse MCP entry are overwritten**. Read the printed configuration before approving.

## Security and privacy

Allowing a chat application exposes its window to automation, including private messages. The agent may be able to navigate chats, type or click; restrict its tasks carefully. Approval to select a chat does **not** authorize sending messages, deleting data, forwarding content or modifying account settings.

The `kitty` class includes terminals, where untrusted GUI input can be especially powerful. To allow Telegram *without* kitty, use:

```bash
bash scripts/hypruse-access.sh allow org.telegram.desktop
```

Scope is an application-class allowlist; it does **not** grant global mouse access and does not override an authentication guard or a locked session. Screenshot and desktop observation capabilities may remain broader than action scope; hide sensitive content before an AI desktop session.

**Do not let an AI agent silently change its own confinement profile.** Run the command manually after deciding which applications it should be able to control.

## Troubleshooting

- `outside the agent's confinement scope`: verify current `codex mcp get hypruse`, correct class name, and restart Codex. Do not route around a refusal with an alternative tool.
- `Hypruse is not registered`: install JARVIS on Hyprland or register Hypruse first.
- `HYPRUSE_STRICT` refusal: the human may have changed pointer/focus; re-observe, do not bypass the seat guard.
- `AUTH_GUARD` refusal: do not automate credentials or permission dialogs.

Upstream reference: [Hypruse README — Optional confinement](https://github.com/IlyasKhallouki/hypruse#optional-confinement).
