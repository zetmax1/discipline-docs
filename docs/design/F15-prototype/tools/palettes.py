"""F15 palettes: one source for the prototype tokens, the doc tables and the contrast report."""
import colorsys, sys, json

P = {
 'a': {  # Morning Paper
  'light': dict(sidebar='#F1ECE3', nav_active='#E0EAE2', nav_active_foreground='#2D5040', session_bg='#F7F3EC', today_col='#FBF8F2', border_strong='#958A78', background='#F7F4EE', foreground='#23211D', card='#FFFDF9', muted='#EFEAE1', muted_foreground='#5F594F',
    border='#E2DACD', primary='#3B6652', primary_foreground='#FFFFFF', secondary='#ECE6DB', secondary_foreground='#23211D',
    accent='#F1DFB4', accent_foreground='#3D3015', ring='#3B6652', destructive='#A63D2C', destructive_foreground='#FFFFFF',
    cat_focus='#3D6CA3', cat_study='#7655A3', cat_admin='#6A6D73', cat_exercise='#3A8460', cat_rest='#B07A2E', cat_personal='#AE5574',
    status_done='#3B6652', status_done_tint='#E4EEE7', status_partial='#7C5F22', status_partial_tint='#F4EAD3',
    status_skipped='#6F695F', status_skipped_tint='#F1ECE4', rest_tint='#F6EBD8'),
  'dark': dict(sidebar='#1E1C19', nav_active='#2A3A31', nav_active_foreground='#B7DDC8', session_bg='#1D1B18', today_col='#24221D', border_strong='#7D7567', background='#191815', foreground='#EDE8DF', card='#22201C', muted='#2C2A25', muted_foreground='#AEA799',
    border='#3A362F', primary='#93C3A9', primary_foreground='#10241A', secondary='#2F2C26', secondary_foreground='#EDE8DF',
    accent='#4A3E22', accent_foreground='#F3E2B6', ring='#93C3A9', destructive='#E59482', destructive_foreground='#2A120D',
    cat_focus='#86AEDF', cat_study='#B8A0DB', cat_admin='#A7AAB1', cat_exercise='#80C49F', cat_rest='#E2B670', cat_personal='#E59BB5',
    status_done='#93C3A9', status_done_tint='#23302A', status_partial='#E2C17A', status_partial_tint='#332B1C',
    status_skipped='#A39C90', status_skipped_tint='#2A2823', rest_tint='#322A1C'),
 },
 'b': {  # Instrument
  'light': dict(sidebar='#FFFFFF', nav_active='#E5E8FA', nav_active_foreground='#2333A6', session_bg='#F6F8FB', today_col='#F5F7FF', border_strong='#8593A3', background='#F3F5F8', foreground='#0E1621', card='#FFFFFF', muted='#E9EDF2', muted_foreground='#4F5B69',
    border='#D5DCE4', primary='#3044C9', primary_foreground='#FFFFFF', secondary='#E6EAF0', secondary_foreground='#0E1621',
    accent='#D7F1EE', accent_foreground='#0A4D48', ring='#3044C9', destructive='#BE3329', destructive_foreground='#FFFFFF',
    cat_focus='#3044C9', cat_study='#7E3CC4', cat_admin='#596676', cat_exercise='#0B7553', cat_rest='#0B7F78', cat_personal='#B63F75',
    status_done='#0B7553', status_done_tint='#E4F4EE', status_partial='#8F5A00', status_partial_tint='#FBF0DC',
    status_skipped='#5F6B7A', status_skipped_tint='#EEF1F5', rest_tint='#E0F3F1'),
  'dark': dict(sidebar='#0E141C', nav_active='#1B2448', nav_active_foreground='#BBC3FF', session_bg='#0F1620', today_col='#131C29', border_strong='#5E718A', background='#0B1017', foreground='#E5ECF4', card='#121A24', muted='#1A2431', muted_foreground='#97A5B6',
    border='#263345', primary='#93A0FF', primary_foreground='#0B1017', secondary='#1C2735', secondary_foreground='#E5ECF4',
    accent='#123B3A', accent_foreground='#9DE8E0', ring='#93A0FF', destructive='#FF8E84', destructive_foreground='#2A0D0A',
    cat_focus='#93A0FF', cat_study='#C4A0FF', cat_admin='#A6B2C1', cat_exercise='#52CC97', cat_rest='#45C9BE', cat_personal='#F293BD',
    status_done='#52CC97', status_done_tint='#12291F', status_partial='#F0BE63', status_partial_tint='#2C2414',
    status_skipped='#9AA6B5', status_skipped_tint='#18212C', rest_tint='#0F2A2B'),
 },
}

