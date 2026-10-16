#!/usr/bin/env bash
# TIGO-CODEX MANAGED — explicit per-app Hypruse confinement profiles
set -Eeuo pipefail

usage() {
  cat <<'HELP'
Usage: tigo access status
       tigo access all
       tigo access telegram
       tigo access allow <window-class> [more classes...]
       tigo access restricted

Hyprland/Wayland only:
  status      Show the existing Hypruse MCP configuration
  all         Allow ALL desktop windows; turn off red Hypruse marking
  telegram    Allow pre-existing Telegram and kitty windows
  allow       Explicitly allow selected Hyprland window classes
  restricted  Return to Hypruse-launched windows only

This replaces the current Hypruse MCP registration after confirmation.
A timestamped backup of ~/.codex/config.toml is saved locally.
Use 'hyprctl clients -j' to inspect the class of a window.
After switching access, restart the interactive Codex/Tigo session.
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
  all)
    scope=""
    mode="ALL desktop windows" ;;
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
  echo "[error] Hypruse is not registered in Codex. Install Tigo first." >&2
  exit 1
fi

echo "Current Hypruse registration:"
codex mcp get hypruse
echo
if [[ -n "$scope" ]]; then
  echo "Requested HYPRUSE_CONFINE=$scope"
else
  echo "Requested: no HYPRUSE_CONFINE (all windows allowed)"
fi
echo "HYPRUSE_MARK=0 (no new red borders or screenshot notifications)."
echo "The existing MCP entry (including any custom flags) will be replaced."
echo "The new registration retains STRICT, AUTH_GUARD, JOURNAL; marking is disabled."
echo "Allowing more windows may expose private chats and documents to the agent."
echo "This is NOT equivalent to granting permissions in Codex."
read -r -p "Type APPLY to save this profile: " confirmation
if [[ "$confirmation" != "APPLY" ]]; then
  echo "[info] Nothing changed."
  exit 0
fi

config="${CODEX_HOME:-$HOME/.codex}/config.toml"
if [[ ! -f "$config" ]]; then
  echo "[error] Expected config file not found at $config; no changes made." >&2
  exit 1
fi
backups="$HOME/.codex/tigo-backups"
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
mcp_args=(
  --env HYPRUSE_STRICT=1
  --env HYPRUSE_AUTH_GUARD=strict
  --env HYPRUSE_JOURNAL=1
  --env HYPRUSE_MARK=0
)
if [[ -n "$scope" ]]; then
  mcp_args=(--env "HYPRUSE_CONFINE=$scope" "${mcp_args[@]}")
fi
if ! codex mcp add hypruse "${mcp_args[@]}" -- uvx hypruse; then
  rollback
  exit 1
fi

if [[ -n "$scope" ]]; then
  echo "[ok] Hypruse confinement profile is now: $scope"
else
  echo '[ok] Hypruse now permits all existing desktop windows.'
fi
echo '[ok] HYPRUSE_MARK disabled for new Hypruse sessions.'
echo "[ok] Configuration backup: $backup"
echo "[next] Close all old Codex sessions, then run: tigo"
echo '[info] Old red border rules may persist until Hyprland config reload.'
read -r -p 'Reload Hyprland configuration now to clear old red borders? Type RELOAD: ' reload_choice
if [[ "$reload_choice" == RELOAD ]]; then
  if hyprctl reload; then
    echo '[ok] Requested Hyprland config reload.'
  else
    echo '[warn] Reload failed; run hyprctl reload manually when ready.' >&2
  fi
fi
echo '[safety] GUI scope changed; Codex approvals and OS privileges are unchanged.'
