#!/usr/bin/env bash
# TIGO-CODEX MANAGED - install a menu entry for this checkout's GUI
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for tool in uv uvx python3 codex; do command -v "$tool" >/dev/null || { echo "Missing $tool; see docs/install-desktop.md." >&2; exit 1; }; done
uv sync --project "$ROOT/gui" --frozen --extra voice
if [[ -n "${WAYLAND_DISPLAY:-}" ]] && ! /usr/bin/python3 -c 'from ctypes import CDLL; CDLL("libgtk4-layer-shell.so.0"); import cairo, gi; gi.require_foreign("cairo"); gi.require_version("Gtk", "4.0"); gi.require_version("Gtk4LayerShell", "1.0")' 2>/dev/null; then
  echo '[notice] The Wayland screen indicator needs GTK4, PyGObject, Pycairo/GI Cairo and gtk4-layer-shell for /usr/bin/python3. See docs/install-desktop.md; other features remain available.'
fi
echo 'Neural voices are included. Models download on first speech use; see docs/speech-output.md.'
echo 'Updating the shared Codex profile and desktop backend.'
bash "$ROOT/scripts/install-linux.sh"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import shlex
import sys
root = Path(sys.argv[1])
home = Path.home()
launcher = home / '.local/bin/tigo-gui'
desktop = home / '.local/share/applications/tigo-gui.desktop'
for target in (launcher, desktop):
    if target.is_symlink() or (target.exists() and 'TIGO-CODEX MANAGED' not in target.read_text()):
        raise SystemExit(f'Refusing to replace unrelated file: {target}')
launcher.parent.mkdir(parents=True, exist_ok=True)
desktop.parent.mkdir(parents=True, exist_ok=True)
launcher.write_text('#!/usr/bin/env bash\n# TIGO-CODEX MANAGED\nexport PATH="$HOME/.local/bin:$PATH"\nexec bash ' + shlex.quote(str(root / 'scripts/tigo-gui-linux.sh')) + ' "$@"\n')
launcher.chmod(0o755)
def desktop_quote(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'
desktop.write_text('[Desktop Entry]\n# TIGO-CODEX MANAGED\nType=Application\nName=Tigo\nComment=Personal intelligence powered by Codex\nExec=' + desktop_quote(str(launcher)) + '\nIcon=' + str(root / 'gui/tigo_gui/ui/icon.svg') + '\nTerminal=false\nCategories=Utility;Development;\nStartupWMClass=Tigo\n')
print('Installed Tigo in your application menu. Full Access is on by default; change it in Preferences > Access. Keep this checkout in place.')
PY
if [[ -f "$ROOT/scripts/migrate_brand.py" ]]; then
  python3 "$ROOT/scripts/migrate_brand.py"
fi
