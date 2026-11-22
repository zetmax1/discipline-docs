# F15 review
Date 2026-11-22, reviewer: fresh agent, scope: `git diff main...feat/F15` in discipline.

## Summary
- **Blocker 0 · High 1 · Medium 5 · Low 6.**
- The token, font and status work is solid. The flag-off look matches `main`: I ran the branch's flag-off computed-style E2E against a build of `main` and it passed at 390 and 1440. Unit tests: 350 passed, none skipped.
- The one serious problem is the new conflict-marker strip. It has a fixed width of 106 px, so in the week view at 768–1279 px it is wider than the day column. There it spills out and its "Place anyway" button sits under a block. Two markers at the same time overflow even at 1440.
- The other issues: error text is still red with F15 on, the marker outline contrast doesn't match §5, one E2E fails on Mondays, two owner-requested fixes were not changed, and parts of the Direction A spec were not built.

How I checked: I read the diff and the full files, and ran throwaway Playwright probes from the scratchpad. Nothing in the repo was changed.

## Findings

1. **H1 — The conflict-marker strip overflows its day column and its buttons sit under a block below 1280 px (and with two markers at any width)**
   High · `src/components/planner/TimeGrid.tsx:67-68, 190, 218-220, 259-260`, `src/lib/planner.ts:108-121`
   - **What's wrong:** With F15 on, a conflict marker always takes a 106 px strip (`F15_STRIP_PX`), and the blocks in its group get `calc((100% - 106px)/lanes - 4px)`. But the week view is used from 768 px up, not only at 1440 (`isMobile` is `< 768`). Measured in the probe (week view, en, the mock's Wednesday):

     | Viewport | Column width | Marker | Essay block | "Place anyway" button |
     |---|---|---|---|---|
     | 800 | 64 px | 102 px, starts 40 px inside Tuesday | 17 px | under the block |
     | 1024 | 96 px | 102 px, starts 8 px left of the column | 17 px | under the block |
     | 1280 | 132 px | fits | 21 px | reachable |
     | 1440 | 155 px | fits | 44 px | reachable |

     At 800 and 1024, `elementFromPoint` at the centre of "Place anyway" returns the "Essay draft" block, so a click opens the block instead of placing the rule.
   - **Two markers:** `layoutWithStrip` gives two concurrent markers two strips (its own unit test covers this). Two strips need 212 px, which is more than the 155 px column at 1440. The left edge works out to `calc(100% - 212px + 2px)`, i.e. about −55 px. I checked this by arithmetic, not by running it.
   - **Why it matters:** Owner answer 2 says the marker never overflows its column. The E2E (`e2e/f15.spec.ts:172`) only checks one marker, in en, at 1440. On tablets and small laptops an action is unreachable and the block is a 17 px sliver.
   - **Fix:** Use the strip only when the column is wide enough (measure it, or a container query). Otherwise fall back to the old lane layout or stack the two icon buttons vertically (44 px wide). Give blocks a minimum width. Add E2E cases at 1024 and with two concurrent markers.

