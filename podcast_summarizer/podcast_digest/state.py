"""State persistence helpers."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class StateStore:
    """Persist last processed markers for shows."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def last_processed(self, show_id: str) -> Optional[datetime]:
        raw = self._data.get(show_id)
        if not raw:
            return None
        return datetime.fromisoformat(raw)

    def update_last_processed(self, show_id: str, published_at: datetime) -> None:
        self._data[show_id] = published_at.isoformat()
        self.save()
