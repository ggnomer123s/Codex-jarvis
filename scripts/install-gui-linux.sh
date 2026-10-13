#!/usr/bin/env bash
# JARVIS-CODEX MANAGED - install a menu entry for this checkout's GUI
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for tool in uv python3; do command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 1; }; done
uv sync --project "$ROOT/gui" --frozen --extra voice
python3 - "$ROOT" <<'PY'
from pathlib import Path
import shlex
import sys
root = Path(sys.argv[1])
home = Path.home()
launcher = home / '.local/bin/jarvis-gui'
desktop = home / '.local/share/applications/jarvis-gui.desktop'
for target in (launcher, desktop):
    if target.is_symlink() or (target.exists() and 'JARVIS-CODEX MANAGED' not in target.read_text()):
        raise SystemExit(f'Refusing to replace unrelated file: {target}')
launcher.parent.mkdir(parents=True, exist_ok=True)
desktop.parent.mkdir(parents=True, exist_ok=True)
launcher.write_text('#!/usr/bin/env bash\n# JARVIS-CODEX MANAGED\nexport PATH="$HOME/.local/bin:$PATH"\nexec bash ' + shlex.quote(str(root / 'scripts/jarvis-gui-linux.sh')) + ' "$@"\n')
launcher.chmod(0o755)
def desktop_quote(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'
desktop.write_text('[Desktop Entry]\n# JARVIS-CODEX MANAGED\nType=Application\nName=JARVIS\nComment=Personal intelligence powered by Codex\nExec=' + desktop_quote(str(launcher)) + '\nIcon=' + str(root / 'gui/jarvis_gui/ui/icon.svg') + '\nTerminal=false\nCategories=Utility;Development;\nStartupWMClass=JARVIS\n')
print('Installed JARVIS in your application menu. Keep this checkout in place.')
PY
