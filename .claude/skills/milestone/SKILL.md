---
name: milestone
description: Design, build, review or fix a product milestone (M1–M9). Only run when the user types /milestone.
disable-model-invocation: true
---

Arguments: $ARGUMENTS
First word = mode (`design`, `build`, `review`, `fix`). Second = milestone id (e.g. `M2`). Anything after = notes from the owner.

## Inputs — read only these, plus the code you need
- `docs/product/VISION.md`
- `docs/product/milestones/<id>.md`
- `docs/design/<id>.md` (build, review, fix)
Use the Explore subagent for broad code searches. Don't read `docs/archive/`.

## Mode: design (no application code)
Write `docs/design/<id>.md`, at most ~400 lines:
1. **Stories:** every Must item → user stories with short acceptance criteria. Items you'd move to another milestone → say why.
2. **Data:** migrations (up and down), new/changed tables and columns, indexes, backfills, effect on existing rows.
3. **API:** endpoints, request/response schemas as they will appear in `discipline/contracts/`, error codes, auth, rate limits.
4. **Jobs and notifications**, if any.
5. **Screens:** layout at 390 px and desktop, empty/loading/error/offline states, i18n key namespaces.
6. **Edge cases:** timezone and DST, midnight, several devices, offline, brand-new user, deleted account.
7. **Security and privacy:** authorization for every new endpoint; what personal data is added to export/delete; nothing personal in logs.
8. **Test plan:** unit, integration, contract, one Playwright E2E per main flow.
9. **Rollout:** flag `FEATURE_<id>`, migration order, deploy order, manual steps for the owner.
10. **Open questions:** numbered, only decisions the owner must make.
Then STOP. Reply in ≤ 15 lines: the file path, the 3 biggest risks, the open questions.

## Mode: build
Preconditions: `docs/design/<id>.md` exists and every open question has an answer written in it. Otherwise stop and list what's missing.
1. In each repo the design touches: branch `feat/<id>` from `main`. Everything behind `FEATURE_<id>` (server and client).
2. For each story: failing test → code → green → commit `feat(<id>): <story>` in the repo it belongs to.
3. At the end run the check command of every touched repo, the contract tests and the Playwright E2E. Save screenshots of every new screen at 390 px and 1440 px in `docs/design/<id>-screens/`.
4. Add a **Status** section to the design doc: done, deferred (with reason).
5. Reply in ≤ 30 lines: story → repo + commits, test counts, deferred items, owner steps (env vars, migrations, Railway settings, flags, deploy order).

## Mode: review (no code changes)
Start a fresh subagent that has not seen the build. Give it the design doc, VISION.md and `git diff main...feat/<id>` from every touched repo. It checks: acceptance criteria, authorization on every endpoint, timezone/DST, hardcoded strings, missing screen states, personal data in logs/export/delete, test gaps, principle violations. Findings go to `docs/design/<id>-review.md` with file:line and severity. Reply in ≤ 15 lines.

## Mode: fix
The notes after the id (or `docs/design/<id>-review.md` if the notes say "review") list what to fix. For each: failing test → fix → commit `fix(<id>): …`. Re-run the affected checks. Reply in ≤ 15 lines.

## Always
- Tests run quietly; show only failures and final counts.
- Don't paste file contents into the reply; give paths.
- A decision that isn't in the design doc → stop and ask.
