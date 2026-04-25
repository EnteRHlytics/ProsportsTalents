"""Translation utilities for external sports APIs."""
from datetime import datetime


def map_nba_team(data):
    """Convert NBA API team data into our NBATeam schema fields."""
    return {
        "team_id": data.get("id"),
        "abbreviation": data.get("abbreviation"),
        "city": data.get("city"),
        "conference": data.get("conference"),
        "division": data.get("division"),
        "full_name": data.get("full_name"),
        "name": data.get("name"),
    }


def map_nba_game(data):
    """Convert NBA API game data into our NBAGame schema fields."""
    return {
        "game_id": data.get("id"),
        "date": datetime.fromisoformat(data["date"].rstrip("Z")).date()
        if data.get("date")
        else None,
        "season": data.get("season"),
        "home_team_id": (data.get("home_team") or {}).get("id"),
        "visitor_team_id": (data.get("visitor_team") or {}).get("id"),
        "home_team_score": data.get("home_team_score"),
        "visitor_team_score": data.get("visitor_team_score"),
    }


def map_nfl_team(data):
    """Convert NFL API team data into our NFLTeam schema fields."""
    return {
        # Supports BallDontLie NFL shape and fallback legacy shapes
        "team_id": data.get("id") or data.get("team_id"),
        "name": data.get("name") or data.get("full_name") or data.get("nickname"),
        "abbreviation": data.get("abbreviation") or data.get("abbr"),
        "city": data.get("city") or data.get("location"),
        "conference": data.get("conference"),
        "division": data.get("division"),
    }


def map_mlb_team(data):
    """Convert MLB API team data into our MLBTeam schema fields."""
    return {
        "team_id": data.get("id"),
        "name": data.get("name"),
        "abbreviation": data.get("abbreviation"),
        "location": data.get("locationName") or data.get("city"),
        "league": (data.get("league") or {}).get("name"),
        "division": (data.get("division") or {}).get("name"),
    }


def map_nhl_team(data):
    """Convert NHL API team data into our NHLTeam schema fields."""
    return {
        "team_id": data.get("id"),
        "name": data.get("name"),
        "abbreviation": data.get("abbreviation"),
        "location": data.get("locationName") or data.get("teamName"),
        "conference": (data.get("conference") or {}).get("name"),
        "division": (data.get("division") or {}).get("name"),
    }


def map_nhl_game(data):
    """Convert NHL API schedule data into our NHLGame schema fields."""
    teams = data.get("teams") or {}
    return {
        "game_id": data.get("gamePk"),
        "date": datetime.fromisoformat(data["gameDate"].rstrip("Z")).date()
        if data.get("gameDate")
        else None,
        "season": data.get("season"),
        "home_team_id": (teams.get("home") or {}).get("team", {}).get("id"),
        "visitor_team_id": (teams.get("away") or {}).get("team", {}).get("id"),
        "home_team_score": (teams.get("home") or {}).get("score"),
        "visitor_team_score": (teams.get("away") or {}).get("score"),
    }


# --- Prospect data mappings ---

def _inches_to_cm(height_str: str) -> int | None:
    """Convert ESPN/MLB height string like '6-3' or '6\'3"' to centimetres."""
    if not height_str:
        return None
    try:
        h = str(height_str).replace('"', '').replace("'", '-').replace(' ', '')
        if '-' in h:
            parts = h.split('-')
            feet, inches = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        else:
            feet, inches = int(h), 0
        return round((feet * 12 + inches) * 2.54)
    except (ValueError, TypeError):
        return None


def _lbs_to_kg(lbs) -> float | None:
    try:
        return round(float(lbs) * 0.453592, 2)
    except (ValueError, TypeError):
        return None


def map_milb_player(data: dict) -> dict:
    """Convert MLB Stats API people/{id} response to Prospect fields."""
    primary_pos = (data.get('primaryPosition') or {}).get('abbreviation', '')
    return {
        'first_name': data.get('firstName') or data.get('useName', ''),
        'last_name': data.get('lastName', ''),
        'position': primary_pos,
        'date_of_birth': data.get('birthDate'),
        'nationality': data.get('birthCountry', '')[:3] if data.get('birthCountry') else None,
        'height_cm': _inches_to_cm(data.get('height', '')),
        'weight_kg': _lbs_to_kg(data.get('weight')),
    }


def map_gleague_player(data: dict) -> dict:
    """Convert BallDontLie player response to Prospect fields."""
    return {
        'first_name': data.get('first_name', ''),
        'last_name': data.get('last_name', ''),
        'position': data.get('position', ''),
    }


def map_ncaa_player(data: dict) -> dict:
    """Convert ESPN athlete response to Prospect fields."""
    full = data.get('fullName') or data.get('displayName', '')
    parts = full.split(' ', 1)
    pos = (data.get('position') or {}).get('abbreviation', '') if isinstance(data.get('position'), dict) else ''
    height_str = data.get('height', '')
    weight_val = data.get('weight')
    return {
        'first_name': data.get('firstName') or (parts[0] if parts else ''),
        'last_name': data.get('lastName') or (parts[1] if len(parts) > 1 else ''),
        'position': pos,
        'height_cm': _inches_to_cm(str(height_str)) if height_str else None,
        'weight_kg': _lbs_to_kg(weight_val),
    }


def map_prospect_stat(api_field: str, stat_name: str, value, stat_type: str, season: str) -> dict:
    """Build a ProspectStat-compatible dict from raw API values."""
    return {
        'name': stat_name,
        'value': str(value) if value is not None else None,
        'stat_type': stat_type,
        'season': season,
    }


def map_player(data):
    """Convert generic player data into AthleteProfile fields.

    The function handles common naming variations across APIs and returns
    a dictionary suitable for creating or updating ``AthleteProfile`` and
    related ``User`` records.
    """
    return {
        "external_id": data.get("id") or data.get("playerId"),
        "first_name": data.get("first_name") or data.get("firstName"),
        "last_name": data.get("last_name") or data.get("lastName"),
        "jersey_number": data.get("jersey_number") or data.get("jerseyNumber"),
        "position": data.get("position") or data.get("pos"),
    }

