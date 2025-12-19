"""Spotify API client for fetching shows and episodes."""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional
from urllib import request, parse, error

from podcast_digest.models import Episode

LOGGER = logging.getLogger(__name__)

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyAuthError(Exception):
    pass


@dataclass
class SimpleResponse:
    status_code: int
    text: str

    def json(self) -> Dict:
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 300):
            raise error.HTTPError("", self.status_code, self.text, {}, None)


class SpotifyClient:
    """Lightweight Spotify Web API client using urllib."""

    def __init__(self, client_id: str, client_secret: str, timeout: float = 10.0) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self._token: Optional[str] = None

    def _auth_headers(self) -> Dict[str, str]:
        if not self._token:
            self.refresh_token()
        return {"Authorization": f"Bearer {self._token}"}

    def refresh_token(self) -> None:
        data = parse.urlencode({"grant_type": "client_credentials"}).encode()
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        req = request.Request(
            SPOTIFY_TOKEN_URL,
            data=data,
            headers={"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode()
                payload = json.loads(body)
                self._token = payload.get("access_token")
        except Exception as exc:  # pragma: no cover - network errors
            raise SpotifyAuthError(f"Failed to fetch token: {exc}") from exc

    def resolve_show_id(self, url: str) -> str:
        if "open.spotify.com/show/" in url:
            return url.rstrip("/").split("/")[-1].split("?")[0]
        return url

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> SimpleResponse:
        query = f"?{parse.urlencode(params)}" if params else ""
        req = request.Request(f"{SPOTIFY_API_BASE}{path}{query}", headers=self._auth_headers())
        with request.urlopen(req, timeout=self.timeout) as resp:
            text = resp.read().decode()
            return SimpleResponse(status_code=resp.status, text=text)

    def get_show(self, show_id: str) -> Dict:
        resp = self._get(f"/shows/{show_id}")
        resp.raise_for_status()
        return resp.json()

    def iter_episodes(self, show_id: str, limit: int = 50) -> Iterable[Dict]:  # pragma: no cover - network
        offset = 0
        while True:
            resp = self._get(
                f"/shows/{show_id}/episodes",
                params={"offset": offset, "limit": limit, "market": "US"},
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if not items:
                break
            yield from items
            if data.get("next") is None:
                break
            offset += limit

    def map_episode(self, raw: Dict, show_name: str) -> Episode:
        release_date = raw.get("release_date") or raw.get("release_date_precision")
        published_at = datetime.fromisoformat(release_date)
        return Episode(
            id=raw.get("id", ""),
            show_id=raw.get("show", {}).get("id", ""),
            show_name=show_name,
            title=raw.get("name", ""),
            description=raw.get("description"),
            published_at=published_at,
            duration_ms=raw.get("duration_ms", 0),
            spotify_url=raw.get("external_urls", {}).get("spotify", ""),
        )

    def get_new_episodes(self, show_id: str, last_processed: Optional[datetime]) -> List[Episode]:
        show_data = self.get_show(show_id)
        show_name = show_data.get("name", show_id)
        episodes: List[Episode] = []
        for raw in self.iter_episodes(show_id):
            episode = self.map_episode(raw, show_name)
            if last_processed and episode.published_at <= last_processed:
                break
            episodes.append(episode)
        episodes.sort(key=lambda e: e.published_at)
        return episodes
