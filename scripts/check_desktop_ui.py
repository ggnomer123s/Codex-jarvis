#!/usr/bin/env python3
"""Run simulated desktop tests and expose failures in GitHub's public summary.

Native Qt crashes can bypass unittest results, so capture the child process too.
The suite uses fixture prompts/audio and never runs authenticated desktop tasks.
"""
import os
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', action='store_true', help='Run isolated updater fixtures instead of Qt tests')
    args = parser.parse_args()
    suite = ['-s', 'tests', '-p', 'test_update_bootstrap.py'] if args.bootstrap else ['-s', 'gui/tests']
    label = 'Updater fixtures' if args.bootstrap else 'Desktop process and QML tests'
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", *suite, "-v"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            env={**os.environ, "PYTHONFAULTHANDLER": "1"})
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode and os.environ.get("GITHUB_ACTIONS") == "true":
        # Public annotation views can truncate long messages from the end.
        # Keep the return code and final traceback within the visible limit.
        detail = f"{label} child exit code: {result.returncode}\n" + (result.stdout + result.stderr)[-3400:]
        detail = detail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::error title=" + label + "::" + detail, flush=True)
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
