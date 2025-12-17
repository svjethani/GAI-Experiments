from datetime import datetime

from podcast_digest.models import Episode, SummarySection, EpisodeSummary
from podcast_digest.renderer import render_episode, render_unavailable


def _sample_summary():
    episode = Episode(
        id="ep3",
        show_id="demo",
        show_name="Demo Show",
        title="Episode 3",
        description="",
        published_at=datetime(2024, 1, 3),
        duration_ms=500000,
        spotify_url="http://spotify/ep3",
    )
    return EpisodeSummary(
        episode=episode,
        overview="Overview text",
        segments=[SummarySection(heading="Segment 1", body="Content here.")],
        takeaways=["Key insight from the discussion."],
        quotes=["Quote here."],
        action_items=["Action recommended."],
        open_questions=["What comes next?"],
    )


def test_render_episode_contains_sections():
    content = render_episode(_sample_summary())
    assert "Overview" in content
    assert "Structured breakdown" in content
    assert "Key takeaways" in content
    assert "Notable quotes" in content
    assert "Action items" in content
    assert "Open questions" in content


def test_render_unavailable_notice():
    summary = _sample_summary()
    notice = render_unavailable(summary.episode)
    assert "Transcript unavailable" in notice
    assert summary.episode.title in notice
