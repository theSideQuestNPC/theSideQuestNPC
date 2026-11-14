"""Generates pixel-art stats.svg, langs.svg and heatmap.svg from your real GitHub data.
Runs in GitHub Actions (see .github/workflows/stats.yml). Without a token it writes sample data."""
import os, json, random, datetime, urllib.request

USER = os.environ.get('USERNAME') or os.environ.get('GITHUB_REPOSITORY_OWNER') or 'theSideQuestNPC'
TOKEN = os.environ.get('GITHUB_TOKEN', '')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'generated')
os.makedirs(OUT, exist_ok=True)

ACC, ACC2, DARK, PALE = '#ffffff', '#9a9a9a', '#333333', '#e5e5e5'
LEVELS = ['#1c1c1c', '#3d3d3d', '#6e6e6e', '#a8a8a8', '#ffffff']
MONO = "font-family=\"'Pixelify Sans','Segoe UI',system-ui,-apple-system,Arial,sans-serif\""
NS = 'xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges"'

G = {
'A':["01110","10001","10001","11111","10001","10001","10001"],'B':["11110","10001","10001","11110","10001","10001","11110"],
'C':["01110","10001","10000","10000","10000","10001","01110"],'D':["11110","10001","10001","10001","10001","10001","11110"],
'E':["11111","10000","10000","11110","10000","10000","11111"],'F':["11111","10000","10000","11110","10000","10000","10000"],
'G':["01110","10001","10000","10111","10001","10001","01111"],'H':["10001","10001","10001","11111","10001","10001","10001"],
'I':["11111","00100","00100","00100","00100","00100","11111"],'L':["10000","10000","10000","10000","10000","10000","11111"],
'N':["10001","11001","10101","10101","10011","10001","10001"],'O':["01110","10001","10001","10001","10001","10001","01110"],
'P':["11110","10001","10001","11110","10000","10000","10000"],'R':["11110","10001","10001","11110","10100","10010","10001"],
'S':["01111","10000","10000","01110","00001","00001","11110"],'T':["11111","00100","00100","00100","00100","00100","00100"],
'U':["10001","10001","10001","10001","10001","10001","01110"],'Y':["10001","10001","01010","00100","00100","00100","00100"],
'0':["01110","10001","10011","10101","11001","10001","01110"],'1':["00100","01100","00100","00100","00100","00100","01110"],
'2':["01110","10001","00001","00010","00100","01000","11111"],'3':["11110","00001","00001","01110","00001","00001","11110"],
'4':["00010","00110","01010","10010","11111","00010","00010"],'5':["11111","10000","11110","00001","00001","10001","01110"],
'6':["00110","01000","10000","11110","10001","10001","01110"],'7':["11111","00001","00010","00100","01000","01000","01000"],
'8':["01110","10001","10001","01110","10001","10001","01110"],'9':["01110","10001","10001","01111","00001","00010","01100"],
',':["00000","00000","00000","00000","00000","00100","01000"],'.':["00000","00000","00000","00000","00000","00110","00110"],
}
def btext(s, ps, x, y, fill, gap=1, attrs=''):
    d = ''; cx = 0
    for ch in s:
        if ch == ' ': cx += 3 + gap; continue
        for r, row in enumerate(G.get(ch, G['O'])):
            for c, v in enumerate(row):
                if v == '1': d += f'M{x+(cx+c)*ps} {y+r*ps}h{ps}v{ps}h-{ps}z'
        cx += 5 + gap
    return f'<path d="{d}" fill="{fill}" {attrs}/>', (cx - gap) * ps
def pbox(x, y, w, h, fill, stroke, sw=2, n=4, extra=''):
    d = f'M{x+n} {y}H{x+w-n}V{y+n}H{x+w}V{y+h-n}H{x+w-n}V{y+h}H{x+n}V{y+h-n}H{x}V{y+n}H{x+n}Z'
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
SCAN = '<pattern id="sl" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#fff" fill-opacity=".03"/></pattern>'
def stars(n, W, H, seed):
    r = random.Random(seed); o = ''
    for _ in range(n):
        x = int(r.uniform(0, W) / 2) * 2; y = int(r.uniform(0, H) / 2) * 2; s = r.choice([2, 2, 3])
        o += (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="#fff"><animate attributeName="opacity" '
              f'values=".15;1;.15" dur="{r.uniform(2,6):.1f}s" begin="-{r.uniform(0,6):.1f}s" repeatCount="indefinite"/></rect>')
    return o
def n(v): return f'{v:,}'

