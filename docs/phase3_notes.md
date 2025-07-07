# Phase 3 Placeholder Metrics

The "Client Satisfaction" percentage displayed on the dashboard is currently hard-coded. It is intended as a placeholder metric for demonstration purposes.

In a future phase the client may provide survey data or a formula for calculating this value dynamically. The implementation should be revisited when those requirements are clarified.

## Analytics page

The dashboard now includes a **📊 View Analytics** button linking to `/analytics`. This route displays a "Coming soon" message. Full reporting features are planned for Phase 5, so this button and page act as placeholders in Phase 3.

## Top Rankings

The `/api/rankings/top` endpoint now calculates a basic ranking from any
athletes stored in the database. It uses a simple single-stat formula for each
sport (for example NBA points per game) to assign a score out of 100. If no
athlete data exists it will still return a small hard-coded list. This logic is
explicitly temporary and will be replaced by a multi-metric algorithm in
Phase 4.

## Media upload

A new **📁 Upload Media** option on the dashboard links to `/media/upload`. The page presents a simple form to pick an athlete and upload a file. This demonstrates the media workflow from Phase 2 without persisting large files during the demo.

## Customize Metrics button

The rankings page now displays a **⚙️ Customize Metrics** button. In Phase 3 this opens a modal dialog explaining the feature is coming soon. The modal shows read-only sliders for weighting factors to signal future support for ranking customization.

## Out of scope

Mobile applications and a cloud-hosted deployment are not included in Phases 1–3.
The search bar on the homepage performs only basic filtering and the ranking
algorithm is a simple placeholder. More advanced functionality will arrive in
later phases.
