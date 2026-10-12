#!/usr/bin/env python3
"""JARVIS Memory: opt-in local notes about user-confirmed troubleshooting fixes.

Only explicit CLI actions write data. No AI calls, screenshots, or telemetry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

BASE = Path(os.environ.get(
    "JARVIS_MEMORY_DIR",
    str((Path(os.environ["LOCALAPPDATA"]) / "jarvis-codex" / "memory")
        if os.name == "nt" else
        (Path.home() / ".local" / "share" / "jarvis-codex" / "memory"))
)).expanduser()
FILE = BASE / "confirmed-fixes.json"


def load():
    if not FILE.exists():
        return []
    with FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Invalid memory database format: expected a JSON array")
    return data


def save(data):
    BASE.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        BASE.chmod(0o700)
    fd, tmp = tempfile.mkstemp(dir=BASE, prefix=".memory-", suffix=".tmp")
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, FILE)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def add(_args):
    print("Save a CONFIRMED fix only. Avoid passwords, API keys, tokens and private logs.")
    try:
        issue = input("Problem/symptom: ").strip()
        fix = input("Verified solution: ").strip()
        context = input("OS/app/version context (optional): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 1
    if not issue or not fix:
        print("A problem and verified solution are required.", file=sys.stderr)
        return 1
    summary = f"Problem: {issue}\nSolution: {fix}\nContext: {context or '(none)'}"
    print("\nReview before saving:\n" + summary)
    if input("Save this verified fix locally? Type YES: ").strip() != "YES":
        print("Not saved.")
        return 1
    records = load()
    item = {
        "id": uuid.uuid4().hex[:12],
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "issue": issue,
        "fix": fix,
        "context": context,
        "verified_by_user": True,
    }
    records.append(item)
    save(records)
    print(f"Saved locally with ID {item['id']}. Database: {FILE}")
    return 0


def show_item(item):
    print(f"[{item['id']}] {item['issue']}\n"
          f"  Fix: {item['fix']}\n"
          f"  Context: {item.get('context', '')}\n"
          f"  Confirmed: {item.get('created_utc', '')}\n")


def show(args):
    records = load()
    if args.operation == "search":
        query = " ".join(args.terms).casefold().strip()
        if not query:
            print("Usage: jarvis memory search <keyword>", file=sys.stderr)
            return 2
        terms = query.split()
        records = [
            r for r in records
            if all(term in (" ".join(str(r.get(k, "")) for k in ("issue", "fix", "context"))).casefold()
                   for term in terms)
        ]
    if not records:
        print("No matching confirmed fixes.")
        return 0
    for item in records[-40:]:
        show_item(item)
    return 0


def forget(args):
    records = load()
    target = [x for x in records if x.get("id") == args.id]
    if not target:
        print("Unknown memory ID.", file=sys.stderr)
        return 1
    show_item(target[0])
    if input("Permanently delete this note? Type DELETE: ").strip() != "DELETE":
        print("Not deleted.")
        return 1
    save([x for x in records if x.get("id") != args.id])
    print("Deleted locally.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="JARVIS local, opt-in troubleshooting memory")
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("add", help="Interactively save a verified solution")
    sub.add_parser("list", help="Show saved solutions")
    search = sub.add_parser("search", help="Search saved solutions")
    search.add_argument("terms", nargs="*")
    delete = sub.add_parser("forget", help="Delete a memory note by ID")
    delete.add_argument("id")
    args = parser.parse_args()
    try:
        return {"add": add, "list": show, "search": show, "forget": forget}[args.operation](args)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 1
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Memory error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
