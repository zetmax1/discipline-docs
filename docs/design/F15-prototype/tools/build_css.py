import sys
sys.path.insert(0, sys.argv[1])
from palettes import css
out = sys.argv[2]

A = """/*
 * F15 direction A, "Morning Paper": warm paper, ink and sage; soft, rounded, unhurried.
 * Font: Nunito (SIL OFL 1.1). Tokens are HSL triplets, the same format as the app's index.css;
 * in the app they sit under the F15 root attribute (docs/design/F15.md §6).
 */
@import url('fonts/nunito.css');
:root {
%(light)s
  --font: 'Nunito Variable', system-ui, sans-serif;
  --fw-body: 500; --fw-medium: 650; --fw-heading: 800; --fw-timer: 700; --lh-body: 1.55;
  --fs-xs: .8125rem; --fs-sm: .875rem; --fs-body: 1rem; --fs-btn: .9375rem; --fs-h3: 1.125rem; --fs-h2: 1.375rem; --fs-h1: 1.875rem;
  --fs-brand: 1.0625rem; --fs-timer: 4rem; --fs-timer-phone: 3.5rem;
  --tracking-heading: -.015em; --tracking-brand: -.01em; --case-brand: none; --case-label: none; --tracking-label: 0;
  --tracking-timer: -.01em;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 24px; --s6: 32px; --s8: 44px;
  --pad-card: 24px; --pad-card-x: 24px; --pad-session: 20px; --pad-btn-x: 20px;
  --radius-card: 20px; --radius-inner: 14px; --radius-btn: 999px; --radius-chip: 999px; --radius-block: 10px;
  --radius-seg: 999px; --radius-seg-item: 999px; --radius-pill: 16px; --radius-mark: 9px;
  --hairline: 1px; --card-border: 0px; --session-border: 0px; --ring-width: 3px;
  --shadow-card: 0 1px 2px hsl(30 20%% 20%% / .05), 0 10px 28px -12px hsl(30 25%% 20%% / .16);
  --shadow-btn: 0 1px 2px hsl(150 30%% 15%% / .2); --shadow-seg: 0 1px 3px hsl(30 20%% 20%% / .14);
  --tl-gap: 8px; --tl-bg: hsl(var(--background)); --tl-border: 0px; --stripe: 0px;
  --blk-bg: color-mix(in srgb, hsl(var(--c)) 16%%, hsl(var(--card))); --blk-border: 0px; --blk-border-color: transparent;
  --blk-shadow: none; --blk-pad-left: 8px;
  --ppm-desk: 1px; --ppm-phone: 1.1px;
  --grid-lines: repeating-linear-gradient(to bottom, hsl(var(--border)) 0 1px, transparent 1px calc(60 * var(--ppm)));
  --icon-stroke: 1.75; --icon-cap: round; --icon-join: round;
  --motion-fast: 220ms; --ease: cubic-bezier(.2, .8, .2, 1);
}
:root[data-theme="dark"] {
%(dark)s
  --shadow-card: 0 0 0 1px hsl(var(--border)), 0 12px 28px -14px rgb(0 0 0 / .6);
  --shadow-btn: none; --shadow-seg: 0 1px 2px rgb(0 0 0 / .5);
  --blk-bg: color-mix(in srgb, hsl(var(--c)) 20%%, hsl(var(--card)));
}
"""

B = """/*
 * F15 direction B, "Instrument": cool slate, ink and indigo; crisp hairlines, square corners,
 * numbers you can read at a glance. Font: IBM Plex Sans (SIL OFL 1.1). Tokens are HSL triplets,
 * the same format as the app's index.css; in the app they sit under the F15 root attribute.
 */
@import url('fonts/ibm-plex-sans.css');
:root {
%(light)s
  --font: 'IBM Plex Sans Variable', system-ui, sans-serif;
  --fw-body: 400; --fw-medium: 500; --fw-heading: 600; --fw-timer: 500; --lh-body: 1.5;
  --fs-xs: .75rem; --fs-sm: .8125rem; --fs-body: .9375rem; --fs-btn: .875rem; --fs-h3: 1rem; --fs-h2: 1.25rem; --fs-h1: 1.625rem;
  --fs-brand: .875rem; --fs-timer: 4.25rem; --fs-timer-phone: 3.5rem;
  --tracking-heading: -.01em; --tracking-brand: .14em; --case-brand: uppercase; --case-label: uppercase; --tracking-label: .06em;
  --tracking-time: .02em; --tracking-timer: -.02em;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 20px; --s6: 24px; --s8: 32px;
  --pad-card: 20px; --pad-card-x: 20px; --pad-session: 16px; --pad-btn-x: 14px;
  --radius-card: 8px; --radius-inner: 6px; --radius-btn: 6px; --radius-chip: 4px; --radius-block: 4px;
  --radius-seg: 8px; --radius-seg-item: 6px; --radius-pill: 8px; --radius-mark: 4px;
  --hairline: 1px; --card-border: 1px; --session-border: 1px; --ring-width: 2px;
  --shadow-card: none; --shadow-btn: none; --shadow-seg: 0 0 0 1px hsl(var(--border));
  --tl-gap: 6px; --tl-bg: hsl(var(--card)); --tl-border: 1px; --stripe: 3px;
  --blk-bg: hsl(var(--card)); --blk-border: 1px; --blk-border-color: hsl(var(--border));
  --blk-shadow: inset 3px 0 0 hsl(var(--c)); --blk-pad-left: 9px;
  --ppm-desk: 1px; --ppm-phone: 1.1px;
  --grid-lines: repeating-linear-gradient(to bottom, hsl(var(--border)) 0 1px, transparent 1px calc(30 * var(--ppm)),
    hsl(var(--border) / .5) calc(30 * var(--ppm)) calc(30 * var(--ppm) + 1px), transparent calc(30 * var(--ppm) + 1px) calc(60 * var(--ppm)));
  --icon-stroke: 1.5; --icon-cap: square; --icon-join: miter;
  --motion-fast: 140ms; --ease: cubic-bezier(.3, 0, .2, 1);
}
:root[data-theme="dark"] {
%(dark)s
}
"""
open(f'{out}/a-morning-paper.css', 'w').write(A % {'light': css('a', 'light'), 'dark': css('a', 'dark')})
open(f'{out}/b-instrument.css', 'w').write(B % {'light': css('b', 'light'), 'dark': css('b', 'dark')})
print('ok')
