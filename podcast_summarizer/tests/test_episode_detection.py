from datetime import datetime

from podcast_digest.spotify import SpotifyClient


class DummySpotifyClient(SpotifyClient):
    def __init__(self):
        super().__init__("id", "secret")
        self.calls = {"get_show": 0, "iter_episodes": 0}

    def get_show(self, show_id: str):
        self.calls["get_show"] += 1
        return {"name": "Demo Show"}

    def iter_episodes(self, show_id: str, limit: int = 50):
        self.calls["iter_episodes"] += 1
        items = [
            {
                "id": "ep2",
                "show": {"id": show_id},
                "name": "New Episode",
                "description": "New",
                "release_date": "2024-01-05",
                "duration_ms": 650000,
                "external_urls": {"spotify": "http://spotify/ep2"},
            },
            {
                "id": "ep1",
                "show": {"id": show_id},
                "name": "Old Episode",
                "description": "Old",
                "release_date": "2023-12-31",
                "duration_ms": 600000,
                "external_urls": {"spotify": "http://spotify/ep1"},
            },
        ]
        for item in items:
            yield item


def test_get_new_episodes_filters_by_last_processed():
    client = DummySpotifyClient()
    last_processed = datetime(2024, 1, 1)

    episodes = client.get_new_episodes("show123", last_processed)

    assert len(episodes) == 1
    assert episodes[0].id == "ep2"
    assert client.calls["get_show"] == 1
    assert client.calls["iter_episodes"] == 1
