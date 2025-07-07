import datetime
from app.services import data_mapping as dm


def test_map_nba_team():
    data = {
        "id": 1,
        "abbreviation": "LAL",
        "city": "Los Angeles",
        "conference": "West",
        "division": "Pacific",
        "full_name": "Los Angeles Lakers",
        "name": "Lakers",
    }
    mapped = dm.map_nba_team(data)
    assert mapped["team_id"] == 1
    assert mapped["full_name"] == "Los Angeles Lakers"


def test_map_mlb_team():
    data = {
        "id": 1,
        "name": "Yankees",
        "abbreviation": "NYY",
        "locationName": "New York",
        "league": {"name": "AL"},
        "division": {"name": "East"},
    }
    mapped = dm.map_mlb_team(data)
    assert mapped["location"] == "New York"
    assert mapped["league"] == "AL"


def test_map_nhl_game():
    data = {
        "gamePk": 99,
        "gameDate": "2024-01-01T00:00:00Z",
        "season": "20242025",
        "teams": {
            "home": {"team": {"id": 1}, "score": 3},
            "away": {"team": {"id": 2}, "score": 2},
        },
    }
    mapped = dm.map_nhl_game(data)
    assert mapped["game_id"] == 99
    assert mapped["home_team_score"] == 3
    assert mapped["date"] == datetime.date(2024, 1, 1)

