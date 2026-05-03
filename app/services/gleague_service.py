"""G-League service stub.

Pre-existing references in `app/jobs.py` import this module but the real
implementation was never committed. Stubbed out so the application can boot
and tests can collect. Replace with a real client when G-League ingestion
lands.
"""


class GLeagueAPIClient:
    """No-op G-League API client."""

    def __init__(self, *args, **kwargs):
        pass


def sync_gleague_teams(client):
    return 0


def sync_gleague_players(client):
    return 0


def sync_gleague_stats(client, prospect, season=None):
    return 0
