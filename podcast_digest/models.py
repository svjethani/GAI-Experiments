"""Data models for the podcast digest."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class Episode:
    id: str
    show_id: str
    show_name: str
    title: str
    description: Optional[str]
    published_at: datetime
    duration_ms: int
    spotify_url: str


@dataclass
class TranscriptResult:
    status: str
    text: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


@dataclass
class SummarySection:
    heading: str
    body: str


@dataclass
class EpisodeSummary:
    episode: Episode
    overview: str
    segments: List[SummarySection]
    takeaways: List[str]
    quotes: List[str]
    action_items: List[str]
    open_questions: List[str]


@dataclass
class DigestDocument:
    date: datetime
    total_new_episodes: int
    summarized_count: int
    unavailable_count: int
    overview: str
    show_sections: List[str]
    output_path: Path
