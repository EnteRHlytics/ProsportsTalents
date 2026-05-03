"""College sports service stub.

Pre-existing reference in `app/jobs.py`; real implementation was never
committed. Stubbed so the app boots and tests collect.
"""


class CollegeAPIClient:
    """No-op college API client."""

    def __init__(self, *args, **kwargs):
        pass


def sync_college_teams(client):
    return 0


def sync_college_players(client, team_external_id):
    return 0
