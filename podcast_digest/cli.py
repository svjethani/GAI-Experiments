"""Command line interface for podcast digest."""
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from podcast_digest.config import DigestConfig, load_config
from podcast_digest.digest import DigestRunner
from podcast_digest.spotify import SpotifyClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a daily podcast digest")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the digest pipeline")
    run_parser.add_argument("--config", type=Path, default=Path("config.yaml"), help="Path to config YAML")

    return parser


def load_spotify_client() -> SpotifyClient:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
    return SpotifyClient(client_id=client_id, client_secret=client_secret)


def process(config: DigestConfig) -> None:
    runner = DigestRunner(config)
    spotify_client = load_spotify_client()

    episodes_by_show = []
    for show in config.shows:
        show_id = show.id or spotify_client.resolve_show_id(show.url or "")
        last_processed = runner.state.last_processed(show_id)
        episodes = spotify_client.get_new_episodes(show_id, last_processed)

        rendered_blocks = []
        for episode in episodes:
            transcript_result = runner.transcript_provider.get_transcript(episode)
            if transcript_result.status == "available" and transcript_result.text:
                rendered_blocks.append(runner.process_episode(episode, transcript_result.text))
            elif transcript_result.status == "error":
                rendered_blocks.append(
                    f"### {episode.title}\n**Transcript unavailable — error fetching transcript**\n{transcript_result.error or ''}\n"
                )
            else:
                rendered_blocks.append(runner.handle_unavailable(episode))
        episodes_by_show.append((show_id, episodes, rendered_blocks))

    document = runner.run(episodes_by_show)
    LOGGER.info("Digest written to %s", document.output_path)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.config)
        process(config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
