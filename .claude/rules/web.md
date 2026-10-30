---
paths:
  - "discipline/**"
---

# Web rules (discipline, React/TS)
- Local dates only through the date helper (`localDateString` in `src/lib/dates.ts`, or its successor); never `toISOString()` for dates.
- Server data through react-query; responses parsed with the zod schemas (`src/contracts/`). After changing a zod schema run `npm run contract:update` and commit `contracts/`.
- `contracts/` is generated: never hand-edit it. Product event names are defined there and nowhere else.
- No hardcoded UI strings: everything through i18n (`useI18n().t`, dictionaries in `src/i18n/`; `en.ts` is the key list, `uz.ts`/`ru.ts` must match). `local/no-ui-literal` (ESLint) and `src/i18n/messages.test.ts` enforce it. Dates/numbers via `useI18n().formatDate/formatNumber` (Uzbek is built in: browser Intl data for `uz` is unreliable). API errors via `errorMessage(err, fallbackKey)`.
- Mobile first (390 px), then desktop; touch targets ≥ 44 px (with F12A on, `index.css` enforces it below 768 px; `e2e/touch-targets.ts` checks it). Dark mode: colours only through the design tokens (or with `dark:` variants).
- Every screen: empty, loading, error, offline states.
- Accessibility: keyboard navigation, labeled inputs, WCAG AA contrast.
- Show the server's error message (translated from its code), never a generic "failed".
- No new dependency without checking its license and size.
- Feature-flagged UI goes inside `<Feature flag="F…">` (`src/components/Feature.tsx`) or behind `useFeature`; off unless `GET /api/features` lists it.
- Tests: vitest for logic; one Playwright E2E per main flow in `e2e/` (production build via `vite preview`, API mocked with `mockApi`, projects at 390 px and 1440 px; part of `npm run check`). Screenshots: `E2E_SCREENSHOTS=$(realpath ../docs/design/<id>-screens) npx playwright test`.
