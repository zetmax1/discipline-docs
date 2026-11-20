# F9a — Commitments, Weekly Targets, Calendar (ICS) Import, Smart Schedule on the server

Spec: M2 items 2, 3, 4, 9. Flag: `FEATURE_F9A` (id `F9A` in `GET /api/features`).
Repos: `discipline-back` (data, API, ICS parser, URL fetcher), `discipline-py` (generator input),
`discipline` (pages, contracts). Builds on F13 (categories and their `kind`, Day/Week views).
Out of scope: Google OAuth / Calendar API (F9b, M9), automatic daily refresh of URL imports (M4
worker), Smart Schedule redesign (M6), tasks/Top-3 (F10).

Revision 1 (2026-11-20) — draft for the owner.

## 1. Stories and acceptance criteria

- **S1: Commitments on the server (api, web).**
  - Fields: `name` (1–100), `kind` (F13's six kinds, used for colour and later metrics),
    `weekdays` (ISO 1–7, non-empty), `startMin` 0–1439, `endMin` 1–1440, `validFrom`, optional
    `validTo`. `startMin = endMin` is rejected; an end of `00:00` from the form is stored as 1440.
  - AC: `endMin < startMin` = crosses midnight. On each valid weekday D it expands to D
    `start→1440` and D+1 `0→end` — never D `0→end` (closes F-08). Weekdays and validity apply
    to the **start day**; the after-midnight part follows even when D+1 is past `validTo`.
  - AC: Mon–Fri 23:00–07:00 blocks Mon 23:00–24:00 and Tue 00:00–07:00, not Mon 00:00–07:00;
    a week view starting Monday also shows the previous Sunday's tail on Monday 00:00–07:00
    only when Sunday is one of its weekdays (test).
  - AC: CRUD, at most 100 commitments per user; offline edits queue in F1's sync queue with an
    `Idempotency-Key` (as F13 H1).
  - AC: quick-add presets in the editor: Sleep 23:00–07:00 every day (rest), University
    Mon–Fri 09:00–14:00 (study), Work Mon–Fri 09:00–18:00 (admin), Night shift 22:00–06:00
    (personal). Presets fill the form; nothing is saved until the user taps Save.
- **S2: One-time import of the browser's commitments and goals (web, api).**
  - AC: when F9A is on and `localStorage` holds `smart-schedule-commitments` or
    `smart-schedule-goals`, the page sends them once to `POST /commitments/local-import`, then
    removes both keys **only after a 2xx**. A toast says "Your N commitments are now saved to
    your account". Failure keeps the keys and retries on the next visit.
  - AC: idempotent across devices: an exact duplicate (same name, weekdays, start, end) is
    skipped; goals are applied only while the user has no saved targets.
  - AC: mapping: day names → ISO; `HH:MM` → minutes (`24:00` → 1440, end `00:00` → 1440);
    `validFrom` = today in the user's zone, no `validTo`; kind = `rest`/`study`/`exercise` when
    the name equals the translated example name for sleep/university/gym in uz, ru or en,
    `personal` otherwise (a fixed lookup, no guessing). Invalid items are counted, not saved.
- **S3: Weekly targets on the server (api, web).**
  - AC: minutes per week per category (0–4800, multiples of 15), `maxFocusMinPerDay`
    (null or 60–960, multiples of 15), `restDay` (null or ISO 1–7).
  - AC: a user without saved targets gets the current page defaults (Deep Work 15 h, Study
    10 h, Rest 7 h on the system categories, no cap, no rest day) with `isDefault: true`;
    nothing is written until they save.
  - AC: deleting a category drops its target; with `?reassignTo=` the minutes are added to the
    target category's (same transaction as F13's reassignment).
- **S4: Calendar import from a file or a secret iCal URL, preview first (api, web).**
  - AC: `.ics` upload (≤ 1 MiB) or an `https://` / `webcal://` URL (fetched per §4); nothing is
    saved by the preview.
  - AC: recurring events (`FREQ=DAILY|WEEKLY`, `INTERVAL=1`, `BYDAY`, `UNTIL`/`COUNT`, any
    `TZID` incl. `VTIMEZONE`) become candidate commitments with weekdays, local times and
    validity dates **in the user's zone** (§4.3). Pre-checked.
  - AC: one-off events in the next 56 days are listed unchecked; picking one creates a
    commitment with one weekday and `validFrom = validTo = date`.
  - AC: skipped events are summarised by reason (all-day, longer than 24 h, ended already,
    unsupported repeat, too many occurrences, unknown time zone) — counts only.
  - AC: per candidate the user can untick, rename and change the kind; "Add N commitments"
    saves them in one transaction.
  - AC: a URL source is stored (encrypted) and can be **refreshed manually**: the refresh shows
    the same preview marked new / changed / removed / unchanged and saves only on confirm.
  - AC: the Google Calendar DST fixture imports with the right weekdays and local times (test).
