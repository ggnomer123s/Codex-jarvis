"""Dependency-free Codex discovery, safe launch and app-server parameters."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from .preferences import REASONING, valid_model_id


def thread_options(folder: str, access: str, model: str = "") -> dict:
    """Validated app-server options; access cannot be supplied by model output."""
    if not Path(folder).is_dir():
        raise ValueError("Choose an existing workspace folder.")
    if access not in ("read-only", "workspace-write", "full-access"):
        raise ValueError("Unknown workspace access mode.")
    if not valid_model_id(model):
        raise ValueError("Enter a valid Codex model ID, or select Codex default.")
    options = {"cwd": str(Path(folder).resolve()), "approvalPolicy": "never",
               "sandbox": "danger-full-access" if access == "full-access" else access}
    if model:
        options["model"] = model
    return options


def turn_options(thread_id: str, prompt: str, effort: str, model: str = "", attachments=None) -> dict:
    if effort not in REASONING or not valid_model_id(model):
        raise ValueError("Invalid model or reasoning setting.")
    result = {"threadId": thread_id, "input": [{"type": "text", "text": prompt}]}
    if attachments:
        for item in attachments:
            if item['kind'] == 'image':
                result['input'].append({'type': 'localImage', 'path': item['path']})
            else:
                # Structured mentions are app/plugin targets, not file uploads.
                reference = json.dumps({'name': item['name'], 'path': item['path']}, ensure_ascii=False)
                result['input'].append({'type': 'text', 'text': 'User-selected local file reference (read with available tools and current permissions):\n' + reference})
    if effort != "default":
        result["effort"] = effort
    if model:
        result["model"] = model
    return result


def find_codex() -> str | None:
    # On Windows prefer the native executable, then npm's cmd shim.
    names = ("codex.exe", "codex.cmd") if os.name == "nt" else ("codex",)
    return next((path for name in names if (path := shutil.which(name))), None)


def launch_command(executable: str, arguments: list[str], *, windows: bool | None = None) -> tuple[str, list[str]]:
    """Launch npm's Windows shim through Node, without cmd.exe interpolation."""
    windows = os.name == "nt" if windows is None else windows
    if windows and executable.lower().endswith(".cmd"):
        script = Path(executable).parent / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        node = shutil.which("node.exe") or shutil.which("node")
        if not node or not script.is_file():
            raise ValueError("Could not locate Node and the Codex npm entry point. Reinstall @openai/codex or put codex.exe on PATH.")
        return node, [str(script), *arguments]
    return executable, arguments
