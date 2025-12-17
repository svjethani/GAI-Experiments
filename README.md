# Podcast Digest Automation

This project generates a daily Spotify podcast digest that fetches new episodes for configured shows, attempts to pull transcripts, and produces a structured Markdown report per day.

## Features
- Pulls recent episodes per Spotify show ID or URL using the Spotify Web API.
- Tracks last processed episodes for idempotent re-runs.
- Pluggable transcript providers (local cache by default) with explicit handling when transcripts are unavailable.
- Deterministic summarization that turns transcripts into detailed overviews, segmented breakdowns, key takeaways, quotes, action items, and open questions.
- Markdown output to `output/YYYY-MM-DD.md` with a daily overview at the top.
- CLI entrypoint: `python -m podcast_digest run`.
- Ready for cron or GitHub Actions scheduling.

## Quickstart
1. Create and populate a `.env` file based on `.env.example` with Spotify credentials.
2. (Optional) Create a virtual environment if you plan to add dependencies later:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Update `config.yaml` with your Spotify show IDs or URLs.
4. Run the digest:
   ```bash
   python -m podcast_digest run --config config.yaml
   ```
5. View the generated Markdown in `output/`.

## Configuration
See `config.yaml` for a sample (JSON syntax for compatibility without PyYAML). Key fields:
- `shows`: list of shows (id or url required, optional `last_processed`).
- `output.output_dir`: where Markdown files are stored.
- `state_file`: JSON file storing last processed markers.
- `transcript_cache`: directory of cached transcript text files (`<episode_id>.txt`).

## Scheduling
- **Cron** (runs daily at 8 AM UTC):
  ```cron
  0 8 * * * cd /path/to/GAI-Experiments && /path/to/.venv/bin/python -m podcast_digest run --config /path/to/config.yaml
  ```
- **GitHub Actions**: create `.github/workflows/digest.yml` using Python 3.11, install deps, and run the CLI.

## Testing
```bash
pytest
```

## Notes on transcripts and summaries
- If no transcript is found, the episode still appears with a clear "Transcript unavailable" notice and metadata only.
- The built-in provider reads transcripts from `data/transcripts/<episode_id>.txt`. Add your own providers for external services if desired.
- Summaries extract sentences from the transcript and avoid hallucinating content.
