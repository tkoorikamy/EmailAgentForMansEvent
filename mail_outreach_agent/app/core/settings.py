import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "smtp_host": "",
    "smtp_port": 465,
    "smtp_ssl": True,
    "smtp_starttls": False,
    "smtp_login": "",
    "sender_name": "",
    "delay_seconds": 20,
    "max_per_run": 500,
    "max_per_day": 100,
    "attachment_path": "",
}


def load_settings() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()
    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    return merged


def save_settings(settings: Dict[str, Any]) -> None:
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings)
    CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
