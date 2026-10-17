# -*- coding: utf-8 -*-
# NOTE: 本脚本产出的文档含与 青鹰SE Pro（112 kN 级）的横向对比；该机型不随本仓库分发。
"""Generate the integrated whitepaper (SE Pro + HaiDongQing) with inline SVG charts.

All numbers are taken from the shipped prefabs / PackData (verified by extracting the
actual component values), not from the design proposals.
"""
import os, sys, math, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_prefab as P

OUT = r"C:/Users/xjx20/WorkBuddy/sfs发动机/design"
ENG = r"G:/xiangmuweizhi/Modding Toolkit/Assets/Resources/Parts/Engines"

# ---------------------------------------------------------------- data
PRO = dict(key='pro', name='青鹰SE Pro', en='QingYin SE Pro', thrust=112, isp=311, mass=3.8,
           twr=112 / (3.8 * 9.81), cost=70, gimbal=7, length=2.5923, dia=1.0005,
           pack='青鹰SEPro.pack', bundle='qingyingpro', ver='1.0', pitch=0.155,
           prefab='QingYin Pro Engine.prefab', file='Assets/Resources/Parts/Engines/QingYin Pro Engine.prefab',
           accent='#9fb0c6', role='家族中坚 · 增压改进型',
           tagline='在 SE 的骨架上做增压改进：推力 +12%、比冲 +7%，代价是重量与造价同步上浮。')
HDQ = dict(key='hdq', name='海东青', en='HaiDongQing Engine（HDQ）', thrust=150, isp=318, mass=5.0,
           twr=150 / (5.0 * 9.81), cost=95, gimbal=8, length=2.900, dia=1.1495,
           pack='海东青引擎.pack', bundle='haidongqing', ver='1.1', pitch=0.14,
           prefab='HaiDongQing Engine.prefab', file='Assets/Resources/Parts/Engines/HaiDongQing Engine.prefab',
           accent='#e8963c', role='新系列首款 · 中型机',
           tagline='青鹰设计语言的直系延续，但构造独立：三级泵、环形集合器、三段喷管，填补 112→150 kN 的空档。')
SE = dict(name='青鹰 SE', thrust=100, isp=290, mass=3.5, cost=45, length=2.063)

def pct(a, b):
    return (b - a) / a * 100.0

# ---------------------------------------------------------------- silhouettes from the real prefabs
def world_profiles(path):
    docs = P.load_unity_file(path)
    gos = {f: b for f, (c, b) in docs.items() if c == 'GameObject'}
    tr_of = {}
    for f, b in gos.items():
        for e in b.get('m_Component') or []:
            cf = str(e.get('component', {}).get('fileID'))
            if cf in docs and docs[cf][0] == 'Transform':
                tr_of[f] = docs[cf][1]

    def num(d):
        try:
            return float(d.get('input'))
        except Exception:
            return 0.0

    out = {}
    for f, b in gos.items():
        name = b.get('m_Name')
        pipes = []
        for e in b.get('m_Component') or []:
            cf = str(e.get('component', {}).get('fileID'))
            if cf in docs and docs[cf][0] == 'MonoBehaviour' and 'composedShape' in docs[cf][1]:
                pipes.append(docs[cf][1])
        if not pipes:
            continue
        sx = sy = 1.0
        ox = oy = 0.0
        t = tr_of.get(f)
        chain = []
        while t is not None:
            chain.append(t)
            fa = t.get('m_Father', {}).get('fileID')
            t = docs.get(str(fa), (None, None))[1] if fa and str(fa) in docs else None
        for t in reversed(chain):
            ox += float(t.get('m_LocalPosition', {}).get('x', 0)) * sx
            oy += float(t.get('m_LocalPosition', {}).get('y', 0)) * sy
            sx *= float(t.get('m_LocalScale', {}).get('x', 1))
            sy *= float(t.get('m_LocalScale', {}).get('y', 1))
        pts = []
        for pt in pipes[0]['composedShape']['points']:
            x = num(pt['position']['x']); y = num(pt['position']['y'])
            wx = num(pt['width']['x']); wy = num(pt['width']['y'])
            pts.append((ox + x * sx, oy + y * sy, abs(wx) * abs(sx) / 2, abs(wy) * abs(sy) / 2))
        out[name] = pts
    return out

