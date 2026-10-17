#!/usr/bin/env bash
# TIGO-CODEX MANAGED - dependency-aware installer for supported Linux families
set -Eeuo pipefail

fail() { echo "[error] $*" >&2; exit 1; }

prepare_checkout() {
    local repo_dir="$1" origin branch expected="${TIGO_UPDATE_EXPECTED_REV:-}"
    if [[ -e "$repo_dir/.git" ]]; then
        [[ "$(git -C "$repo_dir" rev-parse --show-toplevel)" == "$repo_dir" ]] || fail 'Use the checkout root.'
        origin="$(git -C "$repo_dir" remote get-url origin)"
        case "$origin" in
            https://github.com/ggnomer123s/Codex-jarvis|https://github.com/ggnomer123s/Codex-jarvis.git|git@github.com:ggnomer123s/Codex-jarvis.git) ;;
            *) fail 'The checkout origin is not the Tigo repository.' ;;
        esac
        branch="$(git -C "$repo_dir" symbolic-ref --quiet --short HEAD)" || fail 'Detached checkout; select main manually.'
        [[ "$branch" == main ]] || fail 'Save your work and select main manually.'
        [[ -z "$(git -C "$repo_dir" status --porcelain)" ]] || fail 'Local changes found. Save or commit them first; no files were discarded.'
        if [[ -n "$expected" ]]; then
            [[ "$expected" =~ ^[0-9a-f]{40}$ ]] || fail 'Invalid reviewed update revision.'
            git -C "$repo_dir" fetch --no-tags origin main
            [[ "$(git -C "$repo_dir" rev-parse FETCH_HEAD)" == "$expected" ]] || fail 'The update changed. Check again in Tigo.'
            git -C "$repo_dir" merge --ff-only "$expected"
        else
            git -C "$repo_dir" pull --ff-only origin main
        fi
    else
        [[ -z "$expected" ]] || fail 'The reviewed checkout is missing.'
        git clone --branch main https://github.com/ggnomer123s/Codex-jarvis.git "$repo_dir"
    fi
}

install_node() {
    local node_root="${XDG_DATA_HOME:-$HOME/.local/share}/tigo/runtime/node"
    export PATH="$node_root/bin:$PATH"
    if command -v node >/dev/null && command -v npm >/dev/null && node -e 'process.exit(Number(process.versions.node.split(".")[0])>=22?0:1)'; then
        return
    fi
    local stage line digest archive
    stage="$(mktemp -d)"
    curl --proto '=https' --tlsv1.2 -fLsS https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt -o "$stage/SHASUMS256.txt"
    line="$(awk '$2 ~ /^node-v22\.[0-9]+\.[0-9]+-linux-x64\.tar\.xz$/ {print;exit}' "$stage/SHASUMS256.txt")"
    read -r digest archive <<< "$line"
    [[ "$digest" =~ ^[0-9a-f]{64}$ && "$archive" =~ ^node-v22\.[0-9]+\.[0-9]+-linux-x64\.tar\.xz$ ]] || fail 'No valid Node 22 archive/checksum was found.'
    curl --proto '=https' --tlsv1.2 -fLsS "https://nodejs.org/dist/latest-v22.x/$archive" -o "$stage/$archive"
    (cd "$stage" && printf '%s  %s\n' "$digest" "$archive" | sha256sum --check --status) || fail 'Node checksum mismatch.'
    mkdir -p "$(dirname "$node_root")"
    tar -xJf "$stage/$archive" -C "$stage"
    # Replace only Tigo's private runtime directory, never system/user node links.
    if [[ -e "$node_root" ]]; then
        [[ -f "$node_root/.tigo-runtime" ]] || fail 'An unmanaged Node runtime already exists at the Tigo path.'
        mv "$node_root" "$stage/previous-node"
    fi
    mv "$stage/${archive%.tar.xz}" "$node_root"
    touch "$node_root/.tigo-runtime"
    rm -rf -- "$stage"
}

