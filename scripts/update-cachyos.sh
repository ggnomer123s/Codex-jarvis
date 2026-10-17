#!/usr/bin/env bash
# TIGO-CODEX MANAGED - dependency-aware CachyOS/Arch bootstrap and update
set -Eeuo pipefail

fail() { echo "[error] $*" >&2; exit 1; }
prepare_checkout() {
    local repo_dir="$1" origin branch
    if [[ -e "$repo_dir/.git" ]]; then
        [[ "$(git -C "$repo_dir" rev-parse --show-toplevel)" == "$repo_dir" ]] || fail 'The target is not the root of its checkout.'
        origin="$(git -C "$repo_dir" remote get-url origin)"
        case "$origin" in
            https://github.com/ggnomer123s/Codex-jarvis|https://github.com/ggnomer123s/Codex-jarvis.git|git@github.com:ggnomer123s/Codex-jarvis.git) ;;
            *) fail 'The existing checkout origin is not the Tigo repository.' ;;
        esac
        branch="$(git -C "$repo_dir" symbolic-ref --quiet --short HEAD)" || fail 'Detached checkout; select main manually first.'
        [[ "$branch" == main ]] || fail 'The checkout is not on main; save your work and switch branches manually.'
        [[ -z "$(git -C "$repo_dir" status --porcelain)" ]] || fail 'Local changes found. Save or commit them before updating; no files were discarded.'
        if [[ -n "${TIGO_UPDATE_EXPECTED_REV:-}" ]]; then
            [[ "$TIGO_UPDATE_EXPECTED_REV" =~ ^[0-9a-f]{40}$ ]] || fail 'Invalid reviewed update revision.'
            git -C "$repo_dir" fetch --no-tags origin main
            [[ "$(git -C "$repo_dir" rev-parse FETCH_HEAD)" == "$TIGO_UPDATE_EXPECTED_REV" ]] || fail 'The update changed. Check again in Tigo.'
            git -C "$repo_dir" merge --ff-only "$TIGO_UPDATE_EXPECTED_REV"
        else
            git -C "$repo_dir" pull --ff-only origin main
        fi
    else
        [[ -z "${TIGO_UPDATE_EXPECTED_REV:-}" ]] || fail 'The reviewed checkout is missing.'
        git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$repo_dir"
    fi
}

main() {
    (( EUID != 0 )) || fail 'Run this script as your ordinary desktop user, not with sudo.'
    [[ "$(uname -m)" == x86_64 ]] || fail 'This bootstrap targets x86-64 desktop systems.'
    command -v pacman >/dev/null || fail 'This script is for CachyOS/Arch. See docs/install-desktop.md for other systems.'
    command -v sudo >/dev/null || fail 'sudo is required to install system dependencies.'
    (( $# <= 1 )) || fail 'Usage: bash update-cachyos.sh [checkout-path]'
    local repo_dir packages login_output login_code=0
    repo_dir="$(realpath -m -- "${1:-$HOME/Tigo}")"
    packages=(git curl uv python gtk4 gtk4-layer-shell python-gobject portaudio libpulse speech-dispatcher espeak-ng
              grim wtype xdotool wmctrl maim mesa libglvnd libxcb libxkbcommon-x11
              xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil)
    if ! command -v node >/dev/null || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
        packages+=(nodejs)
    fi
    command -v npm >/dev/null || packages+=(npm)
    echo 'Quit Tigo before updating, including its background listener.'
    echo 'Checking system dependencies with pacman. This includes the normal full rolling-release update.'
    sudo pacman -Syu --needed --noconfirm "${packages[@]}"
    export PATH="$HOME/.local/bin:$PATH"
    for tool in git uv uvx python3 node npm; do command -v "$tool" >/dev/null || fail "Missing $tool after package installation."; done
    node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)' || fail 'Your active Node manager still selects a version older than 22. Select the newly installed Node and rerun.'
    if ! command -v codex >/dev/null || ! codex app-server --help >/dev/null 2>&1; then
        npm install --global --prefix "$HOME/.local" @openai/codex@latest
        hash -r
    fi
    codex app-server --help >/dev/null
    prepare_checkout "$repo_dir"
    uv python install 3.12
    uv sync --project "$repo_dir/gui" --frozen --extra voice --python 3.12
    bash "$repo_dir/scripts/install-gui-linux.sh"
    # Import the actual CPU voice and GUI dependencies without opening the mic.
    QT_QPA_PLATFORM=offscreen uv run --project "$repo_dir/gui" --frozen --extra voice python -c \
        'import PySide6.QtQuick, sounddevice, faster_whisper, sherpa_onnx, edge_tts, av; print("GUI, CPU transcription and neural speech imports passed.")'
    login_output="$(codex login status 2>&1)" || login_code=$?
    if (( login_code != 0 )); then
        [[ "${login_output,,}" == *'not logged in'* ]] || fail 'Could not verify the existing Codex login. Run codex login status and fix that error; no replacement login was attempted.'
        echo 'Codex is not signed in. Complete device login in the existing home.'
        codex login --device-auth
    fi
    uv run --project "$repo_dir/gui" --frozen --extra voice python -m tigo_gui.speech_models
    echo 'Tigo updated. Whisper models download on first voice use; saved settings and login are reused.'
    [[ "${TIGO_UPDATE_NO_LAUNCH:-}" == 1 ]] || exec "$HOME/.local/bin/tigo-gui"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