# ---------------- data ----------------
def sample():
    r = random.Random(4); today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday() + 1 + 52 * 7)  # a Sunday
    weeks = []; d = start
    for _ in range(53):
        days = []
        for wd in range(7):
            if d > today: break
            c = 0 if r.random() < .38 else int(r.expovariate(1 / 4))
            days.append({'date': d.isoformat(), 'contributionCount': c, 'weekday': wd}); d += datetime.timedelta(days=1)
        weeks.append({'contributionDays': days})
    tot = sum(x['contributionCount'] for w in weeks for x in w['contributionDays'])
    langs = [('TypeScript', 52000), ('JavaScript', 21000), ('CSS', 14000), ('HTML', 8000), ('Python', 3500), ('Shell', 1200)]
    return {'stars': 12, 'commits': tot, 'prs': 18, 'issues': 7, 'repos': 24, 'followers': 31, 'weeks': weeks, 'total': tot, 'langs': langs}

def real():
    q = '''query($login:String!){user(login:$login){followers{totalCount} pullRequests{totalCount} issues{totalCount}
    repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){totalCount nodes{stargazerCount languages(first:8,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
    contributionsCollection{totalCommitContributions contributionCalendar{totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}'''
    req = urllib.request.Request('https://api.github.com/graphql', data=json.dumps({'query': q, 'variables': {'login': USER}}).encode(),
        headers={'Authorization': 'bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'profile-stats'})
    u = json.load(urllib.request.urlopen(req, timeout=30))['data']['user']
    cc = u['contributionsCollection']; cal = cc['contributionCalendar']; langs = {}
    for repo in u['repositories']['nodes']:
        for e in repo['languages']['edges']: langs[e['node']['name']] = langs.get(e['node']['name'], 0) + e['size']
    return {'stars': sum(r['stargazerCount'] for r in u['repositories']['nodes']), 'commits': cc['totalCommitContributions'],
            'prs': u['pullRequests']['totalCount'], 'issues': u['issues']['totalCount'], 'repos': u['repositories']['totalCount'],
            'followers': u['followers']['totalCount'], 'weeks': cal['weeks'], 'total': cal['totalContributions'],
            'langs': sorted(langs.items(), key=lambda kv: -kv[1])}
try:
    data = real() if TOKEN else sample()
except Exception as e:
    print('GitHub fetch failed, using sample data:', e); data = sample()

# ---------------- heatmap ----------------
def heatmap(d):
    cell, pitch, x0, y0 = 14, 18, 24, 44
    W, H = 1000, 230
    counts = [x['contributionCount'] for w in d['weeks'] for x in w['contributionDays']]
    mx = max(counts) or 1
    def lvl(c):
        if c == 0: return 0
        r = c / mx
        return 1 if r <= .25 else 2 if r <= .5 else 3 if r <= .75 else 4
    paths = {i: '' for i in range(5)}; labels = ''; last = None; lastxy = None; prev_m = None
    for wi, w in enumerate(d['weeks']):
        if not w['contributionDays']: continue
        m = datetime.date.fromisoformat(w['contributionDays'][0]['date']).strftime('%b').upper()
        if m != prev_m:
            labels += f'<text x="{x0+wi*pitch}" y="34" {MONO} font-size="12" font-weight="700" fill="#a3a3a3">{m}</text>'; prev_m = m
        for dd in w['contributionDays']:
            x = x0 + wi * pitch; y = y0 + dd['weekday'] * pitch
            paths[lvl(dd['contributionCount'])] += f'M{x} {y}h{cell}v{cell}h-{cell}z'; lastxy = (x, y)
    o = f'<svg {NS} viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Contribution heatmap"><defs>{SCAN}'
    o += f'<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    o += f'<clipPath id="gc"><rect x="{x0}" y="{y0}" width="{53*pitch}" height="{7*pitch}"/></clipPath></defs>'
    o += pbox(1, 1, W - 2, H - 2, '#0b0b0b', '#ffffff', 2, 6, 'stroke-opacity=".09"') + f'<rect x="2" y="2" width="{W-4}" height="{H-4}" fill="url(#sl)"/>'
    o += stars(30, W, 28, 5) + labels
    for i in range(5): o += f'<path d="{paths[i]}" fill="{LEVELS[i]}"/>'
    o += f'<g clip-path="url(#gc)"><rect x="0" y="{y0}" width="90" height="{7*pitch}" fill="url(#beam)"><animateTransform attributeName="transform" type="translate" from="-90 0" to="{W} 0" dur="5s" repeatCount="indefinite"/></rect></g>'
    if lastxy: o += f'<rect x="{lastxy[0]-2}" y="{lastxy[1]-2}" width="{cell+4}" height="{cell+4}" fill="none" stroke="{PALE}" stroke-width="2"><animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/></rect>'
    o += f'<text x="{x0}" y="{H-18}" {MONO} font-size="16" font-weight="700" fill="#e5e5e5"><tspan fill="{ACC}" font-weight="700">{n(d["total"])}</tspan> contributions in the last year</text>'
    lx = W - 24 - 5 * 18 - 90
    o += f'<text x="{lx}" y="{H-18}" {MONO} font-size="12" font-weight="700" fill="#a3a3a3">LESS</text>'
    for i in range(5): o += f'<rect x="{lx+40+i*18}" y="{H-28}" width="{cell}" height="{cell}" fill="{LEVELS[i]}"/>'
    o += f'<text x="{lx+40+5*18+6}" y="{H-18}" {MONO} font-size="12" font-weight="700" fill="#a3a3a3">MORE</text></svg>'
    return o

# ---------------- stats card ----------------
def statscard(d):
    W, H = 490, 240
    o = f'<svg {NS} viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Player stats"><defs>{SCAN}</defs>'
    o += pbox(1, 1, W - 2, H - 2, '#0b0b0b', '#ffffff', 2, 6, 'stroke-opacity=".09"') + f'<rect x="2" y="2" width="{W-4}" height="{H-4}" fill="url(#sl)"/>' + stars(14, W, H, 8)
    t1, _ = btext('PLAYER STATS', 3, 22, 22, DARK); t2, _ = btext('PLAYER STATS', 3, 20, 20, ACC); o += t1 + t2
    cells = [('STARS EARNED', d['stars']), ('COMMITS / YEAR', d['commits']), ('PULL REQUESTS', d['prs']), ('ISSUES', d['issues']), ('REPOSITORIES', d['repos']), ('FOLLOWERS', d['followers'])]
    for i, (lab, v) in enumerate(cells):
        x = 24 + (i % 2) * 236; y = 62 + (i // 2) * 56
        txt = n(v); ps = 4 if len(txt) <= 6 else 3
        o += f'<text x="{x}" y="{y}" {MONO} font-size="13" font-weight="700" letter-spacing="1" fill="#d4d4d4">{lab}</text>'
        a, _ = btext(txt, ps, x + 2, y + 12, DARK); b, _ = btext(txt, ps, x, y + 10, PALE); o += a + b
    return o + '</svg>'

# ---------------- langs card ----------------
def langscard(d):
    W, H = 490, 240
    langs = d['langs'][:6]; tot = sum(v for _, v in d['langs']) or 1
    shades = ['#ffffff', '#dcdcdc', '#b4b4b4', '#8c8c8c', '#666666', '#4a4a4a']
    o = f'<svg {NS} viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Top languages"><defs>{SCAN}</defs>'
    o += pbox(1, 1, W - 2, H - 2, '#0b0b0b', '#ffffff', 2, 6, 'stroke-opacity=".09"') + f'<rect x="2" y="2" width="{W-4}" height="{H-4}" fill="url(#sl)"/>' + stars(14, W, H, 9)
    t1, _ = btext('TOP LANGS', 3, 22, 22, DARK); t2, _ = btext('TOP LANGS', 3, 20, 20, ACC); o += t1 + t2
    for i, (name, v) in enumerate(langs):
        y = 56 + i * 29; pct = v / tot * 100; fill = max(1, round(pct / 100 * 16)) if v else 0
        o += f'<text x="22" y="{y+12}" {MONO} font-size="15" font-weight="700" fill="#ffffff">{name[:11]}</text>'
        for s in range(16):
            on = s < fill; op = ''
            if s == fill - 1: op = '<animate attributeName="opacity" values="1;.4;1" dur="1.4s" repeatCount="indefinite"/>'
            o += f'<rect x="{130+s*13}" y="{y}" width="11" height="14" fill="{shades[i] if on else "#1c1c1c"}">{op}</rect>'
        o += f'<text x="{130+16*13+8}" y="{y+12}" {MONO} font-size="15" font-weight="700" fill="#d4d4d4">{pct:.1f}%</text>'
    return o + '</svg>'

try:
    B64 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'font.b64')).read().strip()
except OSError:
    B64 = ''
CSS = ("<style>@font-face{font-family:'Pixelify Sans';font-weight:700;font-style:normal;src:url(data:font/woff2;base64," + B64 + ") format('woff2');}</style>") if B64 else ''
def with_font(svg):
    i = svg.index('>', svg.index('<svg')) + 1
    return svg[:i] + CSS + svg[i:]

for name, fn in [('heatmap', heatmap), ('stats', statscard), ('langs', langscard)]:
    open(os.path.join(OUT, name + '.svg'), 'w').write(with_font(fn(data))); print('wrote', name)
