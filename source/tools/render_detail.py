# -*- coding: utf-8 -*-
"""Close-up perspective render of the HDQ upper assembly (junction check)."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TOOLS = r"C:/Users/xjx20/WorkBuddy/sfs发动机/tools"
DESIGN = r"C:/Users/xjx20/WorkBuddy/sfs发动机/design"
SPEC = json.load(open(os.path.join(TOOLS, 'hdq_spec.json'), encoding='utf-8'))

BASE_RGB = {'smooth': (168, 172, 182), 'machined': (134, 138, 146),
            'plate_hi': (192, 196, 204), 'plate_lo': (216, 219, 224), 'orange': (232, 150, 62)}

def band_color(b):
    if b['tex'] == 'orange':
        return np.array([232, 152, 64], dtype=float)
    base = np.array(BASE_RGB.get(b['tex'], (150, 150, 150)), dtype=float)
    return base * (0.30 + 0.72 * min(1.0, b['tint'][0]))

def cum_len(pts):
    # SFS measures colour layers in cumulative |Δy| (verified empirically)
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + abs(pts[i][0] - pts[i-1][0]))
    return c

def lathe(tris, pts, bands, segs=72):
    cum = cum_len(pts)
    ang = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    rings = [np.stack([r * np.cos(ang), np.full(segs, y), r * np.sin(ang)], axis=1) for (y, r) in pts]
    def band_of(t):
        for b in bands:
            if t <= b['h'] + 1e-9:
                return b
        return bands[-1]
    for i in range(len(pts) - 1):
        col = band_color(band_of((cum[i] + cum[i+1]) / 2))
        for k in range(segs):
            k2 = (k + 1) % segs
            tris.append((np.array([rings[i][k], rings[i][k2], rings[i+1][k2]]), col))
            tris.append((np.array([rings[i][k], rings[i+1][k2], rings[i+1][k]]), col))

def swept(tris, pts, col, segs=28):
    ang = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    rings = []
    for (x, y, wx, wy) in pts:
        w = math.hypot(wx, wy)
        if w < 1e-9:
            w = 1e-4
        px, py = wx / w, wy / w
        r = w / 2.0
        rings.append(np.stack([x + r * (px * np.cos(ang)), y + r * (py * np.cos(ang)), r * np.sin(ang)], axis=1))
    for i in range(len(rings) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            tris.append((np.array([rings[i][k], rings[i][k2], rings[i+1][k2]]), col))
            tris.append((np.array([rings[i][k], rings[i+1][k2], rings[i+1][k]]), col))

def raster(tris, W, H, yaw, pitch, cy, scale, dist=6.5, cx=0.0):
    yaw, pitch = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(pitch), -math.sin(pitch)], [0, math.sin(pitch), math.cos(pitch)]])
    R = Rx @ Ry
    light = np.array([-0.35, 0.55, 0.76]); light /= np.linalg.norm(light)
    img = np.zeros((H, W, 3), dtype=np.float32) + np.array([14, 17, 22], dtype=np.float32)
    zb = np.full((H, W), 1e9, dtype=np.float32)
    focal = scale * dist
    for quad, col in tris:
        p = quad @ R.T
        d = dist - p[:, 2]
        if (d < 0.2).any():
            continue
        sx = W / 2 + (p[:, 0] - cx) * focal / d
        sy = H / 2 + (cy - p[:, 1]) * focal / d
        n = np.cross(quad[1] - quad[0], quad[2] - quad[0])
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        lam = abs(float(np.dot(n / ln, light)))
        c = np.clip(col * (0.20 + 0.80 * lam), 0, 255)
        x0, x1 = int(max(0, np.floor(sx.min()))), int(min(W - 1, np.ceil(sx.max())))
        y0, y1 = int(max(0, np.floor(sy.min()))), int(min(H - 1, np.ceil(sy.max())))
        if x1 < x0 or y1 < y0:
            continue
        area = (sx[1]-sx[0])*(sy[2]-sy[0]) - (sx[2]-sx[0])*(sy[1]-sy[0])
        if abs(area) < 1e-9:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1+1) + 0.5, np.arange(y0, y1+1) + 0.5)
        w0 = ((sx[1]-X)*(sy[2]-Y) - (sx[2]-X)*(sy[1]-Y)) / area
        w1 = ((sx[2]-X)*(sy[0]-Y) - (sx[0]-X)*(sy[2]-Y)) / area
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        zz = 1.0 / (w0/d[0] + w1/d[1] + w2/d[2])       # perspective-correct depth
        sub = zb[y0:y1+1, x0:x1+1]
        bt = m & (zz < sub)
        sub[bt] = zz[bt]
        img[y0:y1+1, x0:x1+1][bt] = c
    return Image.fromarray(img.astype(np.uint8))

def build():
    tris = []
    for nm in ('Nozzle', 'Nozzle Extension', 'Beam', 'Base'):
        lathe(tris, [(p[0], p[1]) for p in SPEC[nm]['points']], SPEC[nm]['bands'])
    for nm in ('Pump', 'Pump2'):
        swept(tris, SPEC[nm]['points'], np.array([215.0, 60.0, 60.0]) if os.environ.get('DBG') else np.array([150.0, 155.0, 165.0]))
    return tris

if __name__ == '__main__':
    tris = build()
    W, H = 1000, 820
    img = raster(tris, W, H, yaw=-22, pitch=-20, cy=-0.28, scale=760)   # 上方组件
    d = ImageDraw.Draw(img)
    try:
        f1 = ImageFont.truetype(r"C:/Windows/Fonts/msyhbd.ttc", 26)
    except Exception:
        f1 = ImageFont.load_default()
    d.text((26, 20), '海东青引擎 · 上方组件特写（修正后）', font=f1, fill=(236, 239, 245))
    img.save(os.path.join(DESIGN, 'hdq_closeup.png'))
    print('saved hdq_closeup.png')
