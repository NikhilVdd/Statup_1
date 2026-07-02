# Loading... Arena PWA

Loading... Arena is a separate mobile-first PWA area inside the Loading... codebase.

It is intentionally isolated from the main sales teleprompter product.

## Routes

- `/pwa`
- `/pwa/feed`
- `/pwa/record`
- `/pwa/leaderboard`
- `/pwa/profile`
- `/pwa/manifest.json`
- `/pwa/service-worker.js`

## Files

- Templates: `pwa_mobile/templates/`
- CSS: `pwa_mobile/static/css/pwa.css`
- JavaScript: `pwa_mobile/static/js/pwa.js`
- Manifest: `pwa_mobile/static/manifest.json`
- Service worker: `pwa_mobile/static/service-worker.js`

## Isolation Rules

- PWA CSS classes are prefixed with `pwa-`.
- PWA JavaScript stays in `pwa_mobile/static/js/pwa.js`.
- The service worker only handles `/pwa` routes and `/pwa/static` assets.
- It does not cache dashboard, CRM, auth, live-call, or private client routes.

## Current Status

This is a mock-data PWA foundation:

- Mobile home screen
- TikTok-style pitch feed mockup
- 60-second record challenge UI with placeholder timer logic
- Mock leaderboard
- Mock profile
- Install prompt handling
- Safe PWA-only service worker cache

Video recording, uploads, voting persistence, comments, and real profiles are future work.
