"""Digest orchestration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from podcast_digest.config import DigestConfig
from podcast_digest.models import DigestDocument, Episode
from podcast_digest.renderer import (
    build_document,
    render_daily_overview,
    render_episode,
    render_unavailable,
    summarize_transcript,
    write_document,
)
from podcast_digest.state import StateStore
from podcast_digest.transcripts import load_provider

LOGGER = logging.getLogger(__name__)


class DigestRunner:
    def __init__(self, config: DigestConfig) -> None:
        self.config = config
        self.state = StateStore(config.state_file)
        self.transcript_provider = load_provider(config.transcript_cache)

    def process_episode(self, episode: Episode, transcript_text: str) -> str:
        summary = summarize_transcript(episode, transcript_text)
        return render_episode(summary)

    def handle_unavailable(self, episode: Episode) -> str:
        return render_unavailable(episode)

    def build_daily_overview(self, sections: List[str], stats: dict) -> str:
        if stats["summarized"] == 0:
            overview = "No new transcripts were available today."
        else:
            overview = f"Generated summaries for {stats['summarized']} episodes across {stats['total']} new releases."
        return render_daily_overview(datetime.utcnow(), overview, stats)

    def run(self, episodes_by_show: List[tuple[str, List[Episode], List[str]]]) -> DigestDocument:
        date = datetime.utcnow()
        show_sections: List[str] = []
        summarized = 0
        unavailable = 0

        for show_id, episodes, rendered in episodes_by_show:
            if not episodes:
                continue
            show_sections.append(f"## {episodes[0].show_name}\n")
            for block, episode in zip(rendered, episodes):
                show_sections.append(block)
                self.state.update_last_processed(show_id, episode.published_at)
                if "Transcript unavailable" in block:
                    unavailable += 1
                else:
                    summarized += 1

        total_new = len([ep for _, eps, _ in episodes_by_show for ep in eps])
        stats = {"total": total_new, "summarized": summarized, "unavailable": unavailable}
        daily_overview = self.build_daily_overview(show_sections, stats)
        content = "\n".join([daily_overview, *show_sections])
        output_path = write_document(content, self.config.output.output_dir, date)

        return DigestDocument(
            date=date,
            total_new_episodes=total_new,
            summarized_count=summarized,
            unavailable_count=unavailable,
            overview=daily_overview,
            show_sections=show_sections,
            output_path=output_path,
        )