- **S5: Smart Schedule reads the server (web, api, analytics).**
  - AC: the page lists and edits server commitments and targets (S1, S3); the generator gets
    them from the API, never from the browser (§3.5).
  - AC: the generator's placement logic is unchanged except for the overnight split (S1) and
    validity dates of the chosen week; "Save plan" keeps the `plan_id` replace behaviour and
    sends the kind's system `categoryId`.
  - AC: targets of kinds the generator does not place yet (admin, exercise, personal) are saved
    and shown, with the note "The generator plans focus, study and rest for now".

**Moved:** the onboarding commitments step (M2 #2, last bullet) goes with M1 item 4
(onboarding), which is not built yet. It will reuse S1's presets and S4's import sheet as is.

## 2. Data & migrations

Migration number: the next free one at build time (expected `00015`; F13's contract migration
then takes the following number — goose rejects out-of-order files). Additive only: no existing
table or row changes, so the previous API runs on the new schema. Down drops the new tables.

```sql
-- +goose Up
CREATE TABLE calendar_sources (
  id              bigserial PRIMARY KEY,
  user_id         bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  url_ciphertext  bytea  NOT NULL,            -- AES-256-GCM, "v1" key id + nonce + ciphertext
  url_fingerprint bytea  NOT NULL,            -- HMAC-SHA256(key, normalised URL)
  url_host        text   NOT NULL CHECK (length(url_host) BETWEEN 1 AND 253),
  last_fetched_at timestamptz,
  last_status     text CHECK (last_status IN ('ok','blocked','failed','timeout','too_large','invalid')),
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, url_fingerprint)
);

CREATE TABLE commitments (
  id                 bigserial PRIMARY KEY,
  user_id            bigint   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name               text     NOT NULL CHECK (length(name) BETWEEN 1 AND 100),
  kind               text     NOT NULL CHECK (kind IN ('focus','study','admin','exercise','rest','personal')),
  weekdays           smallint[] NOT NULL
                     CHECK (coalesce(array_ndims(weekdays), 0) = 1
                            AND weekdays <@ '{1,2,3,4,5,6,7}' AND array_position(weekdays, NULL) IS NULL),
  start_min          integer  NOT NULL CHECK (start_min BETWEEN 0 AND 1439),
  end_min            integer  NOT NULL CHECK (end_min BETWEEN 1 AND 1440),
  valid_from         date     NOT NULL,
  valid_to           date     CHECK (valid_to IS NULL OR valid_to >= valid_from),
  source             text     NOT NULL CHECK (source IN ('manual','local_import','ics_file','ics_url')),
  calendar_source_id bigint   REFERENCES calendar_sources(id) ON DELETE SET NULL,
  external_key       bytea,   -- SHA-256(UID | run index); never the raw UID
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  CHECK (start_min <> end_min)
);
CREATE INDEX ix_commitments_user_valid ON commitments (user_id, valid_from);
CREATE UNIQUE INDEX uq_commitments_external ON commitments (user_id, external_key)
  WHERE external_key IS NOT NULL;              -- two devices confirming one import create one row

CREATE TABLE weekly_targets (
  user_id               bigint PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  max_focus_min_per_day integer CHECK (max_focus_min_per_day BETWEEN 60 AND 960
                                       AND max_focus_min_per_day % 15 = 0),
  rest_day              smallint CHECK (rest_day BETWEEN 1 AND 7),
  local_import_at       timestamptz,          -- S2: first browser import
  updated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE category_targets (
  user_id          bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id      bigint NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  minutes_per_week integer NOT NULL CHECK (minutes_per_week BETWEEN 0 AND 4800 AND minutes_per_week % 15 = 0),
  PRIMARY KEY (user_id, category_id)
);
-- +goose Down
DROP TABLE category_targets; DROP TABLE weekly_targets;
DROP TABLE commitments; DROP TABLE calendar_sources;
```

- `kind`, not `category_id` (owner: "commitments use F13's category kind"); colour = the user's
  system category of that kind. No FK to `categories`, so F13's delete/reassign is untouched.
- `category_targets`: the API checks the category is the caller's; `ON DELETE CASCADE` as in F13
  answer 4. No backfill: old commitments live only in browsers (S2).

## 3. API & contracts

All routes below exist only when `FEATURE_F9A=true` (404 otherwise, as F13). Auth: the user id
comes from the verified token; every `:id` is looked up with `AND user_id = $me` and answers 404
otherwise (no 403, so ids are not probeable).

### 3.1 Commitments and targets
- `GET /commitments` → `{ commitments: Commitment[] }`.
- `POST /commitments` (optional `Idempotency-Key`) → 201 `Commitment`. `source` is always
  `manual` here.
- `PUT /commitments/:id` `{ name, kind, weekdays, startMin, endMin, validFrom, validTo }` → 200.
  Editing an imported commitment keeps its `source` and `externalKey`; a later refresh shows
  it as "changed in the app" and does not overwrite it unless the user ticks it.
- `DELETE /commitments/:id` → 204.
- `GET /commitments/occurrences?startDate=&endDate=` (≤ 42 days) →
  `{ segments: [{ commitmentId, date, startMin, endMin, part: 'whole'|'evening'|'morning' }] }`.
  The expander (one Go function, §4.5) reads `startDate - 1` so Monday gets Sunday's tail.
- `POST /commitments/local-import` `{ commitments: LegacyCommitment[] (≤ 50), goals?: { deepWorkHours, studyHours, restHours } }`
  → 200 `{ imported, duplicates, invalid, targetsApplied }`. Sets `local_import_at` on first call.
- `GET /weekly-targets` → `WeeklyTargets = { categories: [{ categoryId, minutesPerWeek }], maxFocusMinPerDay: number|null, restDay: 1..7|null, isDefault: boolean }`.
- `PUT /weekly-targets` (same body minus `isDefault`) → 200; replaces all category rows in one
  transaction; an unknown or foreign `categoryId` → 400 `target_category_invalid`.

### 3.2 Calendar import
- `POST /calendar-import/preview`, one of:
  `multipart/form-data` with `file` (≤ 1 MiB, Gin `MaxBytesReader` before parsing);
  JSON `{ url }`; JSON `{ sourceId }` (refresh). → 200 `ImportPreview`:
  ```
  { source: { id: number|null, host: string } | null,
    candidates: [{ key, name, suggestedKind, weekdays, startMin, endMin, validFrom, validTo,
                   notes: ('dst_shift'|'until_horizon'|'exdates_ignored'|'overrides_ignored')[],
                   status: 'new'|'unchanged'|'changed'|'edited_in_app', commitmentId: number|null }],
    oneOffs:    [{ key, name, date, startMin, endMin, status }],   // next 56 days, ≤ 200
    removed:    [{ commitmentId, name }],                           // refresh only
    skipped:    { allDay, tooLong, ended, unsupportedRepeat, tooManyOccurrences, unknownTimezone, invalid } }
  ```
  `key` is hex `externalKey`; `suggestedKind` is always `personal` (no guessing from names).
  `Cache-Control: no-store`.
- `POST /calendar-import/commit` (optional `Idempotency-Key`)
  `{ url?: string, sourceId?: number, origin: 'file'|'url', items: [{ key, name, kind, weekdays, startMin, endMin, validFrom, validTo }] (≤ 200), removeIds?: number[] }`
  → 200 `{ created, updated, removed, sourceId: number|null }`. One transaction: upserts by
  `(user_id, external_key)`, deletes `removeIds` (must belong to that source). With `url` the
  source row is created or found by fingerprint (the URL is **not** fetched again). Items are
  validated exactly like `POST /commitments`; the client cannot exceed the 100 limit.
- `GET /calendar-sources` → `{ sources: [{ id, host, lastFetchedAt, lastStatus, commitmentCount }] }`.
  The URL itself is never returned.
- `DELETE /calendar-sources/:id?withCommitments=true|false` → 204 (default `false`: the
  commitments stay as manual ones, `calendar_source_id` set NULL).
- At most 5 sources per user (`calendar_source_limit`).

### 3.3 Rate limits (new policies in `middleware/rate_limiter.go`, keyed by user id)
| Policy | Limit | Applies to | Fail mode |
|---|---|---|---|
| `calendar_fetch` | 5 / min and 30 / day | preview with `url` or `sourceId` | **closed** (outbound fetch) |
| `calendar_parse` | 20 / min | preview with `file`, commit | open |
| existing `analytics` | 10 / min | `POST /analytics/smart-schedule` | unchanged |
Plus a process-wide semaphore of 8 concurrent outbound fetches; when full → 503 `ics_busy`, so
the API can't be used to flood a third-party host.

### 3.4 Errors (`errors.schema.json`, one `errors.*` key each)
`commitment_not_found`, `commitment_weekdays_invalid`, `commitment_times_invalid`,
`commitment_dates_invalid`, `commitment_kind_invalid`, `commitment_limit_reached`,
`targets_invalid`, `target_category_invalid`, `week_start_invalid`, `ics_file_too_large`,
`ics_invalid`, `ics_too_many_events`, `ics_url_invalid`, `ics_url_blocked`, `ics_fetch_failed`,
`ics_fetch_timeout`, `ics_too_large`, `ics_busy`, `calendar_source_not_found`,
`calendar_source_limit`. None echoes the URL, a resolved IP or a remote status body.

### 3.5 Smart Schedule (`POST /analytics/smart-schedule`)
- Flag on: the web sends `{ weekStart }` (a Monday, else 400 `week_start_invalid`). The Go proxy
  loads the user's commitments and targets, expands Mon–Sun of that week (validity, overnight
  split, Sunday-before tail) and forwards
  `{ weekStart, busy: [{ day, startMin, endMin, name, kind }], goals: {deepWorkHours, studyHours, restHours}, restDay, maxFocusMinPerDay }`.
  `goals` = sum of category targets by kind (focus, study, rest) in hours. The browser's body
  is still never forwarded raw.