2. **M1 — Errors still show in red with F15 on**
   Medium · `src/pages/Today.tsx:63`, `src/pages/Analytics.tsx:50`, `src/pages/PlannerV2.tsx:201`, `src/components/planner/BlockFormModal.tsx:205`, `src/components/planner/CategoryManager.tsx:144`, `src/pages/Login.tsx:169`, `src/components/ProfileModal.tsx:164`, `src/pages/SmartSchedule.tsx:229`
   - **What's wrong:** S4 says red is used only for destructive actions. §8 says error states use `--foreground` text with a neutral border, "not destructive red". All of these still use `text-destructive`, `bg-destructive/10` or `border-destructive/40`, which in Morning Paper is `#A63D2C`. No F15 rule overrides them.
   - **Why it matters:** This acceptance criterion is not met. Red load errors on Today and Analytics read as alarm or failure (VISION #3).
   - **Fix:** Add an F15-only hook. Either a class (`ui-error`) or `:root[data-look="f15"] [role="alert"].text-destructive` that maps to `--foreground` plus a neutral border. That keeps the flag-off look and needs no page-level colours. Or ask the owner whether form validation may stay red.

3. **M2 — Marker outline contrast is about 1.3:1, not the 3.3:1 in §5**
   Medium · `src/components/planner/TimeGrid.tsx:264`, `src/theme/contrast.test.ts:71`
   - **What's wrong:** The marker's dashed outline is `border-border`, which F15 sets to `#E2DACD`. Measured: `rgb(227,219,206)` on body `rgb(247,244,238)`, about 1.26:1. §5 promises "marker outline 3.3" (presumably `--border-strong`). The contrast test checks `border-strong` on `card`, but the marker doesn't use `border-strong`, and nothing tests the token it does use.
   - **Why it matters:** The S5 "every §5 pair" claim is not true for this element. The dashed outline that S4 relies on is barely visible (see `F15-screens/desktop-1440-planner-light.png`).
   - **Fix:** Add `:root[data-look="f15"] .ui-marker { border-color: hsl(var(--border-strong)); }`, plus a test that reads the marker's real border token.

4. **M3 — The status E2E fails on Mondays before 15:30**
   Medium · `e2e/f15.spec.ts:131-142`, `e2e/f15-app.ts:13, 76-88, 96`
   - **What's wrong:** The mock only creates blocks for the current week. A skipped block exists only on a past weekday of this week, or today after 15:30 ("Reading" ends at 930 min). On a Monday morning no skipped block exists anywhere. The test steps back through days or weeks that have no blocks, then `expect(skipped).toBeVisible()` fails. This happens in both projects.
   - **Also:** `today` is computed once at module load, so a run that crosses midnight mixes two dates.
   - **Why it matters:** `npm run check` goes red one morning a week. Commit `cd774bc` already fixed the same kind of bug on Sundays for F13.
   - **Fix:** Generate blocks for the previous week too, or pin the clock (`page.clock.setFixedTime`, plus a fixed date in the mock).

5. **M4 — Two owner-requested fixes were not changed in code**
   Medium · `e2e/f15-fixes.spec.ts:13-55`, F15.md §11 decision 5
   - **What's wrong:** Owner answer 3 asks for the sidebar footer to be fully visible at 1440×900 and 390×700, and for the Today date to line up with the card column. The build adds only E2E guards (and `data-testid`s) and says it could not reproduce either problem. The tests check only F12A on, `/planner` for the footer, and the default content.
   - **Why it matters:** The owner saw something, and the build reports these as done (§11 table: "Owner 3 … footer and date E2E guards").
   - **Fix:** Before merging, mark them in §11 as "not reproduced, waiting for the owner's screenshot", not "done". Extend the guards to F12A off and to Today with a long check-in card.

6. **M5 — Direction A is only partly built, and the gaps are not recorded**
   Medium · `src/index.css` (whole F15 section), `src/components/daily/FocusPanel.tsx:180`
   - **What's missing:**
     - the §2 type scale (body 16, buttons 15, page title 30, timer 64/56): no font-size tokens; h1 stays `text-2xl`, timer `text-6xl` = 60 px;
     - Lucide stroke 1.75 / `--icon-stroke`;
     - `--radius-btn` and `--radius-chip`;
     - the 44 px desktop gutter;
     - the 4 px "rise" motion;
     - §6's "`BlockCheckIn` chips and `SyncStatus` use the status tokens".
   - §11 lists none of these under decisions or deferred.
   - **Why it matters:** S1 says "the new tokens apply". The owner chose A from prototypes that use these values.
   - **Fix:** Build them as F15-only hook rules, or list each one in §11 as deferred so the owner can accept it.

7. **L1 — With the flag off, the app is not exactly as before**
   Low · `src/components/planner/TimeGrid.tsx:306` (TitleTooltip), `src/pages/NotFound.tsx:18`, `src/components/AppSidebar.tsx:34,63`, `index.html:23-39`
   - **What changed:**
     - The block-title tooltip shows with F15 off. Verified: hovering a truncated block with F15 off opens one tooltip.
     - The 404 home link is now a 44 px `inline-flex` for everyone.
     - The sidebar label changes with F1 regardless of F15.
     - Google Fonts moved from a CSS `@import` (render-blocking) to a script-inserted `<link>`, which is not render-blocking. That may add a brief fallback-font flash on first paint with the flag off (unverified).
   - Decision 5 covers the owner fixes. The 404 change and the font-loading timing are not mentioned.
   - **Why it matters:** §10's rollout promise ("Off again restores today's look at once") and CLAUDE.md's "everything behind `FEATURE_<id>`" are not literally true.
   - **Fix:** Get the owner to confirm that unflagged fixes are fine. Otherwise gate the tooltip and the 404 change on `useFeature('F15')`.

8. **L2 — Several tests would pass even if the feature were broken**
   Low
   - `e2e/f15-pages.spec.ts:74`: `ring.shadow !== 'none' || ring.outline !== 'none'` is always true for Tailwind `outline-none` controls. Probe: a bare `button.outline-none` gives `outlineStyle: "solid"` with no ring. The title says "3:1" but the test checks no contrast.
   - `e2e/f15.spec.ts:74`: `document.fonts.check` returns true when no face matches the text's unicode-range, so the coverage check can pass vacuously. Only `loaded >= 3` has teeth.
   - `e2e/f15.spec.ts:34-45`: "set before the first paint" only checks that the HTML contains `look-boot`. After reload, `LookSync` would set the attribute anyway.
   - `src/theme/contrast.test.ts:74`: `status-skipped` on `card` is asserted at 3:1, but in the grid it is text. The real values (about 5.3 light, 6.0 dark) pass 4.5, so only the guard is weak.
   - `e2e/f15-fixes.spec.ts:85`: a fixed `waitForTimeout(400)` to prove that no tooltip appears.
   - **Fix:** Compare the focus ring colour against the background. Check the attribute from `addInitScript` / `DOMContentLoaded` before React mounts. Assert 4.5 for skipped text.

9. **L3 — The phone bottom nav still says "Home" with F1**
   Low · `src/components/nav-items.ts:6`, `src/components/BottomNav.tsx:23`
   - **What's wrong:** With F1 the sidebar says "Today", but at 390 px (no sidebar) the bottom nav still shows `nav.short.dashboard` ("Home" / "Bosh" / "Главная"). The Today screenshot at 390 shows "Home" under a "Today" page title.
   - **Why it matters:** The owner's request named the sidebar only, but on a phone the result is inconsistent.
   - **Fix:** Ask the owner. If yes, add `nav.short.today` in en/uz/ru.

10. **L4 — No screen states or dialogs in the proof**
    Low · `e2e/f15-pages.spec.ts`
    - **What's missing:** The screenshots and overflow/touch checks cover each page's default state only. There are none for the empty, loading, error and offline states (§8), the block form, dialogs, toasts, the planner Day view at 1440 or the week view at 390.
    - **Why it matters:** These states are where M1 shows up, and the rules require every screen to have them.
    - **Fix:** Add a few state shots, e.g. Today with `/checkins/today` returning 503, offline, and an empty planner.

11. **L5 — The OFL licence text does not ship with the font files**
    Low (unverified) · `THIRD_PARTY_NOTICES.md:9`
    - **What's wrong:** The licence text is recorded as "in `node_modules/.../LICENSE`", which is not part of the build. OFL §2 requires the copyright notice and licence with each copy. That can be met by the font's metadata, but I could not check the woff2 name table (no fontTools here).
    - **Fix:** Confirm the name table carries the notice and licence, or copy `OFL.txt` into `public/` and point to it from the notices file.

12. **L6 — The font is not precached for offline use**
    Low · `public/sw.js:10`
    - **What's wrong:** Decision 6 makes the font cached on first use instead of precached, and `MAX_ASSETS = 80` can trim it later. Offline before first use (or after trimming), the app falls back to Arial or Helvetica. This differs from §6/§9 "precached".
    - **Fix:** Accept it in writing, or precache the four Nunito subsets.

Noticed, out of scope: `Today.tsx` formats "today" with the browser's `new Date()`, not the user's IANA timezone. This was already there; the diff only adds a test id.

## Checked and fine
- **S1:** the boot script in `<head>` sets `data-look` from cached flags before React (unit-tested in jsdom). `LookSync` follows the flag at runtime. `:root`/`.dark` are untouched (snapshot). The flag-off computed-style fixture **matches a build of `main`** (I ran it at 390 and 1440, light and dark).
- **S2:** Nunito 5.3.0 is self-hosted, exact-pinned and OFL. Unicode ranges cover U+02BB/02BC (latin), Ўў (cyrillic) and Ққ Ғғ Ҳҳ (cyrillic-ext). With cached flags there is no request to `fonts.googleapis.com` or `fonts.gstatic.com`; the first visit on a new device still makes one, as §9 accepts. `THIRD_PARTY_NOTICES.md` and §7 record the font.
- **Owner 1:** Direction A palette values match §2. JetBrains Mono is gone with F15 on (`--font-code: var(--font)`; `.font-mono` uses Nunito with `tabular-nums`). Body text is also `tabular-nums`.
- **Owner 2:** "Didn't fit" / "Sigʻmadi" / "Не поместилось" is a new key in all three languages. The buttons are icon-only, 44×44, with `aria-label`s and tooltips on hover and focus, and an sr-only full sentence. At 1440 the label fits in en, uz and ru (92 px in a 92 px box). The problems at narrower widths are H1.
- **Owner 3:** the sidebar says "Today" / "Bugun" / "Сегодня" with F1 (unit-tested both ways). Truncated week titles show in a tooltip on hover and focus, and only when actually cut off.
- **S3:** `bg-green-600`, the toast reds and the `bg-black/80` overlays became tokens whose defaults equal the old Tailwind RGB values exactly. A palette-class guard test with reviewed exceptions covers the rest.
- **S4:** done = filled check, partial = half ring, skipped = dashed neutral ring with muted text (no red, no strike-through), in progress = primary outline, rest = rest tint (grid and Smart Schedule). Done and partial are no longer faded. The Skip check-in button is ghost/neutral.
- **S5:** the §5 token pairs are unit-tested in both themes (apart from the marker, M2). Overflow at 390 is checked in en/uz/ru on every page, and touch targets on every page in light and dark. Reduced motion stops the transitions and the breathing dot (F15 only).
- **S6:** every page at 390 and 1440, light and dark, plus uz/ru shots of Today and Planner at 390.
- **i18n:** no hard-coded UI strings in the diff; the en/uz/ru keys match.
- **Dark mode:** `.dark[data-look="f15"]` wins over `:root[data-look]`, and the boot script never touches `.dark`.
- **Privacy:** no logging and no personal data; the fixtures are fictional.
- **Tests:** 350 vitest passed, 0 skipped. Nothing was weakened or deleted; the F13 spec change is test-only.
