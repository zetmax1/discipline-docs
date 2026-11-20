# F13 build review (cold read of `main...feat/F13` in all three repos, 2026-11-20)

I reviewed the design doc, VISION, the three diffs and the code around them. I ran no checks, and every
finding below was verified in the code unless it is marked *uncertain*. Authorization held up: every new
endpoint filters by the token's user id. `categoryId` on blocks and rules, `reassignTo`, `:id` on rules,
occurrences and place-anyway/skip are all checked against the caller, and the integration tests cover
cross-user attempts. I found no logging of personal data and no copy that shames.

Counts: **Blocker 0 · High 4 · Medium 9 · Low 12**

---

## Blocker

None found.

---

## High

**H1 — Offline-queued creates of rules and blocks are not idempotent (breaks the sync-queue rule)**
`discipline/src/lib/planner-api.ts:53` (`createRule`), `:84` (`createBlock`);
`discipline-back/internal/handlers/recurring_handler.go:330`, `internal/handlers/task_handler.go` (`CreateTask`).
- The client sends no `Idempotency-Key`, and the server neither reads one nor uses F1's
  `idempotency_keys` table, which only `MoveTask` uses (`task_repository.go:365-414`).
- `sync-queue.ts` states that "every queued request is replay-safe on the server". `sendOrQueue`/`flush`
  re-send a request after a `TypeError` or a 5xx, even when the server already committed it (the response
  was lost, or a proxy returned 502 after the commit).
- A replayed `POST /recurring-rules` creates a second identical rule. Every occurrence of that rule then
  clashes with the first rule's occurrence and becomes a permanent "didn't fit" conflict marker, every
  week.
- The web has no rule list, so the duplicate cannot be deleted from the UI: its occurrences never exist,
  so "delete this and following" is never reachable.
- A replayed `POST /tasks` is only saved by accident: the copy overlaps the original, gets a 409, and is
  dropped with a confusing "couldn't sync" toast.
- The design's Status lists this as "deferred, small risk". It is not small for rules.
- Fix: the client sends `Idempotency-Key: <queue key uuid>` on both POSTs. The server stores
  `(user_id, key) → resource_id` in `idempotency_keys` inside the create transaction and returns the first
  result on a replay, the same pattern as `MoveTask`.

**H2 — The new web and new analytics do not work with the previous API or schema, so the §11 rollback breaks them**
`discipline/src/contracts/blocks.ts:34-38`; `discipline-py/app/reports.py:40`.
- `Block` now *requires* `categoryId`, `categoryKind`, `recurringRuleId`, `originalDate` and
  `recurringEdited`. The F1 daily screens parse every block response with this schema
  (`daily-api.ts` → `BlockResponse`). The F1 E2E mock had to add these fields, which shows that the old
  shape no longer parses.
- If the API is rolled back as §11 describes (goose down 00014 plus the previous API) while the web stays
  deployed, check-in, move and focus panels fail with a `ContractError`.
- `discipline-py` now outer-joins `categories`, which no longer exists after 00014's Down, so analytics
  and dashboard return 500.
- CLAUDE.md requires that every change works with the previous version of the other services.
- Fix: make the five new `Block` fields `.optional()` (or give them defaults) on the client. In py, fall
  back to the legacy string when the `categories` table or column is missing, or document that a rollback
  goes web → py → API in reverse order.

**H3 — The "keyboard only" E2E pass is not keyboard-only, and the Status claim is inaccurate**
`discipline/e2e/f13.spec.ts:184` and `fillForm` at `:150-160`; `src/pages/PlannerV2.test.tsx` ("keyboard path").
- The E2E focuses the button with `.focus()` and presses Enter. It types "Lectures" once, then
  `fillForm` overwrites the name with `fill()`.
- The date and "From" fields use `fill()`, Start/End use `selectOption()`, weekday toggles use
  `click()`, and Save is reached with `.focus()`, not Tab.
- The unit "keyboard path" uses `fireEvent.change` and `fireEvent.click`.
- As a result, nothing exercises Tab order, the focus trap, Space on the weekday toggles, arrow keys on
  the selects, or typing a date. These are S2's AC ("a form dialog does everything the gestures do
  (keyboard, screen reader)") and §5.3 ("the E2E keyboard pass does the whole flow without a pointer").
- The Status says "types every field except dates". In fact only the name is typed.
- Fix: drive the dialog with `keyboard.press('Tab')`, `type`, `Space` and `ArrowDown` for every field.
  For dates, type digits into the focused `input[type=date]` with the locale pinned in the Playwright
  config (`locale: 'en-US'`), and assert focus stays inside the dialog.

**H4 — Planner caches leak one account's data to the next account on the same device**
`discipline/src/hooks/use-planner.ts:41,44,57,72`; `src/lib/planner.ts` (`saveWeekCache`, key `planner-week:<monday>`).
- The week, category and rule caches live in `localStorage` under keys that do not include the user, and
  `revokeSession`/`logout` (`src/lib/api.ts:194-215`) never remove them.
