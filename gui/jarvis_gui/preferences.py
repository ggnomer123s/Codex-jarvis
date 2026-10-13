"""Model metadata and multilingual voice settings; no authentication reads."""
import json
import os
from pathlib import Path
import re

LANGUAGES = [("auto", "Auto detect"), ("ru", "Russian"), ("en", "English"),
             ("uk", "Ukrainian"), ("de", "German"), ("fr", "French"),
             ("es", "Spanish"), ("it", "Italian"), ("pt", "Portuguese"),
             ("pl", "Polish"), ("tr", "Turkish"), ("ar", "Arabic"),
             ("zh", "Chinese"), ("ja", "Japanese"), ("ko", "Korean"), ("hi", "Hindi")]
VOICE_MODELS = ["tiny", "base", "small", "medium"]
FULL_ACKNOWLEDGEMENT = "ENABLE FULL ACCESS"


def valid_model_id(model):
    return not model or bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", model))


def valid_voice_model(model):
    multilingual = [*VOICE_MODELS, "large", "large-v1", "large-v2", "large-v3", "turbo", "large-v3-turbo"]
    return model in multilingual or (bool(model) and Path(model).is_dir())


def cached_models(home):
    path = Path(home) / "models_cache.json"
    try:
        if path.stat().st_size > 2_000_000:
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        return []
    models = []
    for item in data["models"][:200]:
        if not isinstance(item, dict) or item.get("visibility") == "hide":
            continue
        slug = item.get("slug", item.get("id", ""))
        if isinstance(slug, str) and slug and valid_model_id(slug) and slug not in models:
            models.append(slug)
    return models


def full_profile_home():
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "jarvis-codex/full-codex-home"
    return Path.home() / ".local/share/jarvis-codex/full-codex-home"


def elevated():
    if os.name == "nt":
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    return os.geteuid() == 0
