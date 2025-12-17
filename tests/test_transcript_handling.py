from datetime import datetime
from pathlib import Path

from podcast_digest.config import DigestConfig, OutputConfig, ShowConfig
from podcast_digest.digest import DigestRunner
from podcast_digest.models import Episode


def make_runner(tmp_path: Path) -> DigestRunner:
    config = DigestConfig(
        shows=[ShowConfig(id="demo")],
        output=OutputConfig(output_dir=tmp_path / "output"),
        state_file=tmp_path / "state.json",
        transcript_cache=tmp_path / "cache",
    )
    return DigestRunner(config)


def test_transcript_unavailable(tmp_path: Path):
    runner = make_runner(tmp_path)
    episode = Episode(
        id="ep1",
        show_id="demo",
        show_name="Demo Show",
        title="Episode 1",
        description=None,
        published_at=datetime(2024, 1, 1),
        duration_ms=600000,
        spotify_url="http://spotify/ep1",
    )

    result = runner.transcript_provider.get_transcript(episode)

    assert result.status == "unavailable"
    rendered = runner.handle_unavailable(episode)
    assert "Transcript unavailable" in rendered


def test_state_updates_on_run(tmp_path: Path):
    runner = make_runner(tmp_path)
    episode = Episode(
        id="ep2",
        show_id="demo",
        show_name="Demo Show",
        title="Episode 2",
        description=None,
        published_at=datetime(2024, 1, 2),
        duration_ms=700000,
        spotify_url="http://spotify/ep2",
    )
    section = runner.handle_unavailable(episode)
    runner.run([(episode.show_id, [episode], [section])])

    assert runner.state.last_processed("demo").isoformat().startswith("2024-01-02")
