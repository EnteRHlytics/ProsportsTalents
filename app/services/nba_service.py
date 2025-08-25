import logging
from typing import Optional

import requests
from flask import current_app
from cachelib import SimpleCache
from .http_utils import request_with_retry
from .rate_limit import RateLimiter

from app import db
from app.models import NBATeam, NBAGame, AthleteProfile, AthleteStat
from .data_mapping import map_nba_team, map_nba_game


class NBAAPIClient:
    """Simple client for the public NBA stats API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        rate_limit_interval: float = 1.0,
        cache_timeout: int = 3600,
    ):
        self.base_url = base_url or current_app.config.get(
            'NBA_API_BASE_URL', 'https://api.balldontlie.io/v1'
        )
        self.session = requests.Session()
        self.token = token or current_app.config.get('NBA_API_TOKEN')
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        self.rate_limiter = RateLimiter(rate_limit_interval)
        self.cache = SimpleCache(default_timeout=cache_timeout)

    def _get(self, endpoint: str, params: Optional[dict] = None):
        """Perform GET with retry and handle errors gracefully."""
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
                "NBA API request failed for %s: %s", url, exc
            )
            return {}

    def get_teams(self):
        cached = self.cache.get('teams')
        if cached is not None:
            return cached
        teams = self._get('/teams').get('data', [])
        self.cache.set('teams', teams)
        return teams

    def get_games(self, team_id: int, season: Optional[int] = None):
        params = {'team_ids[]': team_id}
        if season:
            params['seasons[]'] = season
        key = f"games:{team_id}:{season}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        games = self._get('/games', params=params).get('data', [])
        self.cache.set(key, games)
        return games

    def get_player_season_avg(self, player_id: int, season: Optional[int] = None):
        params = {'player_ids[]': player_id}
        if season:
            params['season'] = season
        data = self._get('/season_averages', params=params)
        if data.get('data'):
            return data['data'][0]
        return None


def sync_teams(client: NBAAPIClient):
    """Fetch and store all NBA teams."""
    teams = client.get_teams()
    for t in teams:
        mapped = map_nba_team(t)
        team = NBATeam.query.get(mapped['team_id'])
        if not team:
            team = NBATeam(team_id=mapped['team_id'])
        team.abbreviation = mapped['abbreviation']
        team.city = mapped['city']
        team.conference = mapped['conference']
        team.division = mapped['division']
        team.full_name = mapped['full_name']
        team.name = mapped['name']
        db.session.add(team)
    db.session.commit()
    logging.getLogger(__name__).info("Synced %d NBA teams", len(teams))
    return teams


def sync_games(client: NBAAPIClient, team_id: int, season: Optional[int] = None):
    """Fetch game logs for a team and store them."""
    games = client.get_games(team_id=team_id, season=season)
    for g in games:
        mapped = map_nba_game(g)
        game = NBAGame.query.get(mapped['game_id'])
        if not game:
            game = NBAGame(game_id=mapped['game_id'])
        game.date = mapped['date']
        game.season = mapped['season']
        game.home_team_id = mapped['home_team_id']
        game.visitor_team_id = mapped['visitor_team_id']
        game.home_team_score = mapped['home_team_score']
        game.visitor_team_score = mapped['visitor_team_score']
        db.session.add(game)
    db.session.commit()
    logging.getLogger(__name__).info("Synced %d games for team %s", len(games), team_id)
    return games


def sync_player_stats(client: NBAAPIClient, athlete: AthleteProfile, season: Optional[int] = None):
    """Fetch season averages for an athlete and store as stats."""
    if not athlete.current_team:
        return None
    player_id = getattr(athlete, 'nba_player_id', None)
    if not player_id:
        return None
    data = client.get_player_season_avg(player_id, season=season)
    if not data:
        return None
    mapping = {
        'pts': 'PointsPerGame',
        'reb': 'ReboundsPerGame',
        'ast': 'AssistsPerGame',
    }
    for api_field, stat_name in mapping.items():
        stat = AthleteStat.query.filter_by(
            athlete_id=athlete.athlete_id,
            name=stat_name,
            season=str(data.get('season')),
        ).first()
        if not stat:
            stat = AthleteStat(
                athlete_id=athlete.athlete_id,
                name=stat_name,
                season=str(data.get('season')),
            )
        stat.value = str(data.get(api_field))
        stat.stat_type = 'NBA'
        db.session.add(stat)
    db.session.commit()
    logging.getLogger(__name__).info(
        "Synced stats for athlete %s from NBA season %s", athlete.athlete_id, data.get('season')
    )
    return data