def silhouette_svg(profs, w, h, scale, color, accent, label, show_axis=True):
    """front silhouette; anchors the flange top (y=+0.1125) at the same screen y"""
    cx, top = w / 2, 26
    def sx(x): return cx + x * scale
    def sy(y): return top + (0.1125 - y) * scale
    parts = []
    for nm in ('Base', 'Nozzle', 'Nozzle Extension', 'Beam'):
        pts = profs.get(nm)
        if not pts:
            continue
        right = [(p[2], p[1]) for p in pts]
        left = [(-p[2], p[1]) for p in reversed(pts)]
        poly = right + left
        parts.append('<polygon points="%s" fill="%s" fill-opacity="0.30" stroke="%s" stroke-width="1.2" stroke-linejoin="round"/>' % (
            ' '.join('%.1f,%.1f' % (sx(x), sy(y)) for (x, y) in poly), color, color))
    for nm in ('Pump', 'Pump2'):
        pts = profs.get(nm)
        if not pts:
            continue
        outer = [(p[0] + p[2] * (1 if p[2] >= 0 else -1) * 0, p[1]) for p in pts]
        # draw the tube as a thick polyline through the centreline
        d = ' '.join('%.1f,%.1f' % (sx(p[0]), sy(p[1])) for p in pts)
        parts.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-opacity="0.85"/>' % (
            d, color, 0.1243 * scale))
    if show_axis:
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity="0.35" stroke-dasharray="3 4"/>' % (
            cx, top - 6, cx, top + 2.95 * scale, accent))
    return '<svg viewBox="0 0 %d %d" width="100%%" height="%d" xmlns="http://www.w3.org/2000/svg">%s</svg>' % (
        w, h, h, ''.join(parts))

# ---------------------------------------------------------------- charts
def bar_chart(rows, w=980):
    """rows: [(label, pro, hdq, fmt, better)]  one pair per row, normalised inside the row"""
    rowh, gap, left, barx, barw = 46, 10, 118, 128, 560
    h = gap + len(rows) * (rowh + gap) + 8
    out = ['<svg viewBox="0 0 %d %d" width="100%%" height="%d" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei, sans-serif">' % (w, h, h)]
    for i, (label, a, b, fmt, better) in enumerate(rows):
        y = gap + i * (rowh + gap)
        m = max(a, b) * 1.0
        wa = barw * (a / m); wb = barw * (b / m)
        out.append('<text x="%d" y="%.1f" fill="#8d97a8" font-size="13" text-anchor="end">%s</text>' % (left - 10, y + 22, label))
        out.append('<rect x="%d" y="%.1f" width="%.1f" height="15" rx="3" fill="#5d6b80"/>' % (barx, y + 2, max(2, wa)))
        out.append('<text x="%.1f" y="%.1f" fill="#c7d0dd" font-size="12.5" font-variant-numeric="tabular-nums">%s</text>' % (barx + max(2, wa) + 8, y + 14, fmt(a)))
        out.append('<rect x="%d" y="%.1f" width="%.1f" height="15" rx="3" fill="#e8963c"/>' % (barx, y + 22, max(2, wb)))
        out.append('<text x="%.1f" y="%.1f" fill="#f3c48b" font-size="12.5">%s</text>' % (barx + max(2, wb) + 8, y + 34.5, fmt(b)))
        d = pct(a, b)
        sign = '+' if d >= 0 else ''
        col = '#7fc08a' if (d > 0) == (better == 'up') else '#c97b5a'
        out.append('<text x="%d" y="%.1f" fill="%s" font-size="12" text-anchor="end">%s%.1f%%</text>' % (w - 12, y + 25, col, sign, d))
    out.append('</svg>')
    return ''.join(out)

def radar_chart(axes, a, b, w=520, h=430):
    """axes: [(label, unit)]; a/b: normalised 0..1 lists"""
    cx, cy, r = w / 2, h / 2 + 6, 128
    n = len(axes)
    out = ['<svg viewBox="0 0 %d %d" width="100%%" height="%d" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei, sans-serif">' % (w, h, h)]
    for ring in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for i in range(n):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            pts.append('%.1f,%.1f' % (cx + r * ring * math.cos(ang), cy + r * ring * math.sin(ang)))
        out.append('<polygon points="%s" fill="none" stroke="#2c3342" stroke-width="1"/>' % ' '.join(pts))
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#2c3342"/>' % (cx, cy, x, y))
        lx, ly = cx + (r + 26) * math.cos(ang), cy + (r + 26) * math.sin(ang)
        anchor = 'middle'
        if abs(math.cos(ang)) > 0.4:
            anchor = 'start' if math.cos(ang) > 0 else 'end'
        out.append('<text x="%.1f" y="%.1f" fill="#9aa3b3" font-size="12" text-anchor="%s">%s</text>' % (lx, ly + 4, anchor, axes[i][0]))
    def poly(vals, col, fill_op, dash=''):
        pts = []
        for i, v in enumerate(vals):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            pts.append('%.1f,%.1f' % (cx + r * v * math.cos(ang), cy + r * v * math.sin(ang)))
        style = ' stroke-dasharray="%s"' % dash if dash else ''
        dots = ''.join('<circle cx="%.1f" cy="%.1f" r="2.4" fill="%s"/>' % (
            cx + r * v * math.cos(-math.pi / 2 + 2 * math.pi * i / n),
            cy + r * v * math.sin(-math.pi / 2 + 2 * math.pi * i / n), col) for i, v in enumerate(vals))
        return ('<polygon points="%s" fill="%s" fill-opacity="%s" stroke="%s" stroke-width="1.6"%s/>%s' % (
            ' '.join(pts), col, fill_op, col, style, dots))
    out.append(poly(a, '#9fb0c6', '0.10', '5 4'))
    out.append(poly(b, '#e8963c', '0.20'))
    out.append('</svg>')
    return ''.join(out)

