# API Endpoints

All API routes are prefixed with `/api`. Authentication is required for endpoints that modify data.

## Athlete Profiles

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/athletes` | List athlete profiles. Supports pagination via `page` and `per_page` and basic search using `q`, `position` and `team` query parameters. |
| POST | `/api/athletes` | Create a new athlete profile. Requires `user_id`, `primary_sport_id`, `primary_position_id` and `date_of_birth`. |
| GET | `/api/athletes/<athlete_id>` | Retrieve a single athlete profile. |
| PUT | `/api/athletes/<athlete_id>` | Update an athlete profile. Auth required. |
| DELETE | `/api/athletes/<athlete_id>` | Soft-delete an athlete profile. Auth required. |

### Media

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/athletes/<athlete_id>/media` | List media attached to an athlete. |
| POST | `/api/athletes/<athlete_id>/media` | Upload a file for an athlete. Requires multipart `file` and optional `media_type`. Auth required. |
| DELETE | `/api/media/<media_id>` | Delete a media entry. Auth required. |
| GET | `/api/media/<media_id>/download` | Download a media file. |

### Stats

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/athletes/<athlete_id>/stats` | List stats for an athlete. |
| POST | `/api/athletes/<athlete_id>/stats` | Add or update a stat. Requires `name`. Auth required. |
| DELETE | `/api/stats/<stat_id>` | Delete a stat entry. Auth required. |

### Search

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/athletes/search` | Search athletes using query parameters such as `q`, `sport`, `position`, `team`, age/height/weight filters and the `filter` tab (nba, nfl, mlb, nhl, available, top). |

## Rankings

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/rankings/top` | Return the top five athletes using a temporary single-stat score (falls back to a small static list). |

## External Sports Data Proxies

These endpoints proxy public sports data APIs via the backend (handles auth and avoids CORS).

| Method | Endpoint | Upstream | Notes |
| ------ | -------- | -------- | ----- |
| GET | `/api/external/nba/teams` | BallDontLie NBA | Requires `NBA_API_TOKEN` or `BALLDONTLIE_API_TOKEN` |
| GET | `/api/external/nfl/teams` | BallDontLie NFL | Requires `NFL_API_TOKEN` or `BALLDONTLIE_API_TOKEN` |
| GET | `/api/external/mlb/teams` | MLB Stats API | No auth required |
| GET | `/api/external/nhl/teams` | NHL Stats API | No auth required |

Aliases:

- `/api/nba/teams`, `/api/nfl/teams`, `/api/mlb/teams`, `/api/nhl/teams`