- Flag off / previous web: the legacy `{ commitments, goals }` body is proxied as today.
- `discipline-py` `SmartScheduleRequest` accepts either shape (`busy` xor `commitments`).
  With `busy`, each segment removes its slots from that day and appears as a `fixed` block
  with its own times (so 23:00–24:00 Mon and 00:00–07:00 Tue are two blocks). The legacy path
  keeps its same-day wrap until the contract step removes it.
- `restDay` / `maxFocusMinPerDay` are forwarded; whether the generator uses them is open
  question 1.

### 3.6 Contracts (`discipline/contracts/`, generated from zod; `npm run contract:update`)
- `commitments.schema.json`: `Commitment = { id, name, kind, weekdays, startMin, endMin,
  validFrom, validTo: string|null, source, calendarSourceId: number|null, overnight: boolean }`,
  `CommitmentSegment`, `LegacyCommitment`, `LocalImportResult`.
- `targets.schema.json`: `WeeklyTargets`.
- `calendar-import.schema.json`: `ImportPreview`, `ImportCommit`, `ImportResult`, `CalendarSource`.
- `analytics.schema.json`: request v2 (`weekStart`, `busy`, `restDay`, `maxFocusMinPerDay`);
  py's contract test validates against it.
- `errors.schema.json`, `events.schema.json` (§7). Go contract tests cover every endpoint the web
  reads.

