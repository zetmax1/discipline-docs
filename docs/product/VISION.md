# Discipline Tracker — Product vision

Read this file for principles, vocabulary and constraints. Read only the milestone file you are working on in `docs/product/milestones/`.

## One line
A planner that helps people build discipline **and** rest properly: plan the week, do the work, recover, and learn what works for you.

## Audience
Students, office workers and developers. Uzbekistan first. UI languages: Uzbek (Latin, default for UZ), Russian, English. Mostly used on phones. Heavy Telegram users.

## Principles (every feature must respect them)
1. **Discipline and rest are equal goals.** Sleep, rest blocks and breaks are planned, protected and counted. The app prevents overwork; rest is never shown as wasted time or failure.
2. **Logging takes seconds.** One tap, sensible defaults, reminders where people already are (Telegram, push).
3. **No shame.** Encouraging copy. Rest days and streak freezes never break streaks. No "failure" screens, no guilt notifications.
4. **Learn → suggest → the user decides.** Every suggestion says why. Nothing is applied automatically.
5. **Honest numbers.** No metric without data behind it. "Not enough data yet (N more days)" beats fake precision. Rules are never called "AI".
6. **Privacy by default.** Personal data is private; sharing is opt-in; export and delete anytime; no ads, no third-party trackers, no biometric data.
7. **Not a medical app.** No diagnoses or health claims. Wellbeing tips stay general.

## Core daily loop
Morning check-in (~10 s: sleep, sleep quality, energy) → Today: Top-3 priorities + blocks from the accepted weekly plan → focus sessions with breaks → one-tap block check-ins → evening shutdown (move unfinished, one win, tomorrow's Top-3) → wind-down reminder before bedtime → Sunday weekly review → next week's suggested plan.

## Glossary (use these names in code, API and UI)
| Term | Meaning |
|---|---|
| **Block** | A time slot on a date: category, planned start/end, actual start/end, status, focus rating, distractions. Today's DB table is `tasks`; the concept is "block". |
| **Block status** | `planned → in_progress → done \| partial \| skipped \| moved`. `moved` links to the new block. Skipped and moved blocks never count for overlaps. |
| **Task / Top-3** | A to-do item (title, done, optional due date, optional linked block). Top-3 = up to 3 ordered tasks chosen for a day. |
| **Commitment** | Recurring fixed time the planner must not use (sleep, university, work, prayer). Weekdays + start/end + validity dates. End before start = crosses midnight, split at midnight when expanded. |
| **Category** | User-editable name, color, icon + a fixed **kind**: `focus`, `study`, `admin`, `exercise`, `rest`, `personal`. Metrics and rules use **kind**, never the name. |
| **Goal** | Weekly target minutes per category, plus max focus minutes per day and the preferred rest day. |
| **Check-in** | Morning: sleep start/end, quality 1–5, energy 1–5. Evening: shutdown. |
| **Focus session** | A timed work interval (inside or outside a block) followed by a break. Server stores start time; clients compute the countdown. |
| **Plan draft** | A versioned weekly suggestion. Accepting it creates blocks with `source=plan` and a `plan_id`. |
| **Rest day** | A day with no focus targets; task reminders silenced; neutral for streaks. |
| **Load / Recovery** | Load = completed minutes of kinds focus+study+admin. Recovery = sleep + rest-kind blocks + breaks taken. |

## Time rules
- Every "today", week and month is computed in the user's IANA timezone (stored on the user). Weeks start Monday.
- Times of day are minutes 0–1440 (1440 = end of day). Dates are `YYYY-MM-DD` local dates.
- DST and midnight cases are tested for anything that schedules, groups or notifies.

## Product metrics (events go to the internal `product_events` table only)
- **Activation:** onboarding completed + first weekly plan accepted (or ≥5 blocks planned) within 7 days of signup.
- **Retention:** D1 / D7 / D30 (any check-in, block check-in or session that day).
- **Habit of use:** morning check-in rate, block check-in rate, focus sessions per week.
- **Planning quality:** plan acceptance rate, share of suggested blocks completed.
- **Balance:** rest-day adherence, days over the user's max focus.
- **Noise:** notification opt-out rate per type.
Event names are defined once in `discipline/contracts/` and nowhere else.

## Architecture constraints
- Three repos: `discipline` (web, React/TS, PWA), `discipline-back` (api, Go/Gin, owns the DB and auth; from M4 also the worker as `cmd/worker`, Go + Asynq on Redis, sharing the API's models and migrations), `discipline-py` (analytics, FastAPI: metrics and the learning engine, read-only DB access).
- Postgres + Redis. Versioned migrations only (goose), each with a Down step.
- API contracts live in `discipline/contracts/` (JSON Schema generated from the web's zod schemas). Backend tests validate their responses against these files (path from `CONTRACTS_DIR`, default `../discipline/contracts`).
- A change that touches several repos uses the same branch name in each (`feat/M{N}`); the design doc's rollout section gives the deploy order.
- Each repo has one local check command (`make check` / `npm run check`) that runs lint, types and tests. CI/CD comes later and will call the same commands.
- Each milestone ships behind a feature flag (`FEATURE_M{N}`) until accepted.
- Append-only event tables for blocks, sessions, check-ins and plan suggestions (the learning engine needs history).
- Third-party content and libraries must have licenses that allow this use; record the source and license of every content item.

## Non-goals
Medical advice; ads or selling data; biometric data; leaderboards by hours; automatically applied plans; dark patterns (fear of losing streaks, nagging, guilt).

## Milestones
| ID | Theme | Depends on |
|---|---|---|
| M1 | Public foundation: auth v2, onboarding, settings, i18n, mobile shell, legal, export/delete, admin basics | — |
| M2 | Planner v2: categories, persisted commitments & goals, block lifecycle, week view, recurring blocks, Top-3 | M1 |
| M3 | Daily loop: morning check-in, Today screen, focus sessions, block check-ins, evening shutdown | M2 |
| M4 | Worker, notifications, Telegram bot, web push, beta gate → **closed beta starts** | M3 |
| M5 | Habits, streak rules, rest & balance warnings, rest-day mode | M4 |
| M6 | Learning engine, plan drafts, insights (client charts), weekly review | M5 + ≥2 weeks of beta data |
| M7 | Language learning: licensed content, placement, FSRS, games | M4 |
| M8 | Motivation (XP, achievements, coins), mini-games, Telegram Mini App | M6, M7 |
| M9 | Social (opt-in), AI coach (opt-in), admin analytics — re-scope after beta | M8 |
