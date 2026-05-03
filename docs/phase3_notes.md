# Phase 3 Placeholder Metrics

The "Client Satisfaction" percentage displayed on the dashboard is currently hard-coded. It is intended as a placeholder metric for demonstration purposes.

In a future phase the client may provide survey data or a formula for calculating this value dynamically. The implementation should be revisited when those requirements are clarified.

## Analytics page

The dashboard now includes a **View Analytics** button linking to `/analytics`. This route displays a "Coming soon" message. Full reporting features are planned for Phase 5, so this button and page act as placeholders in Phase 3.

## Top Rankings

`/api/rankings/top` uses a **multi-factor weighted algorithm** implemented in `app/services/ranking_service.py`. Each athlete receives five independent component scores in the 0-100 range:

* **performance** — primary production stat per sport (NBA PPG, NFL passing yards, MLB batting average, NHL points, soccer goals) scaled against a rough maximum.
* **efficiency** — sport-specific advanced ratio (NBA TS%, NFL passer rating, MLB OPS, NHL +/-, soccer assists). Falls back to a neutral 50 when the underlying stat is unavailable.
* **durability** — games played versus the typical season length for the sport (e.g. 82 for NBA / NHL, 17 for NFL).
* **fan_perception** — *placeholder*. Currently uses a 50-baseline with small bumps for `is_featured` / verified athletes pending a real survey or social-sentiment data source.
* **market_value** — *placeholder*. Approximated from `overall_rating` and an experience curve until contract / endorsement data is available.

The final score is the weighted sum of the five components. Default weights are `{performance: 0.4, efficiency: 0.2, durability: 0.2, fan_perception: 0.1, market_value: 0.1}` and are auto-normalised when the caller supplies a partial dictionary.

New endpoints:

* `GET  /api/rankings/top?sport=&limit=` — leaderboard using either the authenticated user's default preset (if any) or the global defaults.
* `GET|POST /api/rankings/calculate` — ad-hoc rankings with custom weights passed via query string (`weights=performance=0.5,efficiency=0.3`) or JSON body.
* `GET  /api/rankings/presets` — list the current user's saved presets.
* `POST /api/rankings/presets` — save a preset (`name`, `sport`, `weights`, optional `is_default`).
* `DELETE /api/rankings/presets/<id>` — remove a preset.

Presets are persisted in the new `ranking_presets` table (see migration `7c4a91d3e5a2_add_ranking_presets`). The `fan_perception` and `market_value` components remain placeholders pending real data sources.

## Media upload

A new **Upload Media** option on the dashboard links to `/media/upload`. The page presents a simple form to pick an athlete and upload a file. This demonstrates the media workflow from Phase 2 without persisting large files during the demo.

## Customize Metrics button

The rankings page now exposes a **Customize Metrics** button that navigates to `/rankings/customize`. The customize view presents live sliders for the five component weights, an auto-normalising total, a live top-10 preview that re-queries `/api/rankings/calculate` as weights change, and controls to save the configuration as a preset (with an optional "set as default" toggle).

## Out of scope

Mobile applications and a cloud-hosted deployment are not included in Phases 1-3. The search bar on the homepage performs only basic filtering. Fan perception and market value remain heuristic placeholders pending real data inputs.
