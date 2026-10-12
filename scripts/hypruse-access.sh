#!/usr/bin/env bash
# JARVIS-CODEX MANAGED — explicit per-app Hypruse confinement profiles
set -Eeuo pipefail

usage() {
  cat <<'HELP'
Usage: jarvis access status
       jarvis access telegram
       jarvis access allow <window-class> [more classes...]
       jarvis access restricted

Hyprland/Wayland only:
  status      Show the existing Hypruse MCP configuration
  telegram    Allow pre-existing Telegram and kitty windows
  allow       Explicitly allow selected Hyprland window classes
  restricted  Return to Hypruse-launched windows only

This replaces the current Hypruse MCP registration after confirmation.
A timestamped backup of ~/.codex/config.toml is saved locally.
Use 'hyprctl clients -j' to inspect the class of a window.
After switching access, restart the interactive Codex/JARVIS session.
HELP
}

if [[ $# -eq 0 || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

command -v codex >/dev/null || { echo "[error] Codex CLI not found." >&2; exit 1; }
if [[ "${XDG_SESSION_TYPE:-}" != "wayland" ]] || [[ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" && "${XDG_CURRENT_DESKTOP:-}" != *Hyprland* ]]; then
  echo "[error] Hypruse access profiles require a live Hyprland/Wayland session." >&2
  exit 1
fi

action="$1"
case "$action" in
  status)
    exec codex mcp get hypruse ;;
  restricted)
    scope="launched" ;;
  telegram)
    # Explicit opt-in to pre-existing windows in these classes only.
    scope="class:org.telegram.desktop,kitty" ;;
  allow)
    shift
    if [[ $# -lt 1 || $# -gt 12 ]]; then
      echo "[error] Provide 1 to 12 window classes (for example: org.telegram.desktop kitty)." >&2
      exit 2
    fi
    for class in "$@"; do
      if [[ ! "$class" =~ ^[a-zA-Z0-9_.-]{1,100}$ ]]; then
        echo "[error] Invalid window class: $class" >&2
        exit 2
      fi
    done
    scope="class:$(IFS=,; echo "$*")" ;;
  *)
    usage >&2
    exit 2 ;;
esac

if ! codex mcp get hypruse >/dev/null 2>&1; then
  echo "[error] Hypruse is not registered in Codex. Install JARVIS first." >&2
  exit 1
fi

echo "Current Hypruse registration:"
codex mcp get hypruse
echo
echo "Requested HYPRUSE_CONFINE=$scope"
echo "The existing MCP entry (including any custom flags) will be replaced."
echo "The new registration retains STRICT, AUTH_GUARD, JOURNAL and MARK."
echo "Telegram/kitty may show private content and allow significant GUI actions."
echo "This is NOT equivalent to granting permissions in Codex."
read -r -p "Type APPLY to save this profile: " confirmation
if [[ "$confirmation" != "APPLY" ]]; then
  echo "[info] Nothing changed."
  exit 0
fi

config="$HOME/.codex/config.toml"
if [[ ! -f "$config" ]]; then
  echo "[error] Expected config file not found at $config; no changes made." >&2
  exit 1
fi
backups="$HOME/.codex/jarvis-backups"
mkdir -p "$backups"
chmod 700 "$backups"
backup="$backups/config-$(date +%Y%m%d-%H%M%S)-$$.toml"
cp -p -- "$config" "$backup"
chmod 600 "$backup"

rollback() {
  cp -p -- "$backup" "$config"
  echo "[error] Hypruse update failed; restored the original Codex config from $backup" >&2
}
if ! codex mcp remove hypruse; then
  rollback
  exit 1
fi
if ! codex mcp add hypruse \
  --env "HYPRUSE_CONFINE=$scope" \
  --env HYPRUSE_STRICT=1 \
  --env HYPRUSE_AUTH_GUARD=strict \
  --env HYPRUSE_JOURNAL=1 \
  --env HYPRUSE_MARK=1 \
  -- uvx hypruse; then
  rollback
  exit 1
fi

echo "[ok] Hypruse confinement profile is now: $scope"
echo "[ok] Configuration backup: $backup"
echo "[next] Close existing Codex sessions, then run: jarvis"
echo "[safety] This changes GUI access scope, NOT per-action approval policy."
