# -*- coding: utf-8 -*-
"""2D preview of the HDQ part (front view, colour bands)."""
import sys, os, math, json
from PIL import Image, ImageDraw, ImageFont

OUT = r"C:/Users/xjx20/WorkBuddy/sfs发动机/design"
TOOLS = r"C:/Users/xjx20/WorkBuddy/sfs发动机/tools"
SPEC = json.load(open(os.path.join(TOOLS, 'hdq_spec.json'), encoding='utf-8'))

def font(sz, bold=False):
    for pth in ([r"C:/Windows/Fonts/msyhbd.ttc", r"C:/Windows/Fonts/msyh.ttc"] if bold
                else [r"C:/Windows/Fonts/msyh.ttc"]):
        try:
            return ImageFont.truetype(pth, sz)
        except Exception:
            pass
    return ImageFont.load_default()

def shade(tint, tex):
    if tex == 'orange':
        return (231, 150, 62)
    base = {'smooth': 206, 'machined': 228, 'plate_hi': 226, 'plate_lo': 292}.get(tex, 220)
    v = max(0.0, min(1.0, tint[0]))
    c = min(255, base * v)
    return (int(c), int(c * 0.995), int(min(255, c * 1.015)))

def cum_len(pts):
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]))
    return c

def sample(pts, c, t):
    """(y, r) at cumulative distance t along the profile"""
    if t <= 0:
        return pts[0]
    for i in range(1, len(c)):
        if c[i] >= t - 1e-12:
            span = c[i] - c[i-1]
            k = 0.0 if span <= 0 else (t - c[i-1]) / span
            return (pts[i-1][0] + k*(pts[i][0]-pts[i-1][0]),
                    pts[i-1][1] + k*(pts[i][1]-pts[i-1][1]))
    return pts[-1]

def draw_object(d, pts, bands, ox, oy, sc):
    c = cum_len(pts)
    prev = 0.0
    for b in bands:
        t0, t1 = prev, b['h']
        strip = [sample(pts, c, t0)]
        for i, ci in enumerate(c):
            if t0 + 1e-9 < ci < t1 - 1e-9:
                strip.append(pts[i])
        strip.append(sample(pts, c, t1))
        poly = [(ox + r*sc, oy - y*sc) for (y, r) in strip] + \
               [(ox - r*sc, oy - y*sc) for (y, r) in reversed(strip)]
        d.polygon(poly, fill=shade(b['tint'], b['tex']))
        prev = b['h']
    outline = [(ox + r*sc, oy - y*sc) for (y, r) in pts] + \
              [(ox - r*sc, oy - y*sc) for (y, r) in reversed(pts)]
    d.line(outline + [outline[0]], fill=(52, 56, 64), width=2)
    # seam edges at both ends (so the two-piece joint reads)
    for y, r in (pts[0], pts[-1]):
        d.line([(ox - r*sc, oy - y*sc), (ox + r*sc, oy - y*sc)], fill=(52, 56, 64), width=2)

def draw_tube(d, pts, ox, oy, sc, col=(170, 174, 184)):
    """pts = (x, y, wx, wy)"""
    out_o, out_i = [], []
    for (x, y, wx, wy) in pts:
        out_o.append((ox + (x + wx/2)*sc, oy - (y + wy/2)*sc))
        out_i.append((ox + (x - wx/2)*sc, oy - (y - wy/2)*sc))
    poly = out_o + list(reversed(out_i))
    d.polygon(poly, fill=col, outline=(52, 56, 64))

W, H = 900, 1080
img = Image.new('RGB', (W, H), (18, 21, 28))
d = ImageDraw.Draw(img)
d.text((36, 22), '海东青（HDQ）正视图 · 按生成数据绘制', font=font(30, True), fill=(236, 239, 245))
d.text((38, 64), '世界尺度；色带 = PipeMesh 的 tint 分层', font=font(16), fill=(140, 148, 165))

ox, oy, sc = 470, 120, 320
for nm in ('Pump', 'Pump2'):
    draw_tube(d, SPEC[nm]['points'], ox, oy, sc)
for nm in ('Nozzle', 'Nozzle Extension', 'Beam', 'Base'):
    draw_object(d, [(p[0], p[1]) for p in SPEC[nm]['points']], SPEC[nm]['bands'], ox, oy, sc)

def dim_v(d, x, y0, y1, txt):
    d.line([(x, oy - y0*sc), (x, oy - y1*sc)], fill=(120, 128, 142), width=1)
    for yy in (y0, y1):
        d.line([(x-6, oy - yy*sc), (x+6, oy - yy*sc)], fill=(120, 128, 142), width=1)
    d.text((x - 10, (oy - (y0+y1)/2*sc)), txt, font=font(15), fill=(170, 178, 192), anchor='rm')

def dim_h(d, y, x0, x1, txt, above=True):
    d.line([(ox + x0*sc, oy - y*sc), (ox + x1*sc, oy - y*sc)], fill=(120, 128, 142), width=1)
    for xx in (x0, x1):
        d.line([(ox + xx*sc, oy - y*sc - 6), (ox + xx*sc, oy - y*sc + 6)], fill=(120, 128, 142), width=1)
    d.text((ox + (x0+x1)/2*sc, oy - y*sc - (24 if above else -24)), txt,
           font=font(15), fill=(170, 178, 192), anchor='mm')

dim_v(d, ox - 0.86*sc, 0.1125, -2.7875, '2.90')
dim_h(d, 0.26, -0.5, 0.5, 'Φ1.00 对接法兰')
dim_h(d, -3.02, -0.6842, 0.6842, 'Φ1.368', above=False)

img.save(os.path.join(OUT, 'hdq_preview.png'))
print('saved', os.path.join(OUT, 'hdq_preview.png'))
