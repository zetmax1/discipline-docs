---
paths:
  - "discipline/**"
---

# Web rules (discipline, React/TS)
- Local dates only through the date helper (`localDateString` in `src/lib/dates.ts`, or its successor); never `toISOString()` for dates.
- Server data through react-query; responses parsed with the zod schemas (`src/contracts/`). After changing a zod schema run `npm run contract:update` and commit `contracts/`.
- `contracts/` is generated: never hand-edit it. Product event names are defined there and nowhere else.
- No hardcoded UI strings: everything through i18n, keys in all three languages (`uz`, `ru`, `en`).
- Mobile first (390 px), then desktop; touch targets ≥ 44 px.
- Every screen: empty, loading, error, offline states.
- Accessibility: keyboard navigation, labeled inputs, WCAG AA contrast.
- Show the server's error message (translated from its code), never a generic "failed".
- No new dependency without checking its license and size.
- Tests: vitest for logic; one Playwright E2E per main flow (Playwright isn't set up yet: the first E2E adds it); screenshots at 390 px and 1440 px.