def scatter_chart(w=520, h=430):
    pts = [(SE['cost'], SE['thrust'], SE['mass'], '#5d6b80', '青鹰 SE', 1),
           (PRO['cost'], PRO['thrust'], PRO['mass'], '#9fb0c6', '青鹰SE Pro', -1),
           (HDQ['cost'], HDQ['thrust'], HDQ['mass'], '#e8963c', '海东青', 1)]
    x0, x1, y0, y1 = 40, 105, 90, 165
    L, B, T, R = 54, 42, 22, 22
    def X(v): return L + (v - x0) / (x1 - x0) * (w - L - R)
    def Y(v): return h - B - (v - y0) / (y1 - y0) * (h - B - T)
    out = ['<svg viewBox="0 0 %d %d" width="100%%" height="%d" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei, sans-serif">' % (w, h, h)]
    for gy in (100, 120, 140, 160):
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#252b37"/>' % (L, Y(gy), w - R, Y(gy)))
        out.append('<text x="%d" y="%.1f" fill="#6b7688" font-size="11" text-anchor="end">%d</text>' % (L - 8, Y(gy) + 4, gy))
    for gx in (40, 60, 80, 100):
        out.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#252b37"/>' % (X(gx), T, X(gx), h - B))
        out.append('<text x="%.1f" y="%d" fill="#6b7688" font-size="11" text-anchor="middle">%d</text>' % (X(gx), h - B + 16, gx))
    out.append('<text x="%.1f" y="%d" fill="#8d97a8" font-size="12" text-anchor="middle">造价（生涯）</text>' % (w / 2, h - 8))
    out.append('<text x="14" y="%.1f" fill="#8d97a8" font-size="12" transform="rotate(-90 14 %.1f)" text-anchor="middle">推力 kN</text>' % (h / 2, h / 2))
    for (c, t, m, col, name, side) in pts:
        rr = 6 + m * 1.6
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="0.22" stroke="%s" stroke-width="1.6"/>' % (X(c), Y(t), rr, col, col))
        out.append('<text x="%.1f" y="%.1f" fill="%s" font-size="12" text-anchor="%s">%s</text>' % (
            X(c) + (rr + 8) * side, Y(t) + 4, col, 'start' if side > 0 else 'end', name))
    out.append('</svg>')
    return ''.join(out)

# ---------------------------------------------------------------- build
pro_prof = world_profiles(os.path.join(ENG, PRO['prefab']))
hdq_prof = world_profiles(os.path.join(ENG, HDQ['prefab']))
se_prof = world_profiles(os.path.join(ENG, 'QingYin SE Engine.prefab'))

sil_pro = silhouette_svg(pro_prof, 260, 470, 150, '#9fb0c6', '#e8963c', 'SE Pro')
sil_hdq = silhouette_svg(hdq_prof, 260, 470, 150, '#e8963c', '#e8963c', 'HDQ')

# family line-up (three silhouettes, same scale)
def family_svg(w=980, h=250):
    scale = 62
    cx = [170, 490, 810]
    out = ['<svg viewBox="0 0 %d %d" width="100%%" height="%d" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei, sans-serif">' % (w, h, h)]
    for i, (pr, col, label, dx) in enumerate([(se_prof, '#6b7688', '青鹰 SE · 100 kN', 0),
                                              (pro_prof, '#9fb0c6', '青鹰SE Pro · 112 kN', 0),
                                              (hdq_prof, '#e8963c', '海东青 · 150 kN', 0)]):
        top = 24
        for nm in ('Base', 'Nozzle', 'Nozzle Extension'):
            pts = pr.get(nm)
            if not pts: continue
            right = [(p[2], p[1]) for p in pts]; left = [(-p[2], p[1]) for p in reversed(pts)]
            out.append('<polygon points="%s" fill="%s" fill-opacity="0.28" stroke="%s" stroke-width="1"/>' % (
                ' '.join('%.1f,%.1f' % (cx[i] + x * scale, top + (0.1125 - y) * scale) for (x, y) in right + left), col, col))
        out.append('<text x="%d" y="%d" fill="%s" font-size="12.5" text-anchor="middle">%s</text>' % (cx[i], h - 10, col, label))
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-opacity="0.4" stroke-dasharray="2 3"/>' % (
            cx[i], top - 4, cx[i], h - 24, col))
    out.append('</svg>')
    return ''.join(out)