system_packages() {
    if command -v apt-get >/dev/null; then
        sudo apt-get update
        sudo apt-get install -y git curl python3 ca-certificates xz-utils libportaudio2 libpulse0 libegl1 libopengl0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 xdotool wmctrl maim grim wtype python3-gi gir1.2-gtk-4.0
        if apt-cache show libgtk4-layer-shell0 >/dev/null 2>&1; then
            sudo apt-get install -y libgtk4-layer-shell0 gir1.2-gtk4layershell-1.0
        else
            echo '[notice] This release lacks GTK4 layer-shell packages. The Wayland indicator may be unavailable; see the installation guide.'
        fi
    elif command -v dnf >/dev/null; then
        sudo dnf install -y git curl python3 xz portaudio pulseaudio-libs mesa-libEGL mesa-libGL libxcb libxkbcommon-x11 xcb-util-cursor xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil xdotool wmctrl maim grim wtype gtk4 gtk4-layer-shell python3-gobject
    elif command -v zypper >/dev/null; then
        sudo zypper --non-interactive install git curl python3 xz libportaudio2 libpulse0 libEGL1 libOpenGL0 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 xdotool wmctrl maim grim wtype
        echo '[notice] For a Wayland screen indicator install the distribution GTK4/PyGObject/Gtk4LayerShell typelibs; see the installation guide.'
    else
        fail 'Supported families: Arch/CachyOS, Debian/Ubuntu/Mint, Fedora, openSUSE. See docs/install-desktop.md for manual setup.'
    fi
}

main() {
    (( EUID != 0 )) || fail 'Run as your ordinary desktop user, not with sudo.'
    [[ "$(uname -m)" == x86_64 ]] || fail 'This installer currently targets x86-64 desktop Linux.'
    (( $# <= 1 )) || fail 'Usage: bash update-linux.sh [checkout-path]'
    if command -v pacman >/dev/null; then
        exec bash "$(dirname "${BASH_SOURCE[0]}")/update-cachyos.sh" "$@"
    fi
    command -v sudo >/dev/null || fail 'sudo is required for system packages.'
    command -v getconf >/dev/null && getconf GNU_LIBC_VERSION | awk '{split($2,v,"."); exit !(v[1]>2 || v[1]==2 && v[2]>=34)}' || fail 'A glibc 2.34+ distribution is required.'
    local repo_dir login_output login_code=0 uv_stage
    repo_dir="$(realpath -m -- "${1:-$HOME/Tigo}")"
    echo 'Quit Tigo first. Native package-manager/password prompts remain in this terminal.'
    system_packages
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv >/dev/null || ! command -v uvx >/dev/null; then
        uv_stage="$(mktemp)"
        curl --proto '=https' --tlsv1.2 -fLsS https://astral.sh/uv/install.sh -o "$uv_stage"
        sh "$uv_stage"
        rm -f -- "$uv_stage"
    fi
    install_node
    if ! command -v codex >/dev/null || ! codex app-server --help >/dev/null 2>&1; then
        npm install --global --prefix "$HOME/.local" @openai/codex@latest
        hash -r
    fi
    codex app-server --help >/dev/null
    prepare_checkout "$repo_dir"
    uv python install 3.12
    uv sync --project "$repo_dir/gui" --frozen --extra voice --python 3.12
    bash "$repo_dir/scripts/install-gui-linux.sh"
    QT_QPA_PLATFORM=offscreen uv run --project "$repo_dir/gui" --frozen --extra voice python -c 'import PySide6.QtQuick, sounddevice, faster_whisper, sherpa_onnx, edge_tts, av'
    login_output="$(codex login status 2>&1)" || login_code=$?
    if (( login_code != 0 )); then
        [[ "${login_output,,}" == *'not logged in'* ]] || fail 'Could not verify the existing Codex login. Run codex login status; no replacement login was attempted.'
        codex login --device-auth
    fi
    uv run --project "$repo_dir/gui" --frozen --extra voice python -m tigo_gui.speech_models
    echo 'Tigo is ready. Your settings, history and existing account were retained.'
    [[ "${TIGO_UPDATE_NO_LAUNCH:-}" == 1 ]] || exec "$HOME/.local/bin/tigo-gui"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
