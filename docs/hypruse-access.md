# Hypruse desktop access profiles

Hypruse enforces a GUI **confinement scope** separately from Codex shell permissions. Codex Full Access does not automatically change this setting.

## Access ALL windows (opt-in)

If Spotify or Firefox is blocked with `outside the agent's confinement scope`, you can explicitly remove the window class filter:

```bash
# From the Codex-jarvis repository:
git pull --ff-only
bash scripts/hypruse-access.sh all
```

Read the displayed current MCP configuration and type `APPLY`. Then quit and restart Codex/JARVIS. The updated registration has **no `HYPRUSE_CONFINE` variable**, so desktop input is no longer limited to Telegram/kitty or windows opened through Hypruse. This is not an OS/root privilege change.

This profile sets `HYPRUSE_MARK=0` to stop tagging and highlighting newly launched windows. **Existing red outlines** may remain until a Hyprland configuration reload. The script offers to run `hyprctl reload` only if you explicitly type `RELOAD`. This reload can reapply personal Hyprland settings.

```text
HYPRUSE_CONFINE  (omitted: all windows)
HYPRUSE_MARK=0
HYPRUSE_STRICT=1
HYPRUSE_AUTH_GUARD=strict
HYPRUSE_JOURNAL=1
```

Security note: **All windows** means Telegram, Spotify, Firefox, terminals, file managers and other existing applications can receive GUI input. The agent may see private data and can cause state changes. Its instructions should still require authorization before sending, deleting or publishing. `HYPRUSE_STRICT` may pause actions when the human moves the cursor or focus, and `HYPRUSE_AUTH_GUARD` refuses authentication dialogs.

## Alternative restricted profiles

```bash
bash scripts/hypruse-access.sh status
bash scripts/hypruse-access.sh telegram
bash scripts/hypruse-access.sh allow org.telegram.desktop firefox Spotify
bash scripts/hypruse-access.sh restricted
```

- `status` shows the current MCP configuration.
- `telegram` enables the named Telegram/kitty classes only.
- `allow` accepts a list of application classes obtained from `hyprctl clients -j`.
- `restricted` returns to `HYPRUSE_CONFINE=launched`.

Switching profiles replaces the old MCP registration after explicit confirmation; a timestamped backup of `~/.codex/config.toml` is saved under `~/.codex/jarvis-backups/`. Previous custom Hypruse MCP settings may be replaced; review before approving.

The marking flag is now disabled for changed access profiles. If a red border persists after reloading Hyprland, inspect your personal configuration for a manual `hypruse-owned` border rule; do not blindly delete unrelated rules.

## Troubleshooting

- **Scope error still appears:** restart every old Codex/JARVIS process; old processes keep old MCP startup settings. Run `codex mcp get hypruse` from a new terminal.
- **New red border persists:** check `HYPRUSE_MARK=0`, then `hyprctl reload` and inspect custom Hyprland rules if needed.
- **Seat moved since last acted:** this is `HYPRUSE_STRICT`, a different check from confinement. Reobserve desktop after focus changes.
- **Auth dialog refused:** `HYPRUSE_AUTH_GUARD` is still active; do not bypass credential prompts.
- **Unexpected effects after reloading Hyprland:** restore your user config from its normal backup and report the behavior.

Sources: [Hypruse upstream security and confinement documentation](https://github.com/IlyasKhallouki/hypruse#optional-confinement).