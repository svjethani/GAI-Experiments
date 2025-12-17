"""Markdown rendering and deterministic summarization utilities."""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from podcast_digest.models import DigestDocument, Episode, EpisodeSummary, SummarySection


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _segment_sentences(sentences: List[str], desired_segments: int) -> List[List[str]]:
    if not sentences:
        return []
    desired_segments = max(1, desired_segments)
    chunk_size = max(1, math.ceil(len(sentences) / desired_segments))
    return [sentences[i : i + chunk_size] for i in range(0, len(sentences), chunk_size)]


def summarize_transcript(episode: Episode, transcript_text: str) -> EpisodeSummary:
    sentences = _split_sentences(transcript_text)
    segments_raw = _segment_sentences(sentences, min(12, max(5, len(sentences) // 8 or 1)))

    overview_sentences = sentences[:4] if sentences else []
    overview = " ".join(overview_sentences) or "Transcript provided no readable content."

    segments: List[SummarySection] = []
    for idx, seg_sentences in enumerate(segments_raw, start=1):
        if not seg_sentences:
            continue
        heading_source = seg_sentences[0][:80]
        heading = f"Segment {idx}: {heading_source}" if len(heading_source) > 10 else f"Segment {idx}"
        body = " ".join(seg_sentences)
        segments.append(SummarySection(heading=heading, body=body))

    takeaways: List[str] = []
    for seg in segments:
        sentences_seg = _split_sentences(seg.body)
        sample = " ".join(sentences_seg[:2]) if sentences_seg else seg.body
        if sample:
            takeaways.append(sample)
    takeaways = takeaways[:20]

    quotes = [s for s in sentences if len(s) < 180][:10]
    if not quotes and sentences:
        quotes = sentences[:5]

    action_items: List[str] = []
    for s in sentences:
        if any(token in s.lower() for token in ["should", "try", "plan", "recommend"]):
            action_items.append(s)
    action_items = action_items[:10]

    question_sentences = [s for s in sentences if s.endswith("?")]
    open_questions = question_sentences[:8]

    return EpisodeSummary(
        episode=episode,
        overview=overview,
        segments=segments,
        takeaways=takeaways,
        quotes=quotes,
        action_items=action_items,
        open_questions=open_questions,
    )


def render_daily_overview(date: datetime, overview: str, stats: dict) -> str:
    header = f"# Podcast Digest — {date.date().isoformat()}\n\n"
    lines = [header, "## Daily overview", "", overview.strip(), ""]
    lines.append(
        f"New episodes: {stats['total']} | Summarized: {stats['summarized']} | Transcript unavailable: {stats['unavailable']}"
    )
    lines.append("")
    return "\n".join(lines)


def render_episode(summary: EpisodeSummary) -> str:
    episode = summary.episode
    lines = [
        f"### {episode.title}",
        f"*Published:* {episode.published_at.isoformat()} | *Duration:* {episode.duration_ms // 60000} min | [Spotify]({episode.spotify_url})",
        "",
        "#### Overview",
        summary.overview,
        "",
        "#### Structured breakdown",
    ]
    for segment in summary.segments:
        lines.append(f"* **{segment.heading}** — {segment.body}")
    lines.extend(["", "#### Key takeaways"])
    for takeaway in summary.takeaways:
        lines.append(f"* {takeaway}")

    lines.extend(["", "#### Notable quotes"])
    for quote in summary.quotes:
        lines.append(f"> {quote}")

    lines.extend(["", "#### Action items / recommendations"])
    if summary.action_items:
        for item in summary.action_items:
            lines.append(f"* {item}")
    else:
        lines.append("* No explicit action items were captured in the transcript.")

    lines.extend(["", "#### Open questions"])
    if summary.open_questions:
        for question in summary.open_questions:
            lines.append(f"* {question}")
    else:
        lines.append("* No open questions were recorded in the transcript.")

    lines.append("")
    return "\n".join(lines)


def render_unavailable(episode: Episode) -> str:
    lines = [
        f"### {episode.title}",
        "**Transcript unavailable — summary not generated**",
        f"Published: {episode.published_at.isoformat()} | Duration: {episode.duration_ms // 60000} min",
        f"Spotify: {episode.spotify_url}",
        "",
    ]
    return "\n".join(lines)


def build_document(doc: DigestDocument) -> str:
    date_display = doc.date.astimezone(timezone.utc).date().isoformat()
    header = f"# Podcast Digest — {date_display}\n\n"
    body = "\n".join(doc.show_sections)
    return header + doc.overview + "\n\n" + body


def write_document(content: str, output_dir: Path, date: datetime) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{date.date().isoformat()}.md"
    path.write_text(content, encoding="utf-8")
    return path
