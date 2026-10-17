# -*- coding: utf-8 -*-
"""Offline 3D preview of the HDQ part with a real z-buffer rasteriser."""
import json, math, os
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
    t = min(1.0, b['tint'][0])
    return base * (0.30 + 0.72 * t)

def cum_len(pts):
    # SFS measures colour layers in cumulative |Δy| (verified empirically)
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + abs(pts[i][0] - pts[i-1][0]))
    return c

def lathe(tris, pts, bands, segs=64):
    cum = cum_len(pts)
    ang = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    rings = [np.stack([r * np.cos(ang), np.full(segs, y), r * np.sin(ang)], axis=1) for (y, r) in pts]
    def band_of(t):
        for b in bands:
            if t <= b['h'] + 1e-9:
                return b
        return bands[-1]
    for i in range(len(pts) - 1):
        col = band_color(band_of((cum[i] + cum[i + 1]) / 2))
        for k in range(segs):
            k2 = (k + 1) % segs
            a, b_, c, d = rings[i][k], rings[i][k2], rings[i+1][k2], rings[i+1][k]
            tris.append((np.array([a, b_, c]), col))
            tris.append((np.array([a, c, d]), col))
    for idx, nb in ((0, bands[0]), (len(pts) - 1, bands[-1])):
        col = band_color(nb)
        apex = np.array([0.0, pts[idx][0], 0.0])
        for k in range(segs):
            k2 = (k + 1) % segs
            tris.append((np.array([rings[idx][k], rings[idx][k2], apex]), col))

def swept(tris, pts, col, segs=24):
    ang = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    rings = []
    for (x, y, wx, wy) in pts:
        w = math.hypot(wx, wy)
        if w < 1e-9:
            w = 1e-4
        # the width vector IS the cross-section direction in the XY plane
        px, py = wx / w, wy / w
        r = w / 2.0
        ring = np.stack([x + r * (px * np.cos(ang)), y + r * (py * np.cos(ang)), r * np.sin(ang)], axis=1)
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            a, b_, c, d = rings[i][k], rings[i][k2], rings[i+1][k2], rings[i+1][k]
            tris.append((np.array([a, b_, c]), col))
            tris.append((np.array([a, c, d]), col))
    apex = rings[-1].mean(axis=0)
    for k in range(segs):
        k2 = (k + 1) % segs
        tris.append((np.array([rings[-1][k], rings[-1][k2], apex]), col))

def rasterize(tris, W=900, H=1150, yaw=-26, pitch=-6, scale=330, center=(0.0, -1.32)):
    yaw, pitch = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(pitch), -math.sin(pitch)], [0, math.sin(pitch), math.cos(pitch)]])
    R = Rx @ Ry
    light = np.array([-0.40, 0.62, 0.68]); light /= np.linalg.norm(light)

    img = np.zeros((H, W, 3), dtype=np.float32) + np.array([16, 19, 25], dtype=np.float32)
    zbuf = np.full((H, W), 1e9, dtype=np.float32)

    for quad, col in tris:
        p = quad @ R.T
        sx = (W / 2 + (p[:, 0] - center[0]) * scale)
        sy = (H / 2 + (center[1] - p[:, 1]) * scale)
        z = -p[:, 2]
        n = np.cross(quad[1] - quad[0], quad[2] - quad[0])
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        n = n / ln
        lam = abs(float(np.dot(n, light)))
        c = np.clip(col * (0.22 + 0.78 * lam), 0, 255)

        x0, x1 = int(max(0, np.floor(sx.min()))), int(min(W - 1, np.ceil(sx.max())))
        y0, y1 = int(max(0, np.floor(sy.min()))), int(min(H - 1, np.ceil(sy.max())))
        if x1 < x0 or y1 < y0:
            continue
        area = (sx[1]-sx[0])*(sy[2]-sy[0]) - (sx[2]-sx[0])*(sy[1]-sy[0])
        if abs(area) < 1e-9:
            continue
        xs = np.arange(x0, x1 + 1) + 0.5
        ys = np.arange(y0, y1 + 1) + 0.5
        X, Y = np.meshgrid(xs, ys)
        w0 = ((sx[1]-X)*(sy[2]-Y) - (sx[2]-X)*(sy[1]-Y)) / area
        w1 = ((sx[2]-X)*(sy[0]-Y) - (sx[0]-X)*(sy[2]-Y)) / area
        w2 = 1 - w0 - w1
        mask = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not mask.any():
            continue
        zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
        sub = zbuf[y0:y1+1, x0:x1+1]
        better = mask & (zz < sub)
        sub[better] = zz[better]
        img[y0:y1+1, x0:x1+1][better] = c
    return Image.fromarray(img.astype(np.uint8))

tris = []
for nm in ('Nozzle', 'Nozzle Extension', 'Beam', 'Base'):
    lathe(tris, [(p[0], p[1]) for p in SPEC[nm]['points']], SPEC[nm]['bands'])
for nm in ('Pump', 'Pump2'):
    swept(tris, SPEC[nm]['points'], np.array([150.0, 155.0, 165.0]))

img = rasterize(tris)
d = ImageDraw.Draw(img)
try:
    f1 = ImageFont.truetype(r"C:/Windows/Fonts/msyhbd.ttc", 30)
    f2 = ImageFont.truetype(r"C:/Windows/Fonts/msyh.ttc", 17)
except Exception:
    f1 = f2 = ImageFont.load_default()
d.text((34, 24), '海东青（HDQ）· 生成网格 3/4 视图（z-buffer）', font=f1, fill=(236, 239, 245))
d.text((36, 64), '由 prefab 中的真实轮廓数据旋转生成，近似材质着色', font=f2, fill=(140, 148, 165))
img.save(os.path.join(DESIGN, 'hdq_render3d.png'))
print('saved, tris=%d' % len(tris))