rows = [
    ('推力 kN', PRO['thrust'], HDQ['thrust'], lambda v: '%.0f' % v, 'up'),
    ('真空比冲 s', PRO['isp'], HDQ['isp'], lambda v: '%.0f' % v, 'up'),
    ('推重比', round(PRO['twr'], 2), round(HDQ['twr'], 2), lambda v: '%.2f' % v, 'up'),
    ('摆角 ±°', PRO['gimbal'], HDQ['gimbal'], lambda v: '%.0f' % v, 'up'),
    ('干重 t', PRO['mass'], HDQ['mass'], lambda v: '%.2f' % v, 'down'),
    ('造价', PRO['cost'], HDQ['cost'], lambda v: '%.0f' % v, 'down'),
    ('总长 m', PRO['length'], HDQ['length'], lambda v: '%.2f' % v, 'down'),
    ('出口直径 m', PRO['dia'], HDQ['dia'], lambda v: '%.2f' % v, 'up'),
]

axes = [('推力', 'kN'), ('比冲', 's'), ('推重比', ''), ('摆角', '°'), ('推力密度', 'kN/m'), ('经济性', 'kN/造价')]
def norm(pair):
    return [v / max(pair) for v in pair]
vals = {
    '推力': (PRO['thrust'], HDQ['thrust']),
    '比冲': (PRO['isp'], HDQ['isp']),
    '推重比': (PRO['twr'], HDQ['twr']),
    '摆角': (PRO['gimbal'], HDQ['gimbal']),
    '推力密度': (PRO['thrust'] / PRO['length'], HDQ['thrust'] / HDQ['length']),
    '经济性': (PRO['thrust'] / PRO['cost'], HDQ['thrust'] / HDQ['cost']),
}
a_vals = []; b_vals = []
for name, _ in axes:
    a, b = vals[name]
    m = max(a, b)
    a_vals.append(a / m); b_vals.append(b / m)

# ---------------------------------------------------------------- HTML
def f2(v): return ('%.2f' % v)

CSS = """
:root{--bg:#0e1117;--pan:#151a22;--pan2:#1a2029;--line:#242b36;--txt:#d6dae2;--sub:#8b95a6;
--acc:#e8963c;--sil:#9fb0c6;--good:#7fc08a;--bad:#c97b5a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;line-height:1.72;font-size:15px}
.wrap{max-width:1120px;margin:0 auto;padding:48px 28px 80px}
h1{font-size:34px;margin:0 0 8px;letter-spacing:.5px}
h1 em{font-style:normal;color:var(--acc)}
.sub{color:var(--sub);font-size:14px;margin-bottom:6px}
.meta{color:#5f6a7c;font-size:12.5px;margin-bottom:34px}
.card{background:var(--pan);border:1px solid var(--line);border-radius:12px;padding:26px 28px;margin:22px 0}
.card h2{font-size:19px;margin:0 0 2px;padding-left:12px;border-left:3px solid var(--acc)}
.card .desc{color:var(--sub);font-size:13px;margin:6px 0 18px;padding-left:15px}
h3{font-size:15.5px;margin:26px 0 8px;color:#e8ecf3}
h3 .n{color:var(--acc);font-family:Consolas,monospace;margin-right:8px;font-size:13px}
p{margin:8px 0}
ul{margin:8px 0 8px 4px;padding-left:20px}
li{margin:5px 0}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0 4px}
th,td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--sub);font-weight:600;font-size:12.5px;letter-spacing:.3px}
td.num{font-variant-numeric:tabular-nums;font-family:Consolas,"SF Mono",monospace;color:#e5eaf3}
tr:last-child td{border-bottom:none}
.up{color:var(--good)}.dn{color:var(--bad)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
@media(max-width:860px){.grid2,.grid3{grid-template-columns:1fr}}
.feat{background:var(--pan2);border:1px solid var(--line);border-radius:9px;padding:13px 15px;font-size:13.5px}
.feat b{color:var(--acc);display:block;margin-bottom:3px;font-size:13.5px}
.prod{display:grid;grid-template-columns:1fr 300px;gap:26px;align-items:start}
@media(max-width:860px){.prod{grid-template-columns:1fr}}
.chip{display:inline-block;border:1px solid var(--line);background:#1d232d;border-radius:999px;
padding:2px 10px;font-size:12px;color:var(--sub);margin:0 6px 6px 0}
.chip b{color:var(--txt);font-weight:600}
.hero{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:26px 0 8px}
@media(max-width:860px){.hero{grid-template-columns:1fr}}
.pcard{border-radius:12px;padding:22px 24px;border:1px solid var(--line);background:linear-gradient(180deg,rgba(255,255,255,.03),transparent)}
.pcard h4{margin:0 0 4px;font-size:20px}
.pcard .role{font-size:12.5px;color:var(--sub);letter-spacing:.4px;margin-bottom:10px}
.pcard .big{display:flex;gap:22px;margin-top:12px}
.pcard .big div{font-size:12px;color:var(--sub)}
.pcard .big strong{display:block;font-size:21px;color:#eef1f6;font-variant-numeric:tabular-nums}
.toc{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}
.toc a{color:var(--sub);text-decoration:none;font-size:12.5px;border:1px solid var(--line);
border-radius:6px;padding:4px 10px}
.toc a:hover{color:var(--acc);border-color:#4a3a22}
.note{color:var(--sub);font-size:12.5px;margin-top:10px}
.kv{display:grid;grid-template-columns:96px 1fr;gap:2px 12px;font-size:13.5px}
.kv span:nth-child(odd){color:var(--sub)}
code{background:#1d232d;border:1px solid var(--line);border-radius:4px;padding:1px 6px;
font-family:Consolas,monospace;font-size:12.5px;color:#e5c79b}
.step{display:grid;grid-template-columns:26px 1fr;gap:10px;margin:9px 0}
.step i{font-style:normal;color:var(--acc);font-family:Consolas,monospace}
"""

