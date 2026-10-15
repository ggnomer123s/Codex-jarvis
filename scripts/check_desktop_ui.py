#!/usr/bin/env python3
"""Run simulated desktop tests and expose failures in GitHub's public summary.

Native Qt crashes can bypass unittest results, so capture the child process too.
The suite uses fixture prompts/audio and never runs authenticated desktop tasks.
"""
import os
import subprocess
import sys


def main():
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "gui/tests", "-v"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            env={**os.environ, "PYTHONFAULTHANDLER": "1"})
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode and os.environ.get("GITHUB_ACTIONS") == "true":
        # Public annotation views can truncate long messages from the end.
        # Keep the return code and final traceback within the visible limit.
        detail = f"Desktop child exit code: {result.returncode}\n" + (result.stdout + result.stderr)[-3400:]
        detail = detail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::error title=Desktop process and QML tests::" + detail, flush=True)
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
