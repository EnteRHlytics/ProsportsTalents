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
        "team_id": data.get("id"),
        "name": data.get("name"),
        "abbreviation": data.get("abbreviation"),
        "city": data.get("city"),
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