- After user A logs out and user B logs in, `initialData` immediately renders A's block names, rule
  names and category names. Online this lasts until the refetch completes; offline it lasts
  indefinitely.
- VISION #6: personal data is private.
- Related, pre-existing but now wider: the `sync-queue` is not cleared on logout either, so B's session
  replays A's queued block and rule creates.
- Fix: key the caches by user id (or clear `planner-*` and `sync-queue` in `revokeSession`), and add a
  test.

---

## Medium

**M1 — Deleting an occurrence with plain `DELETE /tasks/:id` brings it back**
`discipline-back/internal/repositories/task_repository.go:344` (`Delete`); `recurring_repository.go:302`.
- `Delete` writes no exception. The next range read finds the `(rule, date)` slot free and materializes
  the occurrence again.
- The new form uses `/occurrence`, but the legacy planner, older cached PWA clients and any API client
  still call `DELETE /tasks/:id`.
- Fix: in `Delete`, when the row has `recurring_rule_id`, write a `cancelled` exception for
  `coalesce(original_date, date)` in the same transaction, and add a test.

**M2 — The deploy-window trigger ignores a category change made by the previous API**
`discipline-back/migrations/00014_categories_and_recurring.sql:153,179`.
- On `UPDATE OF category`, `NEW.category_id` still holds the old id, so the trigger returns early.
- When the previous API changes a block from "gym" to "study", `category_id` keeps pointing at Gym. The
  new web shows the wrong category, and analytics count the wrong kind.
- Fix: on UPDATE, re-resolve when `NEW.category IS DISTINCT FROM OLD.category AND NEW.category_id IS NOT DISTINCT FROM OLD.category_id`.
  Add a test next to `TestF13TriggerFillsCategoryForTheOldAPI`.

**M3 — New-API writes still depend on the trigger, so 00015 as planned will break them**
`discipline-back/internal/repositories/task_repository.go:258` (`cols["category_id"] = nil`); `resolveCategory` (`task_repository.go`, returns early without `categoryId`).
- A legacy-only `PUT` sets `category_id = NULL` and relies on the trigger to fill it.
- Legacy-only creates (Smart Schedule `SavePlan`, bulk, older clients) insert NULL and rely on the
  trigger too.
- 00015 drops the trigger and sets `NOT NULL`, so all of these start returning 500. The Status precondition
  ("`count(*) … IS NULL` is 0") is necessary but not sufficient.
- Fix: before 00015, resolve legacy strings in Go (the same lookup as the trigger) and test that a
  legacy-only POST/PUT works without the trigger.

**M4 — The web computes "today" and "now" in the browser's zone, not the user's IANA zone**
`discipline/src/pages/PlannerV2.tsx:31,47` (`localDateString()`, `new Date().getHours()`).
- The server materializes from the user's zone (`userToday`). The web takes today, the today column, the
  now line, auto-scroll, the default form date and "planned up to" from the device clock.
- When the device zone differs from the profile zone (travel, or a misconfigured phone), the view
  disagrees with the server. For example, the server has created nothing for the browser's "today".
- `AuthUser.timezone` is already available on the client.
- The rule (VISION time rules, CLAUDE.md product rule 1) is explicit, even though the pattern predates F13.
- Fix: derive `today`/`nowMin` with `Intl.DateTimeFormat(…, { timeZone: user.timezone })`, and add a
  unit test across midnight.

**M5 — "Delete this and following" past a rule's end date extends the rule**
`discipline-back/internal/repositories/recurring_repository.go:247-256`.
- With `fromDate > valid_to`, the code sets `valid_to = fromDate - 1`, which is later than the current
  end, so the rule is lengthened.
- `UpdateRule` rejects this case (`d > *old.ValidTo → ErrRuleDates`); `DeleteRule` does not.
- Fix: use the same guard, or set `valid_to = least(valid_to, fromDate - 1)`, and add a test.

**M6 — Recurring blocks exist only after someone opens the planner for that week** (design gap; owner decision needed, *intent uncertain*)
`discipline-back/internal/routes/routes.go` (`GET /tasks?date=` unchanged); `discipline/src/hooks/use-tasks.ts:38`.
- The Dashboard/Today screen reads `?date=today`, which never materializes.
- A user who sets up "Gym Mon/Wed/Fri" and then only uses Today sees no gym block in the following weeks,
  so no check-in is possible. M3's daily loop builds on this.
- §10.5 keeps materialization in `GET /tasks`, but §3.1 left the single-day read unchanged.
- Fix (owner's call): materialize the single day in `?date=` as well, with the same clamps.

**M7 — The E2E runs entirely against a hand-written mock, and several flows have no E2E**
`discipline/e2e/f13.spec.ts:36-125`.
- The mock re-implements materialization, so drift from the server's rules (`original_date`,
  `moved`/`conflict` handling) goes unnoticed.
