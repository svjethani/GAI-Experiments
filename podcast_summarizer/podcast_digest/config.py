"""Configuration loading and validation for the podcast digest."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:  # Optional dependency
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None
import json


@dataclass
class ShowConfig:
    id: Optional[str] = None
    url: Optional[str] = None
    name: Optional[str] = None
    last_processed: Optional[str] = None

    def resolve_id(self) -> str:
        if not (self.id or self.url):
            raise ValueError("Either 'id' or 'url' must be set for a show")
        return self.id or ""


@dataclass
class OutputConfig:
    format: str = "markdown"
    output_dir: Path = Path("output")


@dataclass
class DigestConfig:
    shows: List[ShowConfig]
    output: OutputConfig = field(default_factory=OutputConfig)
    state_file: Path = Path("data/state.json")
    transcript_cache: Path = Path("data/transcripts")
    timezone: str = "UTC"


def load_config(path: Path) -> DigestConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        content = f.read()
        if yaml:
            raw = yaml.safe_load(content) or {}
        else:
            raw = json.loads(content)

    shows = [ShowConfig(**item) for item in raw.get("shows", [])]
    output_raw = raw.get("output", {})
    output = OutputConfig(**output_raw)
    state_file = Path(raw.get("state_file", "data/state.json"))
    transcript_cache = Path(raw.get("transcript_cache", "data/transcripts"))
    timezone = raw.get("timezone", "UTC")

    return DigestConfig(
        shows=shows,
        output=output,
        state_file=state_file,
        transcript_cache=transcript_cache,
        timezone=timezone,
    )