## 4. Calendar import: parsing, expansion, and the URL fetcher

### 4.1 URL fetcher (SSRF) — `internal/calendarfetch`
1. **Scheme:** `webcal://` is rewritten to `https://`; anything but `https` → `ics_url_invalid`.
   No userinfo, port 443 only (empty or `:443`), host ≤ 253 chars, URL ≤ 2048 chars.
2. **Host names:** IP literals (v4, v6, decimal/octal/hex forms — rejected by requiring a
   hostname that `netip.ParseAddr` does not accept and that contains a letter), `localhost`,
   `*.localhost`, `*.local`, `*.internal` (covers `*.railway.internal`), `*.home.arpa` → `ics_url_blocked`.
   The name is lower-cased and IDNA-normalised before the check, trailing dot removed.
3. **Every connection** goes through a `net.Dialer` whose `Control` hook checks the **actual
   remote IP** after resolution, so DNS rebinding and redirects to a new host are covered by the
   same check. Rejected (after `Unmap()`): not `IsGlobalUnicast()`, `IsPrivate()`,
   `IsLoopback()`, `IsLinkLocalUnicast()`, `IsLinkLocalMulticast()`, `IsMulticast()`,
   `IsUnspecified()`, and explicitly `0.0.0.0/8`, `100.64.0.0/10`, `169.254.0.0/16`,
   `192.0.0.0/24`, `192.0.2.0/24`, `198.18.0.0/15`, `198.51.100.0/24`, `203.0.113.0/24`,
   `240.0.0.0/4`, `fc00::/7` (Railway's private network is `fd12::/16`), `64:ff9b::/96` and
   `2002::/16` (their embedded IPv4 is checked too), `2001:db8::/32`. Every resolved address
   of the name must pass, otherwise the fetch fails (no "try the next address").
4. **Redirects:** at most 3; each `Location` goes through steps 1–2 again in `CheckRedirect`
   (https only, no downgrade), and step 3 runs on the new connection.
5. **Transport:** `Proxy: nil` (ignores `HTTP_PROXY`), no cookies, no auth header, our own
   `User-Agent: DisciplineCalendarImport/1`, `Accept: text/calendar`. TLS verification on, TLS 1.2+.
6. **Limits:** whole fetch 10 s (`context.WithTimeout`); dial 3 s, TLS handshake 5 s, response
   header 5 s. Status must be 200. `Content-Length > 2 MiB` → `ics_too_large` before reading;
   the body is read through `io.LimitReader(2 MiB + 1)` **after** Go's transparent gzip
   decoding, so a compressed bomb is cut at 2 MiB too. Content-Type is not trusted.
7. **Logging:** only `host`, outcome code, duration, byte count. Never path, query, the
   resolved IP of a blocked target, or body bytes. The URL is never in Sentry context.

### 4.2 Parser limits (file and URL alike)
≤ 1 MiB file / 2 MiB URL body; ≤ 3 000 `VEVENT`s (`ics_too_many_events`); unfolded line ≤ 8 KiB;
`SUMMARY` cut to 100 runes, control characters stripped; whole preview ≤ 3 s CPU (context
checked in the expansion loop). Libraries (licenses recorded in `THIRD_PARTY.md`):
`github.com/arran4/golang-ical` (Apache-2.0) for parsing, `github.com/teambition/rrule-go` (MIT)
for RRULE, CLDR `windowsZones.xml` (Unicode License v3) embedded for Outlook's Windows zone names.

### 4.3 From an event to candidate commitments
1. Skip: all-day (`VALUE=DATE`), duration ≥ 24 h or ≤ 0, `STATUS:CANCELLED`,
   `FREQ` other than `DAILY`/`WEEKLY`, `INTERVAL > 1`, `BYSETPOS`/`BYMONTHDAY`/`BYYEARDAY`/`BYWEEKNO`
   → counted in `skipped`.
2. Zone of `DTSTART`: `Z` = UTC; `TZID` → IANA name, else the CLDR Windows map, else the
   file's `VTIMEZONE` observances (STANDARD/DAYLIGHT with their RRULEs, expanded under the same
   cap), else `unknownTimezone`. Floating times use the user's zone.
