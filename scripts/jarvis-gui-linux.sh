#!/usr/bin/env bash
# JARVIS-CODEX MANAGED - native desktop application
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v uv >/dev/null || { echo 'Install uv first; see docs/desktop-app.md.' >&2; exit 1; }
extras=(--extra voice)
if [[ "${1:-}" == --no-voice ]]; then extras=(); shift; fi
exec uv run --project "$ROOT/gui" --frozen "${extras[@]}" jarvis-gui "$@"
