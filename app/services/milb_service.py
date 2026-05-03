"""Minor-League Baseball service stub.

Pre-existing reference in `app/jobs.py`; real implementation was never
committed. Stubbed so the app boots and tests collect.
"""


class MiLBAPIClient:
    """No-op MiLB API client."""

    def __init__(self, *args, **kwargs):
        pass


def sync_milb_teams(client, sport_id, league_code):
    return 0


def sync_milb_players(client, sport_id, league_code, season=None):
    return 0


def sync_milb_stats(client, prospect, season=None):
    return 0