3. Expand occurrences in `[max(DTSTART, today), min(UNTIL/COUNT end, today + 366 d)]`, **at most
   1 000 per event and 20 000 per import** (`tooManyOccurrences`; total cap → `ics_too_large`).
   `HOURLY` and finer are never expanded (rule 1).
4. Convert each occurrence's start and end to the user's zone → (local date, weekday,
   startMin, endMin). An end on the next local day → overnight (`endMin < startMin`).
5. Group by `(startMin, endMin)` into runs of consecutive weeks; each group becomes one
   candidate with the union of weekdays, `validFrom` = its first date, `validTo` = its last
   date. The last group is open-ended (`validTo = null`) only when the rule has no end **and**
   only one group exists (the zones keep the same offset relation all year). Otherwise it gets
   `validTo` = horizon and the note `until_horizon` ("refresh to extend").
   Two groups for one event (zone with DST seen from a zone without, e.g. Europe/Berlin class
   for a Tashkent user) carry the note `dst_shift`.
6. `EXDATE` and `RECURRENCE-ID` overrides are not kept (notes `exdates_ignored`,
   `overrides_ignored`); see open question 4.
7. `externalKey = SHA-256(UID || ':' || group index)`; on refresh, matching keys give
   `unchanged`/`changed`, a commitment of this source whose key is gone appears in `removed`,
   and one edited in the app since the last import (`updated_at > last_fetched_at`) is
   `edited_in_app` and unticked.