def card(title, desc, body, anchor=None):
    a = ' id="%s"' % anchor if anchor else ''
    return '<div class="card"%s><h2>%s</h2><div class="desc">%s</div>%s</div>' % (a, title, desc, body)

def spec_table(d, ref=None):
    rows = [
        ('推力', '%.0f kN' % d['thrust']),
        ('真空比冲', '%.0f s' % d['isp']),
        ('干重', '%.2f t' % d['mass']),
        ('推重比', '%.2f' % d['twr']),
        ('万向摆角', '±%.0f°' % d['gimbal']),
        ('造价（生涯）', '%.0f' % d['cost']),
        ('总长', '%.3f m' % d['length']),
        ('最大直径（出口）', '%.3f m' % d['dia']),
        ('对接法兰', 'Φ1.000 m · 对接口 +0.1125'),
        ('推进剂', 'Liquid Fuel（液氧/煤油类）'),
        ('音效基频', '%.3f' % d['pitch']),
        ('包版本 / 标签', '%s / %s' % (d['ver'], d['bundle'])),
    ]
    if d['key'] == 'pro':
        rows.insert(8, ('喷管构成', '两件式：本体 + 可拆延伸裙（联动环）'))
        rows.insert(9, ('泵组', '两段式涡轮泵 ×2（进气管 + 泵体）'))
        rows.insert(10, ('质心 / 推力作用点', 'y = -0.72 / -3.70'))
    else:
        rows.insert(8, ('喷管构成', '三段式：主段 + 联动环 + 延伸裙（卷边唇口）'))
        rows.insert(9, ('泵组', '三级台阶泵体 + 环形集合器 + 内弯肘管'))
        rows.insert(10, ('质心 / 推力作用点', 'y = -0.85 / -4.10'))
    body = ''.join('<tr><td>%s</td><td class="num">%s</td></tr>' % (k, v) for k, v in rows)
    return '<table><tr><th>项目</th><th>数值</th></tr>%s</table>' % body

html_doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>青鹰SE Pro &amp; 海东青 · 产品白皮书</title>
<style>%(css)s</style></head><body><div class="wrap">

<h1>青鹰SE Pro <em>&amp;</em> 海东青 · 产品白皮书</h1>
<div class="sub">Spaceflight Simulator 自定义发动机 · 产品定位 / 核心功能 / 适用场景 / 关键规格 / 使用与部署 / 性能对比</div>
<div class="meta">版本 1.0 · 2026-10-17 · 作者 zzasza · 数据取自现役 prefab 与 PackData（非设计估算值）</div>

<div class="toc">
  <a href="#family">家族谱系</a><a href="#pro">青鹰SE Pro</a><a href="#hdq">海东青</a>
  <a href="#compare">性能对比</a><a href="#deploy">安装与部署</a><a href="#notes">维护与已知边界</a>
</div>

<div class="hero">
  <div class="pcard" style="border-color:#2b3648">
    <h4 style="color:%(procol)s">青鹰SE Pro</h4>
    <div class="role">%(prole)s</div>
    <div style="font-size:13.5px;color:#aab3c2">%(ptag)s</div>
    <div class="big">
      <div><strong>112</strong>推力 kN</div><div><strong>311</strong>比冲 s</div>
      <div><strong>±7°</strong>摆角</div><div><strong>3.80</strong>干重 t</div>
    </div>
  </div>
  <div class="pcard" style="border-color:#4a3a22">
    <h4 style="color:%(hdqcol)s">海东青 <span style="font-size:13px;color:#8b95a6">HaiDongQing</span></h4>
    <div class="role">%(hrole)s</div>
    <div style="font-size:13.5px;color:#aab3c2">%(htag)s</div>
    <div class="big">
      <div><strong>150</strong>推力 kN</div><div><strong>318</strong>比冲 s</div>
      <div><strong>±8°</strong>摆角</div><div><strong>5.00</strong>干重 t</div>
    </div>
  </div>
</div>

%(family)s

%(pro)s

%(hdq)s

%(compare)s

%(deploy)s

%(notes)s

