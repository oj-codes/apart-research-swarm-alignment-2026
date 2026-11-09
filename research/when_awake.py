"""Commits on main by hour of day per participant, plus merges, drawn as an SVG. No dependencies.

    python3 research/when_awake.py research/when-the-team-was-awake.svg [ref]

Hours are US Eastern (UTC-5). Author names go through the ref's .mailmap. Merges are counted
separately: every merge on main was applied by the human, so that row is when the gate was open.
Render the SVG to PNG however you like; headless Chrome's --screenshot was used for the committed one.
"""
import collections, datetime, json, subprocess, sys

REF = sys.argv[2] if len(sys.argv) > 2 else 'origin/main'
TZ = datetime.timezone(datetime.timedelta(hours=-5))
COLORS = {'Auran': '#8E6FE0', 'Corrie': '#7DD3FC', 'Codex': '#FB7185', 'Tern': '#FBBF24', 'Venice': '#17705F',
          'Rill': '#C084FC', 'O. J. Wilcox': '#F45D48', 'merges': '#9A9A94'}


def log(*extra):
    cmd = ['git', '-c', f'mailmap.blob={REF}:.mailmap', 'log', REF, *extra, '--format=%aN|%aI']
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines()


by = collections.defaultdict(collections.Counter)
for line in log('--no-merges'):
    name, iso = line.split('|')
    by[name][datetime.datetime.fromisoformat(iso).astimezone(TZ).hour] += 1
for line in log('--merges'):
    _, iso = line.split('|')
    by['merges'][datetime.datetime.fromisoformat(iso).astimezone(TZ).hour] += 1

agents = sorted([n for n in by if n != 'merges'], key=lambda n: -sum(by[n].values()))
order = agents + ['merges']
W, L, R, rowh, top = 1320, 250, 40, 112, 112
barw = (W - L - R) / 24
H = top + rowh * len(order) + 60
ymax = max(max(c.values()) for n, c in by.items() if n != 'merges')
mmax = max(by['merges'].values())
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Georgia, \'Old Standard TT\', serif">',
     f'<rect width="{W}" height="{H}" fill="#FAFAF7"/>',
     f'<text x="{L}" y="44" font-size="26" fill="#2A2A28">When the team was awake</text>',
     f'<text x="{L}" y="70" font-size="13.5" fill="#55554F">Non-merge commits on main by hour of day, US Eastern, 7 and 8 November 2026. Shaded: 22:00 to 07:00. Rows ordered by count.</text>',
     f'<text x="{L}" y="90" font-size="13.5" fill="#55554F">O.J. applied every commit and merged every pull request; her authored commits are her row, and every merge on main is the last row.</text>']
for a, b in ((0, 7), (22, 24)):
    o.append(f'<rect x="{L + a * barw:.1f}" y="{top}" width="{(b - a) * barw:.1f}" height="{rowh * len(order)}" fill="#000" opacity="0.035"/>')
for i, n in enumerate(order):
    base = top + i * rowh + rowh - 22
    scale = (rowh - 40) / (mmax if n == 'merges' else ymax)
    counts = [by[n].get(h, 0) for h in range(24)]
    label = 'O.J.' if n.startswith('O. J') else ('merges, by O.J.' if n == 'merges' else n)
    o.append(f'<line x1="{L}" y1="{base}" x2="{W - R}" y2="{base}" stroke="#D4D4D0" stroke-width="1"/>')
    o.append(f'<text x="{L - 18}" y="{base - 6}" text-anchor="end" font-size="17" fill="#2A2A28">{label}</text>')
    o.append(f'<text x="{L - 18}" y="{base + 16}" text-anchor="end" font-size="12.5" fill="#55554F">{sum(counts)}{" merges" if n == "merges" else " commits"}</text>')
    for h, c in enumerate(counts):
        if not c:
            continue
        hgt = c * scale
        x = L + h * barw + 3
        o.append(f'<rect x="{x:.1f}" y="{base - hgt:.1f}" width="{barw - 6:.1f}" height="{hgt:.1f}" rx="3" fill="{COLORS.get(n, "#6B7280")}"/>')
        if c == max(counts):
            o.append(f'<text x="{x + (barw - 6) / 2:.1f}" y="{base - hgt - 5:.1f}" text-anchor="middle" font-size="11.5" fill="#55554F">{c}</text>')
    if i == len(order) - 1:
        for h in range(0, 24, 3):
            o.append(f'<text x="{L + h * barw + barw / 2:.1f}" y="{base + 36}" text-anchor="middle" font-size="12" fill="#55554F">{h:02d}:00</text>')
o.append('</svg>')
open(sys.argv[1], 'w').write('\n'.join(o))
print(json.dumps({n: sum(c.values()) for n, c in by.items()}))
