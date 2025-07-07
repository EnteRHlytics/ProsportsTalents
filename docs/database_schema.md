# Database Schema

The backend uses a PostgreSQL database managed through SQLAlchemy. Key tables and relationships are outlined below.

```
users (user_id PK)
  |--< user_roles (user_role_id PK)
  |      |-- user_id FK -> users.user_id
  |      `-- role_id FK -> roles.role_id
  |--< user_oauth_accounts (account_id PK)
  |      `-- user_id FK -> users.user_id
  `--1 athlete_profiles (athlete_id PK, user_id FK -> users.user_id)
          |--< athlete_media (media_id PK, athlete_id FK)
          |--< athlete_stats (stat_id PK, athlete_id FK)
          `--< athlete_skills (skill_id PK, athlete_id FK)

roles (role_id PK)

sports (sport_id PK)
  `--< positions (position_id PK, sport_id FK)

athlete_profiles
  |-- primary_sport_id FK -> sports.sport_id
  `-- primary_position_id FK -> positions.position_id
```

Each `AthleteProfile` record is associated with exactly one `User`. Media, stats and skills reference the athlete profile via foreign keys. Sports have many positions, and each athlete is linked to a sport and position.

Key fields on `athlete_profiles` include:

* `contract_active` – indicates if the athlete currently has an active team contract.
* `created_at` – timestamp when the profile was first created.
* `is_featured` – when true the athlete appears in the Featured grid on the homepage.

Additional tables for NBA integration:

```
nba_teams (team_id PK)
  |--< nba_games (game_id PK, home_team_id FK -> nba_teams.team_id, visitor_team_id FK -> nba_teams.team_id)
```

Additional tables for MLB integration:
```
mlb_teams (team_id PK)
```

Additional tables for NFL integration:
```
nfl_teams (team_id PK)
```

## Extended multi-sport stats schema

To support historical statistics across NBA, MLB, NHL and NFL the following
generic tables are introduced:

```
teams (team_id PK, sport_id FK -> sports.sport_id)
  |--< games (game_id PK, sport_id FK -> sports.sport_id,
             home_team_id FK -> teams.team_id,
             visitor_team_id FK -> teams.team_id)
  |      `--< game_stats (game_stat_id PK, game_id FK -> games.game_id,
                         athlete_id FK -> athlete_profiles.athlete_id)
  `--< season_stats (season_stat_id PK, team_id FK -> teams.team_id,
                     athlete_id FK -> athlete_profiles.athlete_id)
```

`season_stats` stores aggregated values per athlete and season, while
`game_stats` captures per-game lines.  Each record references the related
sport and team so multi-season histories can be stored for different leagues.

Key indexes exist to speed up stat retrieval:

* `athlete_stats`: `athlete_id`, `season`, and the combination
  `(athlete_id, season)`.
* `season_stats`: `athlete_id`, `season`, `team_id` and `(athlete_id, season)`.
* `game_stats`: `game_id`, `athlete_id` and `(athlete_id, game_id)`.

Unique constraints prevent duplicate records:

* `season_stats`: `(athlete_id, season, name)`
* `game_stats`: `(athlete_id, game_id, name)`
Scores in all game tables must be non-negative.