8. One-offs: non-recurring events whose start is in `[today, today + 56 d]`.

### 4.4 Secret URL storage
AES-256-GCM with `CALENDAR_URL_KEY` (32 random bytes, base64). Required when `FEATURE_F9A=true`:
the API refuses to start without it, and has no default. Ciphertext = `v1` key id ‖ 12-byte
nonce ‖ sealed URL, so a later key rotation can re-encrypt. `url_fingerprint` (HMAC with a key
derived from the same secret) finds a duplicate source without decrypting. The URL is decrypted
only inside a refresh preview.

### 4.5 Expansion of commitments (one function, Go)
`Expand(commitments, from, to, loc) []Segment`: for each date `d` in `[from - 1, to]` with
`isoWeekday(d)` (F13 §4.2 conversion) in `weekdays` and `validFrom ≤ d ≤ validTo`: not overnight →
`(d, start, end, whole)`; overnight → `(d, start, 1440, evening)` and `(d + 1, 0, end, morning)`;
keep only segments with `from ≤ date ≤ to`. Used by `GET /commitments/occurrences`, the Smart
Schedule proxy, and (open question 2) the planner views.

## 5. Jobs and notifications
None. Daily refresh waits for the M4 worker (reuses §4.1 and the diff; never auto-applies).

## 6. Screens

**Smart Schedule page** (`/schedule`), 390 px: one column — (1) *Fixed times* list: card per
commitment with kind colour dot, name, weekdays ("Mon–Fri"), "23:00 – 07:00 (next day)",
validity when set; tap opens the editor sheet (name, kind, weekday pills ≥ 44 px, start/end
selects in 15-min steps, "From"/"Until" dates, presets row). Buttons "Add" and "Import
calendar". (2) *Weekly targets*: a row per category (translated default names, F13 rule) with
a 0.5 h stepper, "Max focus per day" select (No limit, 1–16 h), "Rest day" pills (None,
Mon…Sun), Save. (3) week picker + Generate + result as today.
Desktop ≥ 1024 px: two columns — left (1)+(2), right (3); the editor and import open as dialogs
(max-w-2xl).

**Import sheet/dialog:** tabs *File* | *Link*. Link tab: field + hint "In Google Calendar:
Settings → your calendar → Secret address in iCal format" + privacy line "We store this link
encrypted and only use it to read your calendar." → *Reading your calendar…* → **Preview**:
"Repeating" (checked rows, editable name and kind, notes as quiet chips), "One-time, next 8
weeks" (unchecked), "Not imported" (collapsed counts by reason), sticky footer "Add N
commitments". Refresh shows the same list with status chips New / Changed / Removed /
Edited by you. *Linked calendars* list: host, "Updated <date>", Refresh, Remove (dialog: keep
or remove its commitments).

| State | Fixed times / targets | Import |
|---|---|---|
| Empty | "No fixed times yet. Add classes, work or sleep so plans leave them free." + presets + Import | "No repeating events found" + one-offs if any |
| Loading | skeleton cards / rows (`aria-busy`) | step text "Reading your calendar…", cancel |
| Error | translated server message + "Try again" | per-code message, e.g. `ics_url_blocked`: "This link can't be used. Copy the secret iCal address from your calendar settings." |
| Offline | cached list; edits queue (banner "Saved on this device, syncs when you're online") | disabled: "Importing needs a connection"; Generate disabled likewise |

