import logging
from typing import Optional

import requests
from flask import current_app
from cachelib import SimpleCache
from .http_utils import request_with_retry
from .rate_limit import RateLimiter

from app import db
from app.models import NHLTeam, NHLGame, AthleteProfile, AthleteStat
from .data_mapping import map_nhl_team, map_nhl_game


class NHLAPIClient:
    """Client for the public NHL stats API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        rate_limit_interval: float = 1.0,
        cache_timeout: int = 3600,
    ):
        self.base_url = base_url or current_app.config.get(
            "NHL_API_BASE_URL", "https://statsapi.web.nhl.com/api/v1"
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
                "NHL API request failed for %s: %s", url, exc
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

    def get_standings(self):
        cached = self.cache.get("standings")
        if cached is not None:
            return cached
        data = self._get("/standings")
        records = data.get("records", [])
        self.cache.set("standings", records)
        return records

    def get_games(self, team_id: int, season: Optional[str] = None):
        params = {"teamId": team_id}
        if season:
            params["season"] = season
        key = f"games:{team_id}:{season}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        data = self._get("/schedule", params=params)
        games = []
        for d in data.get("dates", []):
            games.extend(d.get("games", []))
        self.cache.set(key, games)
        return games

    def get_player_stats(self, player_id: int, season: Optional[str] = None):
        params = {"stats": "statsSingleSeason"}
        if season:
            params["season"] = season
        data = self._get(f"/people/{player_id}/stats", params=params)
        if data.get("stats"):
            splits = data["stats"][0].get("splits", [])
            if splits:
                return splits[0].get("stat", {})
        return None


def sync_teams(client: NHLAPIClient):
    """Fetch and store all NHL teams."""
    teams = client.get_teams()
    for t in teams:
        mapped = map_nhl_team(t)
        team = NHLTeam.query.get(mapped["team_id"])
        if not team:
            team = NHLTeam(team_id=mapped["team_id"])
        team.name = mapped["name"]
        team.abbreviation = mapped["abbreviation"]
        team.location = mapped["location"]
        team.division = mapped["division"]
        team.conference = mapped["conference"]
        db.session.add(team)
    db.session.commit()
    logging.getLogger(__name__).info("Synced %d NHL teams", len(teams))
    return teams


def sync_standings(client: NHLAPIClient):
    """Fetch standings and update team records."""
    records = client.get_standings()
    for r in records:
        for tr in r.get("teamRecords", []):
            team_id = tr["team"]["id"]
            team = NHLTeam.query.get(team_id)
            if not team:
                continue
            league = tr.get("leagueRecord", {})
            team.wins = league.get("wins")
            team.losses = league.get("losses")
            team.overtime_losses = league.get("ot")
            team.points = tr.get("points")
            db.session.add(team)
    db.session.commit()
    logging.getLogger(__name__).info("Synced NHL standings")
    return records


def sync_games(client: NHLAPIClient, team_id: int, season: Optional[str] = None):
    """Fetch schedule for a team and store the games."""
    games = client.get_games(team_id=team_id, season=season)
    for g in games:
        mapped = map_nhl_game(g)
        game = NHLGame.query.get(mapped["game_id"])
        if not game:
            game = NHLGame(game_id=mapped["game_id"])
        game.date = mapped["date"]
        game.season = mapped["season"]
        game.home_team_id = mapped["home_team_id"]
        game.visitor_team_id = mapped["visitor_team_id"]
        game.home_team_score = mapped["home_team_score"]
        game.visitor_team_score = mapped["visitor_team_score"]
        db.session.add(game)
    db.session.commit()
    logging.getLogger(__name__).info(
        "Synced %d NHL games for team %s", len(games), team_id
    )
    return games


def sync_player_stats(
    client: NHLAPIClient, athlete: AthleteProfile, season: Optional[str] = None
):
    """Fetch NHL stats for an athlete and store them."""
    player_id = getattr(athlete, "nhl_player_id", None)
    if not player_id:
        return None

    data = client.get_player_stats(player_id, season=season) or {}

    mapping = {"goals": "Goals", "assists": "Assists", "points": "Points"}
    season_str = str(season) if season else None

    for api_field, stat_name in mapping.items():
        if api_field not in data:
            continue
        stat = AthleteStat.query.filter_by(
            athlete_id=athlete.athlete_id, name=stat_name, season=season_str
        ).first()
        if not stat:
            stat = AthleteStat(
                athlete_id=athlete.athlete_id, name=stat_name, season=season_str
            )
        stat.value = str(data.get(api_field))
        stat.stat_type = "NHL"
        db.session.add(stat)

    db.session.commit()
    logging.getLogger(__name__).info(
        "Synced NHL stats for athlete %s season %s", athlete.athlete_id, season_str
    )
    return data
