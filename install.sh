#!/usr/bin/env bash
# TIGO-CODEX MANAGED - single Linux install/update entry point
set -Eeuo pipefail
command -v curl >/dev/null || { echo 'Install curl with your system package manager, then retry.' >&2; exit 1; }
stage="$(mktemp -d)"
trap 'rm -rf -- "$stage"' EXIT
for script in update-linux.sh update-cachyos.sh; do
    curl --proto '=https' --tlsv1.2 -fLsS "https://raw.githubusercontent.com/ggnomer123s/Codex-jarvis/main/scripts/$script" -o "$stage/$script"
done
bash "$stage/update-linux.sh" "$@"
