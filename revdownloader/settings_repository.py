"""JSON persistence isolated from Tkinter and application state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class JsonSettingsRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
        if not isinstance(data, dict):
            raise ValueError("Settings root must be a JSON object")
        return data

    def save(self, settings: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, indent=2, ensure_ascii=False)

    def update(self, values: Dict[str, Any]) -> None:
        try:
            settings = self.load()
        except (json.JSONDecodeError, ValueError):
            # A valid save should recover from a truncated or otherwise corrupt
            # settings file instead of failing forever on every future save.
            settings = {}
        settings.update(values)
        self.save(settings)
