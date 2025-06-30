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