def lum(h):
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def hsl(h):
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (1, 3, 5))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return f'{round(hh*360)} {round(s*100)}% {round(l*100)}%'

# (fg, bg, minimum, what): text 4.5, large text / UI parts 3.0
PAIRS = [
 ('foreground', 'background', 4.5, 'body text'), ('foreground', 'card', 4.5, 'text on cards'),
 ('muted_foreground', 'background', 4.5, 'secondary text'), ('muted_foreground', 'card', 4.5, 'secondary text on cards'),
 ('muted_foreground', 'muted', 4.5, 'secondary text on muted'), ('primary_foreground', 'primary', 4.5, 'primary button'),
 ('primary', 'background', 4.5, 'links / selected'), ('primary', 'card', 4.5, 'links on cards'),
 ('secondary_foreground', 'secondary', 4.5, 'secondary button'), ('accent_foreground', 'accent', 4.5, 'accent chip'),
 ('destructive_foreground', 'destructive', 4.5, 'destructive button'), ('destructive', 'card', 4.5, 'destructive text'),
 ('status_done', 'status_done_tint', 4.5, 'Done label'), ('status_partial', 'status_partial_tint', 4.5, 'Partly label'),
 ('status_skipped', 'status_skipped_tint', 4.5, 'Skipped label'), ('foreground', 'rest_tint', 4.5, 'text on a rest block'),
 ('border', 'card', 1.0, 'hairline (decorative)'), ('nav_active_foreground', 'nav_active', 4.5, 'active nav item'), ('muted_foreground', 'sidebar', 4.5, 'nav items'), ('foreground', 'session_bg', 4.5, 'timer'), ('border_strong', 'card', 3.0, 'marker outline'), ('ring', 'background', 3.0, 'focus ring'),
] + [(f'cat_{k}', 'card', 3.0, f'{k} stripe / icon') for k in ['focus', 'study', 'admin', 'exercise', 'rest', 'personal']] \
  + [('status_done', 'card', 3.0, 'done icon'), ('status_partial', 'card', 3.0, 'partly icon'), ('status_skipped', 'card', 3.0, 'skipped outline')]

def report():
    bad = 0
    for d in P:
        for theme in P[d]:
            c = P[d][theme]
            for fg, bg, need, what in PAIRS:
                r = ratio(c[fg], c[bg])
                if r < need:
                    bad += 1
                    print(f'FAIL {d} {theme}: {fg} on {bg} {r:.2f} < {need} ({what})')
    print('failures:', bad)

def css(d, theme):
    c = P[d][theme]
    return '\n'.join(f'  --{k.replace("_", "-")}: {hsl(v)};' for k, v in c.items())

if __name__ == '__main__':
    if sys.argv[1:] == ['report']:
        report()
    elif sys.argv[1] == 'css':
        print(css(sys.argv[2], sys.argv[3]))
    elif sys.argv[1] == 'table':
        d = sys.argv[2]
        rows = ['| Token | Light | Dark |', '|---|---|---|']
        for k in P[d]['light']:
            rows.append(f'| `--{k.replace("_", "-")}` | `{P[d]["light"][k]}` | `{P[d]["dark"][k]}` |')
        print('\n'.join(rows))
    elif sys.argv[1] == 'contrast':
        d = sys.argv[2]
        rows = ['| Pair | Need | Light | Dark |', '|---|---|---|---|']
        for fg, bg, need, what in PAIRS:
            if need <= 1: continue
            rows.append(f'| {what} | {need} | {ratio(P[d]["light"][fg], P[d]["light"][bg]):.1f} | {ratio(P[d]["dark"][fg], P[d]["dark"][bg]):.1f} |')
        print('\n'.join(rows))
