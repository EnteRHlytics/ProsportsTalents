import logging
from typing import Optional

import requests
from flask import current_app
from cachelib import SimpleCache
from .http_utils import request_with_retry
from .rate_limit import RateLimiter

from app import db
from app.models import NFLTeam, AthleteProfile, AthleteStat
from .data_mapping import map_nfl_team


class NFLAPIClient:
    """Client for a public NFL stats API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        rate_limit_interval: float = 1.0,
        cache_timeout: int = 3600,
    ):
        self.base_url = base_url or current_app.config.get(
            "NFL_API_BASE_URL", "https://api.nfl.com/v1"
        )
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(rate_limit_interval)
        self.cache = SimpleCache(default_timeout=cache_timeout)

    def _get(self, endpoint: str, params: Optional[dict] = None):
        """Perform GET with retry and handle errors."""
        url = f"{self.base_url}{endpoint}"
        try:
            resp = request_with_retry(
                self.session,
                "get",
                url,
                params=params,
                timeout=10,
                logger=logging.getLogger(__name__),
                rate_limiter=self.rate_limiter,
            )
            try:
                return resp.json()
            except ValueError as exc:
                logging.getLogger(__name__).error(
                    "Failed parsing JSON from %s: %s", url, exc
                )
                return {}
        except Exception as exc:
            logging.getLogger(__name__).error(
                "NFL API request failed for %s: %s", url, exc
            )
            return {}

    def get_teams(self):
        cached = self.cache.get("teams")
        if cached is not None:
            return cached
        data = self._get("/teams")
        teams = data.get("teams", [])
        self.cache.set("teams", teams)
        return teams

    def get_player_stats(
        self, player_id: int, season: Optional[int] = None, group: str = "offense"
    ):
        params = {"group": group}
        if season:
            params["season"] = season
        data = self._get(f"/players/{player_id}/stats", params=params)
        return data.get("stats", {})


def sync_teams(client: NFLAPIClient):
    """Fetch and store all NFL teams."""
    teams = client.get_teams()
    for t in teams:
        mapped = map_nfl_team(t)
        team = NFLTeam.query.get(mapped["team_id"])
        if not team:
            team = NFLTeam(team_id=mapped["team_id"])
        team.name = mapped["name"]
        team.abbreviation = mapped["abbreviation"]
        team.city = mapped["city"]
        team.conference = mapped["conference"]
        team.division = mapped["division"]
        db.session.add(team)
    db.session.commit()
    logging.getLogger(__name__).info("Synced %d NFL teams", len(teams))
    return teams


def sync_player_stats(
    client: NFLAPIClient, athlete: AthleteProfile, season: Optional[int] = None
):
    """Fetch NFL stats for an athlete and store them."""
    player_id = getattr(athlete, "nfl_player_id", None)
    if not player_id:
        return None

    offense = client.get_player_stats(player_id, season=season, group="offense") or {}
    defense = client.get_player_stats(player_id, season=season, group="defense") or {}

    mappings = {
        "NFL_OFFENSE": {
            "passingYards": "PassingYards",
            "rushingYards": "RushingYards",
            "receivingYards": "ReceivingYards",
        },
        "NFL_DEFENSE": {"tackles": "Tackles", "sacks": "Sacks"},
    }

    season_str = str(season) if season else None

    for stat_type, mapping in mappings.items():
        source = offense if stat_type == "NFL_OFFENSE" else defense
        for api_field, stat_name in mapping.items():
            if api_field not in source:
                continue
            stat = AthleteStat.query.filter_by(
                athlete_id=athlete.athlete_id,
                name=stat_name,
                season=season_str,
            ).first()
            if not stat:
                stat = AthleteStat(
                    athlete_id=athlete.athlete_id,
                    name=stat_name,
                    season=season_str,
                )
            stat.value = str(source.get(api_field))
            stat.stat_type = stat_type
            db.session.add(stat)

    db.session.commit()
    logging.getLogger(__name__).info(
        "Synced NFL stats for athlete %s season %s", athlete.athlete_id, season_str
    )
    return {"offense": offense, "defense": defense}
