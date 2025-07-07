import os
from datetime import date
from typing import Dict

from app import create_app, db
from app.models import AthleteProfile, AthleteStat
from app.services import nba_service, nfl_service, mlb_service, nhl_service


def _collect_stats(athlete: AthleteProfile, year: int) -> Dict[str, str]:
    """Return relevant stats for the given athlete."""
    sport = athlete.primary_sport.code if athlete.primary_sport else None
    mapping = {}
    if sport == "NBA":
        mapping = {
            "PPG": "PointsPerGame",
            "RPG": "ReboundsPerGame",
            "APG": "AssistsPerGame",
        }
    elif sport == "NFL":
        mapping = {
            "PassingYards": "PassingYards",
            "Touchdowns": "Touchdowns",
            "QBRating": "QBRating",
        }
    elif sport == "MLB":
        mapping = {
            "AVG": "BattingAverage",
            "HR": "HomeRuns",
            "RBI": "RunsBattedIn",
        }
    elif sport == "NHL":
        mapping = {"Goals": "Goals", "Assists": "Assists", "Points": "Points"}

    stats = {}
    for label, name in mapping.items():
        stat = AthleteStat.query.filter_by(
            athlete_id=athlete.athlete_id, name=name, season=str(year)
        ).first()
        stats[label] = stat.value if stat else "N/A"
    return stats


def main() -> None:
    env = os.getenv("FLASK_ENV") or "development"
    app = create_app(env)

    with app.app_context():
        year = date.today().year
        athletes = (
            AthleteProfile.query.filter_by(is_deleted=False, is_featured=True).all()
        )

        nba_client = nba_service.NBAAPIClient()
        nfl_client = nfl_service.NFLAPIClient()
        mlb_client = mlb_service.MLBAPIClient()
        nhl_client = nhl_service.NHLAPIClient()

        for ath in athletes:
            sport = ath.primary_sport.code if ath.primary_sport else None
            try:
                if sport == "NBA":
                    nba_service.sync_player_stats(nba_client, ath, season=year)
                elif sport == "NFL":
                    nfl_service.sync_player_stats(nfl_client, ath, season=year)
                elif sport == "MLB":
                    mlb_service.sync_player_stats(mlb_client, ath, season=year)
                elif sport == "NHL":
                    nhl_service.sync_player_stats(nhl_client, ath, season=str(year))
            except Exception as exc:  # noqa: BLE001
                app.logger.error("Stat sync failed for %s: %s", ath.athlete_id, exc)
                db.session.rollback()

            stats = _collect_stats(ath, year)

            name = f"{ath.user.first_name} {ath.user.last_name}" if ath.user else ath.athlete_id
            pos = ath.primary_position.name if ath.primary_position else "N/A"
            print(f"- {name}")
            print(f"  - Position: {pos}")
            print(f"  - Team: {ath.current_team or 'N/A'}")
            print(f"  - Sport: {sport}")
            shown = 0
            for label, value in stats.items():
                if shown >= 2:
                    break
                print(f"    - {label}: {value}")
                shown += 1
            print()


if __name__ == "__main__":  # pragma: no cover
    main()