i18n (flat keys, en/uz/ru parity, `local/no-ui-literal`): `commitments.*` (list, editor,
presets, `.nextDay`, `.overnightHint`, `.localImported`), `targets.*` (`.title`, `.perWeek`,
`.maxFocus`, `.noLimit`, `.restDay`, `.none`, `.notPlacedYet`, `.saved`), `calendarImport.*`
(tabs, hints, privacy, preview sections, notes, statuses, skipped reasons, sources),
`schedule.*` (existing, `.default.*` kept for S2's lookup), `errors.*` for §3.4.
All copy is encouraging: a one-off left unticked or a skipped event is never "failed".

## 7. Product events
| Event | When | Props (no personal data) |
|---|---|---|
| `commitment_created` (new) | each created commitment, any source | `source`, `kind`, `overnight`, `weekday_count` |
| `calendar_imported` (new) | a commit that created or updated ≥ 1 | `origin` (`file`/`url`), `refresh`, `created`, `updated`, `removed`, `one_offs` |
Local import records `commitment_created` with `source=local_import`. No event or log carries a
name, URL, host or UID. Replays (`Idempotency-Key`) record nothing twice.

## 8. Edge cases
- **Timezone & DST:** commitments are wall-clock minutes in the user's zone (09:00 stays 09:00).
  Import converts from the event's zone per occurrence (§4.3), so DST shifts become separate
  candidates instead of wrong times. A segment on a spring-forward day keeps its minutes (F13).
  A user changing their zone: commitments keep their wall-clock times (stated in the editor).
- **Midnight:** overnight split on the start day; Sunday's tail lands on next Monday and the
  Monday of the viewed week takes the previous Sunday's tail; `validTo` = Friday still blocks
  Saturday 00:00–07:00. "Today" for `validFrom`, the import window and S2 is computed at the
  request in the user's zone; tests at 23:59 and 00:00 local.
- **Several devices:** commitments last-write-wins like blocks; local import dedupes; two
  devices confirming one import hit `uq_commitments_external` and upsert one row.
- **Offline:** CRUD queues; import, refresh and Generate need a connection and say so.
- **Brand-new user:** no commitments, default targets (`isDefault`), empty states; Generate
  works with no busy time.
- **Deleted account:** cascades remove commitments, targets, sources (ciphertext included).
- **Blocks over a commitment** are allowed (the user decides); the generator never places there.
- **A huge or hostile calendar:** §4.1–4.2 limits; a timeout or block leaves `last_status` set
  and the source listed with "Couldn't refresh — try again later".

## 9. Security and privacy
- Authorization: every route requires the token; every row is scoped by `user_id`; `sourceId`,
  `removeIds`, `categoryId` and `:id` are checked to be the caller's (404 / 400).
- SSRF: §4.1, enforced in the dialer, not by pre-resolution alone. Covered by unit tests with a
  fake resolver and by a test server bound to 127.0.0.1 that must never receive a request.
- Secret URL: encrypted at rest, never returned, logged or sent to analytics; the API response
  shows only the host. Files are parsed in memory and never stored.
- Personal data added: commitment names and times, targets, calendar hosts. **Export** (when
  the user-data export endpoint lands — F13 deferred it too): `commitments`, `weekly_targets`,
  `category_targets`, `calendar_sources` as `{ host, lastFetchedAt }` — the secret URL is a
  credential and is not exported. **Delete**: cascades (tested).
- Logs: no names, SUMMARY, URL path/query, UIDs, file names or body bytes.

## 10. Test plan
**discipline-back**
- Migration up/down on a production-shaped copy; old API binary's queries still run.
- Expander: the M2 overnight test (Mon–Fri 23:00–07:00); Sunday tail into Monday and from the
  previous week; `validTo` on Friday; validity edges; weekday conversion across a Sunday.
- Commitments CRUD: CHECKs (empty weekdays, 0/8, `start = end`, `valid_to < valid_from`), 100
  limit, 404 for another user's id, idempotent create replay.
- Local import: mapping, duplicates across two calls, goals only when no targets, invalid count.
- Targets: defaults with `isDefault`, foreign category → 400, reassign adds minutes, delete drops.
- ICS fixtures (`testdata/ics/`, synthetic, no real calendars): Google export with weekly
  classes in `Europe/Berlin` over the March DST change (Berlin user → 1 candidate; Tashkent user
  → 2 with `dst_shift`); `America/New_York` November fall-back; Outlook Windows TZID +
  `VTIMEZONE`; UTC and floating times; `COUNT`; `UNTIL` in the past (ended); overnight 23:00–01:00;
  all-day, 25 h, `INTERVAL=2`, `FREQ=MONTHLY`, `HOURLY`, EXDATE note; 3 001 events; a daily rule
  without end (cap 1 000); 20 001 total; malformed lines; refresh diff (new, changed, removed,
  edited in app).
- Fetcher: `http://`, userinfo, port 8443, IP literals (`127.0.0.1`, `[::1]`, `2130706433`,
  `0x7f.1`), `metadata.railway.internal`, `foo.internal`; a name resolving to `10.0.0.5`,
  `169.254.169.254`, `fd12::1`, `::ffff:127.0.0.1`, `64:ff9b::a00:1`, and to one public + one
  private address; a redirect from an allowed host to `http://`, to a private host, and a 4th
  redirect; DNS rebinding (first lookup public, second private); slow headers (timeout), slow
  body, 3 MiB body, `Content-Length: 3 MiB`, gzip bomb, non-200. Uses an injected resolver and
  dialer; no real network in tests.
- Rate limits: `calendar_fetch` closed when Redis is down; semaphore → 503.
- Smart Schedule proxy: flag on builds `busy` from the DB (overnight as two segments, validity
  of the chosen week), legacy body still proxied when off; `week_start_invalid`.
- Events: names from `events.schema.json` only; props without personal data; no double record.
- Logs: a test captures log output during an import and asserts no URL path, name or UID.

**discipline-py**
- `busy` segments block exactly their slots (Mon 23:00–24:00 and Tue 00:00–07:00 free of
  plans, Mon 00:00–07:00 free for planning); legacy path unchanged; `busy` xor `commitments`;
  contract test against the new `analytics.schema.json`.

**discipline (web)**
- Commitments list/editor (overnight label, presets, validation), targets form, import preview
  (tick/untick, rename, kind, statuses, skipped counts), sources list; four states each.
- S2: keys removed only after 2xx; failure keeps them; no import when the flag is off.
- i18n parity, no UI literal, contract parse of every response.
- Playwright 390×844 and 1440×900 (screens to `docs/design/F9a-screens/`):
  (1) local data present → moved to the server, toast, keys gone; (2) import the Google DST
  fixture file → preview → add → commitments listed with the right times; (3) link import
  against a mocked API (no outbound fetch in E2E) incl. the `ics_url_blocked` message;
  (4) overnight sleep + timetable + targets → Generate → no plan block in Mon 23–24 or Tue 0–7,
  Save plan; (5) offline: list from cache, import disabled.

## 11. Rollout
- **Flag** `FEATURE_F9A` (off by default). With it on, the API also requires
  `CALENDAR_URL_KEY` and refuses to start without it.
- **Precondition:** F13 merged and deployed (00014 applied); see open question 3.
- **Order** (each step works with the previous version of the others):
  1. `discipline-back`: new migration in the pre-deploy step, flag off. Additive tables only;
     the legacy smart-schedule body is still accepted.
  2. `discipline-py`: accepts `busy` and the legacy body.
  3. `discipline`: flag off → the page behaves as today (localStorage).
  4. Set `CALENDAR_URL_KEY`, then `FEATURE_F9A=true` on staging; walk the E2E flows; production.
  5. Next release (contract): drop the legacy `{ commitments, goals }` path in py and the proxy,
     and the web's localStorage code — once no traffic uses it for 2 weeks.
- **Rollback:** flag off returns the page to localStorage (S2 already cleared those keys for
  migrated users, so the page then shows its examples; their data is safe on the server and
  returns when the flag is on). `goose down` drops the four tables.
- **Owner steps:** `openssl rand -base64 32` → Railway variable `CALENDAR_URL_KEY` on the API
  service (staging and production get different keys); no other new env vars.

## 12. Open questions (owner)
1. **Rest day and max focus in the generator.** Spec #9 keeps the current logic. Recommend a
   minimal use now: no focus/study on the rest day, and focus capped per day at
   `maxFocusMinPerDay` (overflow goes to other days or shortfall). Or store only and wait for M6?
2. **Hatched commitments in F13's Day/Week views** (M2 #6 wording). Recommend yes in F9a: the
   views call `GET /commitments/occurrences` for the visible range; a small web-only story.
   Or a separate follow-up?
3. **Branch base.** F13 is not merged into `main` yet. Build F9a only after F13 merges
   (recommended), or branch `feat/F9a` from `feat/F13` and rebase later?
4. **Calendar exceptions (EXDATE, moved single instances).** Recommend ignoring them in F9a with a
   visible note (holidays stay blocked; the user can still plan there). The alternative is a
   `commitment_exceptions` table (like `recurring_exceptions`), roughly +1 day of work.