- No E2E covers place-anyway or skip-this-week, resize, Escape-cancels-drag, the error state, the loading
  state, offline with a non-empty cached week (the offline test only covers the empty week), or the
  claim that a swipe actually scrolls (the test only shows that it does not move a block).
- The screenshots lack the loading, error and conflict states at 390 and 1440 px.
- Fix: add these cases. Consider one smoke run against the real API (`make test` database).

**M8 — Legacy-only creates return `categoryId`/`categoryKind` as null although the database has them**
`discipline-back/internal/repositories/task_repository.go` (`CreateTasks`: `CreateInBatches` then `attachKinds`).
- The trigger fills `category_id`, but GORM does not read it back, so the 201 body and `block_created`
  carry no kind.
- Fix: add `Clauses(clause.Returning{Columns: [{Name:"category_id"}]})`, or re-select after the insert.

**M9 — No UI lists or deletes recurring rules**
`discipline/src/pages/PlannerV2.tsx` (rules are used only for markers).
- A rule can only be edited or deleted from one of its occurrences. A rule whose dates all conflict (or
  one duplicated by H1), or one that starts beyond 8 weeks, cannot be removed.
- §5 does not ask for a rule list, so this is *possibly out of scope*, but it combines badly with H1.
- Fix: a minimal "Repeating blocks" list with delete, or confirm with the owner that it is deferred.

---

## Low

**L1** `discipline/src/components/planner/TimeGrid.tsx:231-232`: the "Place anyway" and "Skip this
week" buttons are `h-7` (28 px), below §5.1's 44 px rule. `expectTouchTargets` never sees them because the
E2E has no conflict. Fix: use `min-h-[44px]` on touch.

**L2** `discipline/src/lib/planner.ts:110`: `categoryLabel` shows the stored name whenever
`systemKey` is null, so backfilled "Fixed" stays English for uz/ru users. §6 lists `categories.fixed`.
Fix: map `legacy_name='fixed'` to its i18n key, or expose a `legacyKey`.

**L3** `discipline/src/pages/PlannerV2.tsx:176` vs `:269`: the empty-state "Add a block" is disabled
offline, but the header "Add a block" is not. Offline it queues a create, which H1 makes risky. Fix: make
both behave the same way.

**L4** `discipline/src/components/planner/CategoryManager.tsx:134`: choosing the placeholder gives
`Number('') = 0`, which enables "Move and delete". `planner-api.ts:38` then drops `reassignTo=0`, so the
user gets a silent 409 loop. Fix: keep `''` for the placeholder.

**L5** `discipline/src/components/planner/BlockFormModal.tsx:60`: a legacy block with
`categoryId = null` opens with Save disabled and no explanation (the select shows the first option, but
the state holds `''`). Fix: default to Personal, or show a hint.

**L6** `discipline-back/internal/handlers/recurring_integration_test.go:380`: the concurrency test
ignores the response codes. Four failed requests could still leave three rows. Fix: assert 200 for each.

**L7** `discipline-py/tests/test_kinds.py`: "exceptions are not a miss" is tested only as
`day_metrics(D, [])`. The heatmap, streak and focus score over a week that has an exception date are not
covered (§9 py). Fix: add a period-report test.

**L8** The Dashboard/Today screens (`categoryLabel(task.category)` in `lib/smart-schedule.ts`) show the
legacy kind string. A block in the custom category "Reading" (kind study) shows as "Study", and a renamed
default shows its old name. Fix: show the category from `categoryId` once F13 is on.

**L9** Export: the API has no user-data export endpoint at all (VISION #6, M1). The deferral is noted,
but VISION treats export as a hard rule. Fix: track it as a separate item before beta.

**L10** `discipline/src/pages/PlannerV2.tsx`: if `GET /categories` fails, every "Add" button is silently
disabled and no error is shown. Fix: show the same error and retry alert as for the week.

**L11** `discipline-back/migrations/00014_categories_and_recurring.sql:107-111`: the comment says that
`NOT VALID` keeps the `ACCESS EXCLUSIVE` lock short. Goose runs the file in one transaction, though, so the
lock on `tasks` is held through the full-table backfill `UPDATE` and the index builds. This is fine at the
current size, but the comment is misleading. Fix: correct the comment, or split the migration.

**L12** `discipline-back/internal/services/task_service.go:220`: `block_moved.same_day` compares the new
date with the occurrence's *original* date, not with the date before the move. A second move gives the
wrong value. Fix: compare with `current.Date`.

---

## Acceptance criteria not met, or met only partly (summary)

- S2 keyboard and screen-reader parity: not verified (H3).
- S2 "both views have empty, loading, error, offline states": implemented and unit-tested; screenshots
  and E2E cover only the empty and offline states (M7).
- S3 "deleting one occurrence writes an exception": true for `/occurrence` only, not for `DELETE /tasks/:id` (M1).
- §8 Export: not done (accepted deferral, L9). Account delete is covered by the cascades and the `NO ACTION` test.
- §8 Several devices / offline: replays are not idempotent for creates (H1).
- Rollout: forward order works; rollback compatibility does not (H2).
