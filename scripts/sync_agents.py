#!/usr/bin/env python3
"""Synchronize only the JARVIS-owned AGENTS.md marker block; preserve user text."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

START = "<!-- JARVIS-CODEX RULES START -->"
END = "<!-- JARVIS-CODEX RULES END -->"


def sync(target: Path, template: Path) -> bool:
    replacement = template.read_text(encoding="utf-8").strip() + "\n"
    if replacement.count(START) != 1 or replacement.count(END) != 1:
        raise ValueError("Template must contain exactly one complete managed block")
    if replacement.index(START) > replacement.index(END):
        raise ValueError("Malformed template marker order")
    if target.is_symlink():
        raise ValueError("Refusing to replace a symlinked AGENTS.md")
    original = target.read_text(encoding="utf-8") if target.exists() else ""
    if original.count(START) != original.count(END):
        raise ValueError("Unpaired JARVIS markers in AGENTS.md; refusing to overwrite")
    if original.count(START) > 1:
        raise ValueError("Duplicate JARVIS blocks in AGENTS.md; refusing to overwrite")
    if START in original:
        left = original.index(START)
        right = original.index(END) + len(END)
        updated = original[:left] + replacement.rstrip("\n") + original[right:]
    else:
        updated = original.rstrip("\n") + ("\n\n" if original else "") + replacement
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
    fd, tmp = tempfile.mkstemp(prefix=".jarvis-agents-", dir=target.parent)
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
