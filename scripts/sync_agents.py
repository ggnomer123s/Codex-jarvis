#!/usr/bin/env python3
"""Synchronize only the TIGO-owned AGENTS.md marker block; preserve user text."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

START = "<!-- TIGO-CODEX RULES START -->"
END = "<!-- TIGO-CODEX RULES END -->"


def sync(target: Path, template: Path) -> bool:
    replacement = template.read_text(encoding="utf-8").strip() + "\n"
    if replacement.count(START) != 1 or replacement.count(END) != 1:
        raise ValueError("Template must contain exactly one complete managed block")
    if replacement.index(START) > replacement.index(END):
        raise ValueError("Malformed template marker order")
    if target.is_symlink():
        raise ValueError("Refusing to replace a symlinked AGENTS.md")
    original = target.read_text(encoding="utf-8") if target.exists() else ""
    # Validate every owned block before writing, including pre-rename markers.
    for brand in ('TIGO', 'JARVIS'):
        for kind in ('RULES', 'MEMORY'):
            begin, end = (f'<!-- {brand}-CODEX {kind} {edge} -->' for edge in ('START', 'END'))
            if original.count(begin) != original.count(end) or original.count(begin) > 1:
                raise ValueError('Unpaired or duplicate managed markers; refusing to overwrite')
            if begin in original and original.index(begin) > original.index(end):
                raise ValueError('Malformed managed marker order')
    updated = original
    for kind in ('RULES', 'MEMORY'):
        begin, end = (f'<!-- TIGO-CODEX {kind} {edge} -->' for edge in ('START', 'END'))
        if begin not in replacement:
            continue
        block = replacement[replacement.index(begin):replacement.index(end) + len(end)]
        found = False
        for brand in ('TIGO', 'JARVIS'):
            old_begin, old_end = (f'<!-- {brand}-CODEX {kind} {edge} -->' for edge in ('START', 'END'))
            if old_begin in updated:
                left, right = updated.index(old_begin), updated.index(old_end) + len(old_end)
                updated = updated[:left] + ('' if found else block) + updated[right:]
                found = True
        if not found:
            updated = updated.rstrip('\n') + ('\n\n' if updated else '') + block + '\n'
    if updated == original:
        print("[ok] AGENTS.md managed rules are current")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        backup = target.with_name(target.name + ".backup." +
                                  datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        # Never overwrite another backup from this second.
        idx = 0
        while backup.exists():
            idx += 1
            backup = backup.with_name(backup.name + f"-{idx}")
        shutil.copy2(target, backup)
        print(f"[backup] {backup}")
    fd, tmp = tempfile.mkstemp(prefix=".tigo-agents-", dir=target.parent)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(fd, stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(f"[updated] {target}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 sync_agents.py TARGET_AGENTS TEMPLATE")
    try:
        sync(Path(sys.argv[1]).expanduser(), Path(sys.argv[2]).expanduser())
    except (OSError, ValueError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(1)
