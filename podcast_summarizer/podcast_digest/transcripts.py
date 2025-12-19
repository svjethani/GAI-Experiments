"""Transcript provider abstractions."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from podcast_digest.models import Episode, TranscriptResult

LOGGER = logging.getLogger(__name__)


class TranscriptProvider:
    """Interface for transcript providers."""

    def get_transcript(self, episode: Episode) -> TranscriptResult:
        raise NotImplementedError


class CachedTranscriptProvider(TranscriptProvider):
    """Reads transcripts from the local cache directory if present."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir

    def _cache_path(self, episode: Episode) -> Path:
        return self.cache_dir / f"{episode.id}.txt"

    def get_transcript(self, episode: Episode) -> TranscriptResult:
        path = self._cache_path(episode)
        if path.exists():
            LOGGER.info("Using cached transcript for %s", episode.title)
            return TranscriptResult(status="available", text=path.read_text(encoding="utf-8"), source="cache")
        return TranscriptResult(status="unavailable", source="cache")


class NullTranscriptProvider(TranscriptProvider):
    """Fallback provider that marks transcript as unavailable."""

    def get_transcript(self, episode: Episode) -> TranscriptResult:
        LOGGER.warning("Transcript unavailable for %s", episode.title)
        return TranscriptResult(status="unavailable", source="none")


class ProviderChain(TranscriptProvider):
    """Tries transcript providers in sequence until one returns available or error."""

    def __init__(self, *providers: TranscriptProvider) -> None:
        self.providers = providers

    def get_transcript(self, episode: Episode) -> TranscriptResult:
        for provider in self.providers:
            result = provider.get_transcript(episode)
            if result.status in {"available", "error"}:
                return result
        return TranscriptResult(status="unavailable", source="chain")


def load_provider(cache_dir: Path) -> TranscriptProvider:
    """Create a default provider chain using local cache first."""

    cache_dir.mkdir(parents=True, exist_ok=True)
    return ProviderChain(CachedTranscriptProvider(cache_dir), NullTranscriptProvider())
