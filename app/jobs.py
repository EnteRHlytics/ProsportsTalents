from datetime import date
import logging

from app import db
from app.models import AthleteProfile, NBATeam, NHLTeam, SyncLog
from app.services import nba_service, nfl_service, mlb_service, nhl_service
from app.services import gleague_service, milb_service as milb_svc, college_service
from app.models.prospect import ProspectLeague, MinorLeagueTeam, Prospect

logger = logging.getLogger(__name__)


def _log_sync(job_name: str, success: bool, message: str = "") -> None:
    """Persist a sync job result."""
    entry = SyncLog(job_name=job_name, success=success, message=message)
    db.session.add(entry)
    db.session.commit()


def nightly_sync_games():
    """Sync team lists and game results for the current season."""
    year = date.today().year

    try:
        nba_client = nba_service.NBAAPIClient()
        nba_service.sync_teams(nba_client)
        for team in NBATeam.query.all():
            nba_service.sync_games(nba_client, team.team_id, season=year)

        nhl_client = nhl_service.NHLAPIClient()
        nhl_service.sync_teams(nhl_client)
        for team in NHLTeam.query.all():
            nhl_service.sync_games(nhl_client, team.team_id, season=str(year))

        logger.info("Nightly game sync complete")
        _log_sync("nightly_sync_games", True, "completed")
    except Exception as exc:
        logger.exception("Nightly game sync failed: %s", exc)
        db.session.rollback()
        _log_sync("nightly_sync_games", False, str(exc))


def weekly_sync_player_stats():
    """Update player statistics across all sports."""
    year = date.today().year

    try:
        nba_client = nba_service.NBAAPIClient()
        nfl_client = nfl_service.NFLAPIClient()
        mlb_client = mlb_service.MLBAPIClient()
        nhl_client = nhl_service.NHLAPIClient()

        for athlete in AthleteProfile.query.all():
            sport = athlete.primary_sport.code if athlete.primary_sport else None
            if sport == "NBA":
                nba_service.sync_player_stats(nba_client, athlete, season=year)
            elif sport == "NFL":
                nfl_service.sync_player_stats(nfl_client, athlete, season=year)
            elif sport == "MLB":
                mlb_service.sync_player_stats(mlb_client, athlete, season=year)
            elif sport == "NHL":
                nhl_service.sync_player_stats(nhl_client, athlete, season=str(year))

        logger.info("Weekly player stats sync complete")
        _log_sync("weekly_sync_player_stats", True, "completed")
    except Exception as exc:
        logger.exception("Weekly stats sync failed: %s", exc)
        db.session.rollback()
        _log_sync("weekly_sync_player_stats", False, str(exc))


def sync_all_prospects():
    """Sync G League, MiLB AAA/AA, and NCAA D1 Basketball prospects."""
    year = date.today().year

    try:
        # --- G League ---
        gleague_client = gleague_service.GLeagueAPIClient()
        gleague_service.sync_gleague_teams(gleague_client)
        gleague_service.sync_gleague_players(gleague_client)

        gleague_league = ProspectLeague.query.filter_by(code='GLEAGUE').first()
        if gleague_league:
            for prospect in Prospect.query.filter_by(
                prospect_league_id=gleague_league.prospect_league_id, is_deleted=False
            ).all():
                gleague_service.sync_gleague_stats(gleague_client, prospect, season=year)

        # --- MiLB AAA and AA ---
        milb_client = milb_svc.MiLBAPIClient()
        for league_code, sport_id in [('MILB_AAA', 11), ('MILB_AA', 12)]:
            milb_svc.sync_milb_teams(milb_client, sport_id, league_code)
            milb_svc.sync_milb_players(milb_client, sport_id, league_code, season=year)

            league = ProspectLeague.query.filter_by(code=league_code).first()
            if league:
                for prospect in Prospect.query.filter_by(
                    prospect_league_id=league.prospect_league_id, is_deleted=False
                ).all():
                    milb_svc.sync_milb_stats(milb_client, prospect, season=year)

        # --- NCAA D1 Basketball ---
        college_client = college_service.CollegeAPIClient()
        college_service.sync_college_teams(college_client)

        ncaa_league = ProspectLeague.query.filter_by(code='NCAA_BB_D1').first()
        if ncaa_league:
            teams = MinorLeagueTeam.query.filter_by(
                prospect_league_id=ncaa_league.prospect_league_id
            ).all()
            for team in teams:
                college_service.sync_college_players(college_client, team.external_id)

        logger.info('Prospect sync complete for season %s', year)
        _log_sync('sync_all_prospects', True, f'season {year}')
    except Exception as exc:
        logger.exception('Prospect sync failed: %s', exc)
        db.session.rollback()
        _log_sync('sync_all_prospects', False, str(exc))


def historical_backfill_stats(seasons=None, num_seasons: int = 3):
    """Backfill historical stats for tracked athletes and teams."""
    if seasons is None:
        current_year = date.today().year
        seasons = [current_year - i for i in range(num_seasons)]

    try:
        nba_client = nba_service.NBAAPIClient()
        nfl_client = nfl_service.NFLAPIClient()
        mlb_client = mlb_service.MLBAPIClient()
        nhl_client = nhl_service.NHLAPIClient()

        # ensure team lists exist
        nba_service.sync_teams(nba_client)
        nhl_service.sync_teams(nhl_client)
        nfl_service.sync_teams(nfl_client)
        mlb_service.sync_teams(mlb_client)

        for season in seasons:
            for team in NBATeam.query.all():
                nba_service.sync_games(nba_client, team.team_id, season=season)
            for team in NHLTeam.query.all():
                nhl_service.sync_games(
                    nhl_client, team.team_id, season=str(season)
                )

            for athlete in AthleteProfile.query.all():
                sport = athlete.primary_sport.code if athlete.primary_sport else None
                if sport == "NBA":
                    nba_service.sync_player_stats(
                        nba_client, athlete, season=season
                    )
                elif sport == "NFL":
                    nfl_service.sync_player_stats(
                        nfl_client, athlete, season=season
                    )
                elif sport == "MLB":
                    mlb_service.sync_player_stats(
                        mlb_client, athlete, season=season
                    )
                elif sport == "NHL":
                    nhl_service.sync_player_stats(
                        nhl_client, athlete, season=str(season)
                    )

        logger.info("Historical stats backfill complete for seasons %s", seasons)
        _log_sync("historical_backfill_stats", True, f"seasons: {seasons}")
    except Exception as exc:
        logger.exception("Historical backfill failed: %s", exc)
        db.session.rollback()
        _log_sync("historical_backfill_stats", False, str(exc))

