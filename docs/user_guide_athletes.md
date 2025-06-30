# Managing Athlete Profiles

This guide explains common tasks for administrators managing athlete profiles through the API.

## Creating a Profile

1. Ensure the related `User` account exists.
2. Send a `POST` request to `/api/athletes` with JSON body:

```json
{
  "user_id": "<user id>",
  "primary_sport_id": 1,
  "primary_position_id": 2,
  "date_of_birth": "1995-09-01"
}
```

The response includes the newly created `athlete_id`.

## Updating Details

Use `PUT /api/athletes/<athlete_id>` with the fields you want to change. Example:

```json
{
  "bio": "All‑star forward for the home team",
  "primary_position_id": 3
}
```

## Uploading Media

Media files (photos, highlight reels) can be uploaded with:

```
POST /api/athletes/<athlete_id>/media
Content-Type: multipart/form-data
file=<file> media_type=image
```

List media using `GET /api/athletes/<athlete_id>/media` and delete with `DELETE /api/media/<media_id>`.

## Recording Stats

To add or update stats for a season:

```json
POST /api/athletes/<athlete_id>/stats
{
  "name": "points",
  "value": "1200",
  "season": "2023"
}
```

## Searching Profiles

Use `GET /api/athletes/search` with query parameters such as `q`, `sport`, `position` or `team` to find athletes.

## Deleting a Profile

A soft delete is performed with `DELETE /api/athletes/<athlete_id>`; the record remains but is hidden from default queries.
