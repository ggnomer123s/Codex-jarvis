#!/usr/bin/env bash
# JARVIS-CODEX MANAGED - compatibility installer; one shared Codex profile.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
  echo 'Installs JARVIS in the current Codex profile. Full Access defaults on; GUI settings can disable it.'
  exit 0
fi
if [[ $# -eq 2 && "$1" == --acknowledgement ]]; then shift 2; fi
exec bash "$ROOT/scripts/install-linux.sh" "$@"
