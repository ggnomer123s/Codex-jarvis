#!/usr/bin/env bash
# JARVIS-CODEX MANAGED — optional, unsandboxed user-level Codex profile
set -Eeuo pipefail

if [[ "$EUID" -eq 0 ]]; then
  echo '[error] Do not run JARVIS Full Access as root.' >&2
  exit 1
fi
export CODEX_HOME="$HOME/.local/share/jarvis-codex/full-codex-home"

usage() {
  cat <<'HELP'
Usage: jarvis-full [fast|normal|deep|login|status|help]
       jarvis full [fast|normal|deep|login|status|help]

fast     Full Access with low reasoning effort (responsive GUI actions)
normal   Full Access with the profile's configured default reasoning
deep     Full Access with high reasoning effort (complex work)
login    Sign in to the independent CODEX_HOME profile
status   Inspect login and MCP registrations for this profile
help     Show this help

All execution modes are unsandboxed and skip Codex approval prompts.
This is NOT root access or permission to bypass app/OS authentication.
HELP
}

if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi

mode="${1:-normal}"
case "$mode" in
  -h|--help|help)
    usage
    exit 0 ;;
  login)
    exec codex login ;;
  status)
    printf 'Separate CODEX_HOME: %s\n' "$CODEX_HOME"
    codex login status || true
    exec codex mcp list ;;
  fast)
    reasoning='low' ;;
  normal|start)
    reasoning='' ;;
  deep)
    reasoning='high' ;;
  *)
    usage >&2
    exit 2 ;;
esac

printf 'JARVIS FULL ACCESS (%s): unsandboxed, no Codex command approvals. Ctrl+C to stop.\n' "$mode" >&2

# Deliberately do NOT inject a startup task: go straight to interactive Codex.
# Full profile instructions live in its own CODEX_HOME/AGENTS.md, and the
# normal jarvis launcher/configuration is untouched.
args=(--dangerously-bypass-approvals-and-sandbox)
if [[ -n "$reasoning" ]]; then
  args+=(--config "model_reasoning_effort=$reasoning")
fi
exec codex "${args[@]}"