<div class="note" style="text-align:center;margin-top:34px">
青鹰SE Pro &amp; 海东青 产品白皮书 · v1.0 · 2026-10-17 · zzasza
</div>
</div></body></html>"""

family = card('一、家族谱系与产品定位', '同一条设计语言下的三个推力档位：宽平双色顶盘、细颈动力段、内弯肘管、锥形钟喷管、橙色识别色。',
    family_svg() + """
    <table style="margin-top:16px">
      <tr><th>型号</th><th>推力</th><th>比冲</th><th>干重</th><th>造价</th><th>定位</th></tr>
      <tr><td>青鹰 SE</td><td class="num">100 kN</td><td class="num">290 s</td><td class="num">3.50 t</td><td class="num">45</td><td>家族原型 · 入门档</td></tr>
      <tr><td>青鹰SE Pro</td><td class="num">112 kN</td><td class="num">311 s</td><td class="num">3.80 t</td><td class="num">70</td><td>家族中坚 · 增压改进型</td></tr>
      <tr><td><b style="color:#e8963c">海东青</b></td><td class="num">150 kN</td><td class="num">318 s</td><td class="num">5.00 t</td><td class="num">95</td><td>新系列首款 · 中型档（承接向上的推力空缺）</td></tr>
    </table>
    <p class="note">三款共用同一套 Φ1.000 对接法兰与 +0.1125 对接口，可任意混编、叠配、并排；差别集中在推力档位、泵组构造与喷管分段方式。</p>""", 'family')

pro_sec = card('二、青鹰SE Pro', PRO['tagline'],
    '<div class="prod"><div>'
    '<h3><span class="n">2.1</span>产品定位</h3>'
    '<p>家族第二代。在 SE 的骨架上做增压改进：燃烧室压力与泵功率上抬，换来 112 kN 推力与 311 s 真空比冲；'
    '代价是重量、尺寸与造价同步上浮（对比 SE：推力 +12%、比冲 +7%、干重 +8.6%、造价 +56%）。</p>'
    '<p>它不是"更大一号"，而是同一推力级内的效率优化：喷管改成两件式、涡轮泵改成两段式，'
    '让同一副骨架承担更高的室压。</p>'
    '<h3><span class="n">2.2</span>核心功能</h3>'
    '<div class="grid2">'
    '<div class="feat"><b>两件式喷管</b>本体在 y=-1.72 截断，加装独立延伸裙：套筒 + 深色联动环，接缝清晰可见；卸裙即得短喷管（海平面）构型。</div>'
    '<div class="feat"><b>两段式涡轮泵 ×2</b>下部细进气管 + 内弯肘管（沿用 SE 手法），上部粗泵体带台阶，暗示更高泵功率。</div>'
    '<div class="feat"><b>家族双色顶盘</b>Metal×0.9 / Color_White×0.45 分色，分缝落在 y=0；法兰与 SE 完全一致。</div>'
    '<div class="feat"><b>更强的控制力</b>摆角 ±7°（SE 为 ±5°），配合 3.00 的推重比，适合做末级姿控与着陆段。</div>'
    '</div>'
    '<h3><span class="n">2.3</span>适用场景</h3>'
    '<ul>'
    '<li><b>小型运载器芯级 / 单级入轨方案的主动力</b>——112 kN 配 1 m 级贮箱，推重比起飞段约 1.2–1.4。</li>'
    '<li><b>上面级与轨道机动级</b>——311 s 比冲在同尺寸里偏高，单位推进剂速度增量更划算。</li>'
    '<li><b>着陆级 / 月面下降级</b>——±7° 摆角便于重心偏移补偿，短喷管（卸裙）构型更贴地。</li>'
    '<li><b>与 SE 混编</b>——SE 做助推、Pro 做芯级，两者法兰与对接口一致，级间不需要转接件。</li>'
    '</ul>'
    '<p class="note">不擅长：需要 150 kN 级单机推力的中型构型（此时应选海东青），以及追求最低造价的廉价一次性方案（选 SE）。</p>'
    '</div><div>{SIL}</div></div>'.replace('{SIL}', sil_pro), 'pro')

hdq_sec = card('三、海东青（HDQ）', HDQ['tagline'],
    '<div class="prod"><div>'
    '<h3><span class="n">3.1</span>产品定位</h3>'
    '<p>青鹰设计语言的直系延续，但作为独立系列的首款：<b>三级泵 + 环形集合器 + 三段喷管</b>。'
    '定位在 SE Pro 之上，填补 112→150 kN 的空档，为后续更大推力型号留出接口与命名空间（HDQ-2/HDQ-3）。</p>'
    '<p>与 Pro 的关系是"线性放大 + 局部升级"：推力 +34%、干重 +32%、造价 +36%，'
    '单位推力成本几乎不变（0.625 → 0.633 kN/造价），但比冲 +2.3%、摆角 +14% 属于净增益。</p>'
    '<h3><span class="n">3.2</span>核心功能</h3>'
    '<div class="grid2">'
    '<div class="feat"><b>三级台阶泵体</b>Φ0.370 / 0.442 / 0.408 三级外露台阶，暗示更高泵功率；台阶以圆角过渡，不再刀切。</div>'
    '<div class="feat"><b>环形集合器（橙色识别环）</b>两侧内弯肘管不再直插颈部，而是先汇入颈下一圈橙色集合环，再进入泵——家族识别色的构造化。</div>'
    '<div class="feat"><b>三段式钟形喷管</b>主段（中灰）+ 深色套筒联动环（出口上方 0.85 m 接缝）+ 浅色延伸裙 + 卷边厚唇口。</div>'
    '<div class="feat"><b>桁架加强边梁</b>顶盘下沿一圈深色实心环（半宽 1.033 略大于盘面），承担中型机的承载叙事。</div>'
    '<div class="feat"><b>无外露接缝</b>肘管两端均插入实体（顶端深入顶盘、末端径向插入集合环内部），仰视与转动都不露管口。</div>'
    '<div class="feat"><b>精确定位色带</b>色带按层高对齐（喉部识别环、集合环为橙色），涂装分界与结构分界严格重合。</div>'
    '</div>'
    '<h3><span class="n">3.3</span>适用场景</h3>'
    '<ul>'
    '<li><b>中型运载器芯级</b>——150 kN 单机，双机并联即 300 kN 级起飞推力。</li>'
    '<li><b>重型助推并联</b>——推重比 3.06、干重 5 t，作为捆绑助推时结构负担可控。</li>'
    '<li><b>载人 / 货运上升段主动力</b>——较大的裙段出口（Φ1.15）在低空段提供更高的面积比容差。</li>'
    '<li><b>重心偏移较大的构型</b>——±8° 摆角比 Pro 多 14%，适合不对称载荷或需要更强配平余量的方案。</li>'
    '</ul>'
    '<p class="note">不擅长：小推力精细着陆（自重 5 t，最低推力偏大）；预算敏感的一次性上面级（Pro 更划算）。</p>'
    '</div><div>{SIL}</div></div>'.replace('{SIL}', sil_hdq), 'hdq')

compare = card('四、性能对比', '同口径实测参数对比；百分比为海东青相对青鹰SE Pro 的变化（绿色为更优，红色为代价）。',
    '<h3 style="margin-top:0"><span class="n">4.1</span>关键指标逐项对比</h3>' + bar_chart(rows) +
    '<div class="note">每行按两者中的较大值归一，条形末端为实测值，右侧为相对变化。</div>'
    '<div class="grid2" style="margin-top:22px;align-items:start">'
    '<div><h3 style="margin-top:0"><span class="n">4.2</span>综合能力雷达</h3>' + radar_chart(axes, a_vals, b_vals) +
    '<div class="note">各轴按两者中的较大值归一；推力密度 = 推力/总长，经济性 = 推力/造价。</div></div>'
    '<div><h3 style="margin-top:0"><span class="n">4.3</span>推力—造价定位</h3>' + scatter_chart() +
    '<div class="note">气泡面积对应干重；青鹰 SE 作为家族基准一并列出。</div></div>'
    '</div>'
    '<div style="margin-top:6px">'
    '<h3><span class="n">4.4</span>对比表</h3>'
    '<table>'
    '<tr><th>项目</th><th>青鹰SE Pro</th><th>海东青</th><th>变化</th></tr>'
    '<tr><td>推力</td><td class="num">112 kN</td><td class="num">150 kN</td><td class="num up">+33.9%</td></tr>'
    '<tr><td>真空比冲</td><td class="num">311 s</td><td class="num">318 s</td><td class="num up">+2.3%</td></tr>'
    '<tr><td>推重比</td><td class="num">3.00</td><td class="num">3.06</td><td class="num up">+1.8%</td></tr>'
    '<tr><td>万向摆角</td><td class="num">±7°</td><td class="num">±8°</td><td class="num up">+14.3%</td></tr>'
    '<tr><td>干重</td><td class="num">3.80 t</td><td class="num">5.00 t</td><td class="num dn">+31.6%</td></tr>'
    '<tr><td>造价</td><td class="num">70</td><td class="num">95</td><td class="num dn">+35.7%</td></tr>'
    '<tr><td>总长</td><td class="num">2.592 m</td><td class="num">2.900 m</td><td class="num dn">+11.9%</td></tr>'
    '<tr><td>最大直径</td><td class="num">1.000 m</td><td class="num">1.150 m</td><td class="num">+14.9%</td></tr>'
    '<tr><td>推力密度（kN/m）</td><td class="num">43.2</td><td class="num">51.7</td><td class="num up">+19.7%</td></tr>'
    '<tr><td>单位推力造价</td><td class="num">0.625</td><td class="num">0.633</td><td class="num">+1.3%</td></tr>'
    '</table>'
    '<h3><span class="n">4.5</span>选型建议</h3>'
    '<ul style="margin-top:4px">'
    '<li><b>要更轻、更便宜、更短</b> → 青鹰SE Pro。单位推力造价略优，2.59 m 的短机身对小型构型更友好。</li>'
    '<li><b>要更大推力或更大摆角</b> → 海东青。它是"把 Pro 线性放大"的产物，边际成本几乎没有恶化。</li>'
    '<li><b>混合编队</b>：SE 助推 + Pro 芯级用于小型方案；Pro 助推 + 海东青芯级用于中型方案。</li>'
    '</ul>'
    '</div>', 'compare')

deploy = card('五、安装与部署', '两个包互相独立，可同时安装；文件名与标签不影响共存。',
    '<div class="grid2">'
    '<div><h3 style="margin-top:0"><span class="n">5.1</span>安装步骤</h3>'
    '<div class="step"><i>01</i><div>把 <code>{PPACK}</code> 与 <code>{HPACK}</code> 复制到<br><code>Spaceflight Simulator Game / Mods / Custom_Assets / Parts /</code></div></div>'
    '<div class="step"><i>02</i><div>启动游戏，进入 <b>建造界面</b>，在发动机分类中找到两款部件（图标为深色底、橙色识别环）。</div></div>'
    '<div class="step"><i>03</i><div>首次使用若没有出现，退出重进一次（Mod 列表在启动时扫描 <code>Parts</code> 目录）。</div></div>'
    '<div class="step"><i>04</i><div>不需要时直接删除对应 <code>.pack</code> 文件即可，不残留资源。</div></div>'
    '<h3><span class="n">5.2</span>建造与叠配</h3>'
    '<ul>'
    '<li>两者对接法兰均为 <b>Φ1.000 m、对接口 +0.1125</b>，可与 SE / SE Pro / 海东青任意叠配。</li>'
    '<li>引擎底部出口自带附着面，可作为"引擎串联"或级间分离的基准面。</li>'
    '<li>燃料接口为 <code>Liquid Fuel</code>，与游戏自带贮箱直接连通，无需额外管线。</li>'
    '</ul></div>'
    '<div><h3 style="margin-top:0"><span class="n">5.3</span>飞行注意事项</h3>'
    '<ul>'
    '<li><b>万向节</b>随发动机点火启用：Pro ±7°、海东青 ±8°，可在建造界面关闭以省电。</li>'
    '<li><b>热区</b>随推力放大：海东青的受热区宽度 1.90（Pro 为 1.55，+23%）、长度 9.2（+10%），'
    '贴近其它部件布置时请留出间距。</li>'
    '<li><b>卸裙构型</b>：Pro 的延伸裙段为独立网格，可在 prefab 中停用该节点获得海平面短喷管（不影响其它部件）。</li>'
    '<li><b>质心</b>：Pro 在 y=-0.72、海东青在 y=-0.85（自法兰向下），堆叠时注意配平。</li>'
    '</ul>'
    '<h3><span class="n">5.4</span>调参与重新打包</h3>'
    '<p style="font-size:13.5px">在 Unity 工程中修改 prefab 的 <code>Part.mass</code>、<code>EngineModule.thrust / ISP</code>、'
    '<code>MoveModule</code> 摆角曲线后，用菜单重新打包并自动部署：</p>'
    '<div class="kv" style="margin-top:6px">'
    '<span>SE Pro</span><span><code>SFS → QingYin Pro → Rebuild + Build + Export Pack</code></span>'
    '<span>海东青</span><span><code>SFS → HaiDongQing → Repair Junctions + Rebuild Pack</code></span>'
    '</div>'
    '<p class="note">两个脚本都会把成品直接写入游戏 Mods 目录，并覆盖同名 pack。</p>'
    '</div></div>'.replace('{PPACK}', PRO['pack']).replace('{HPACK}', HDQ['pack']), 'deploy')

notes = card('六、维护说明与已知边界', '供后续迭代参考。',
    '<div class="grid3">'
    '<div class="feat"><b>色带高度</b>PipeMesh 的色带/材质层高度按<b>累计 Δy</b> 解释，不是弧长；调轮廓后必须同步重算。</div>'
    '<div class="feat"><b>零高度段</b>相邻两点 y 相同的线段会被整段丢弃；台阶与底面必须留 ≥2 mm 的 y 差。</div>'
    '<div class="feat"><b>管口封闭</b>管件是单面壳体，任何外露管口都会"看穿"；两端需埋入实体或被实体面遮住。</div>'
    '</div>'
    '<p class="note" style="margin-top:14px">数值平衡基于设计建议值，尚未经过长时间飞行实测；'
    '若后续调整推力/比冲，建议同步复核推重比与造价，保持"单位推力成本不恶化"这一家族约束。</p>', 'notes')

doc = (html_doc
       .replace('%(css)s', CSS)
       .replace('%(procol)s', '#9fb0c6').replace('%(hdqcol)s', '#e8963c')
       .replace('%(prole)s', PRO['role']).replace('%(hrole)s', HDQ['role'])
       .replace('%(ptag)s', PRO['tagline']).replace('%(htag)s', HDQ['tagline'])
       .replace('%(family)s', family).replace('%(pro)s', pro_sec).replace('%(hdq)s', hdq_sec)
       .replace('%(compare)s', compare).replace('%(deploy)s', deploy).replace('%(notes)s', notes))

path = os.path.join(OUT, '青鹰SEPro_海东青_产品白皮书.html')
open(path, 'w', encoding='utf-8').write(doc)
print('written', path, len(doc), 'bytes')
