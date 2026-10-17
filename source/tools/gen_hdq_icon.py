# -*- coding: utf-8 -*-
"""HDQ pack icon (256x256 RGBA), same visual language as the other parts."""
import json, os
from PIL import Image, ImageDraw

TOOLS = r"C:/Users/xjx20/WorkBuddy/sfs发动机/tools"
DESIGN = r"C:/Users/xjx20/WorkBuddy/sfs发动机/design"
PROJ = r"G:/xiangmuweizhi/Modding Toolkit"
SPEC = json.load(open(os.path.join(TOOLS, 'hdq_spec.json'), encoding='utf-8'))

ICON = 256
img = Image.new('RGBA', (ICON, ICON), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([6, 6, ICON-6, ICON-6], radius=40, fill=(24, 28, 38, 255),
                    outline=(70, 78, 96, 255), width=3)

sc, ox, oy = 78.0, 128, 24

def poly(pts, fill, outline):
    d.polygon([(ox + x*sc, oy - y*sc) for (x, y) in pts], fill=fill, outline=outline)

def mirrored(pts):
    return [(r, y) for (y, r) in pts] + [(-r, y) for (y, r) in reversed(pts)]

OUT = (58, 62, 70, 255)
# body (mid grey), extension (lighter), plate (light), beam (dark)
poly(mirrored([(p[0], p[1]) for p in SPEC['Nozzle']['points']]), (104, 108, 118, 255), OUT)
poly(mirrored([(p[0], p[1]) for p in SPEC['Nozzle Extension']['points']]), (124, 128, 138, 255), OUT)
poly(mirrored([(p[0], p[1]) for p in SPEC['Beam']['points']]), (74, 78, 86, 255), OUT)
poly(mirrored([(p[0], p[1]) for p in SPEC['Base']['points']]), (150, 154, 164, 255), OUT)

# side ducts
for nm in ('Pump', 'Pump2'):
    pts = SPEC[nm]['points']
    outer = [(p[0] + p[2]/2, p[1] + p[3]/2) for p in pts]
    inner = [(p[0] - p[2]/2, p[1] - p[3]/2) for p in pts]
    d.polygon([(ox + x*sc, oy - y*sc) for (x, y) in outer + list(reversed(inner))],
              fill=(132, 136, 146, 255), outline=OUT)

# orange accents: manifold ring, throat ring, lip edge
def band(y0, y1, col):
    import math
    def r_at(y):
        pts = [(p[0], p[1]) for p in SPEC['Nozzle']['points']]
        for i in range(1, len(pts)):
            a, b = pts[i-1], pts[i]
            if min(a[0], b[0]) - 1e-9 <= y <= max(a[0], b[0]) + 1e-9:
                if abs(b[0]-a[0]) < 1e-9:
                    return max(a[1], b[1])
                return a[1] + (y - a[0]) / (b[0] - a[0]) * (b[1] - a[1])
        return pts[-1][1]
    r0, r1 = r_at(y0), r_at(y1)
    d.polygon([(ox + r0*sc, oy - y0*sc), (ox + r1*sc, oy - y1*sc),
               (ox - r1*sc, oy - y1*sc), (ox - r0*sc, oy - y0*sc)], fill=col)

OR = (232, 150, 62, 255)
band(-0.4375, -0.3375, OR)        # manifold
band(-1.0875, -0.9875, OR)        # throat ring
# lip line
d.line([(ox - 0.5667*sc, oy + 2.7875*sc), (ox + 0.5667*sc, oy + 2.7875*sc)], fill=OR, width=3)

for p in (os.path.join(DESIGN, 'M1_Icon.png'),
          os.path.join(PROJ, 'Assets/Textures/Icons/M1_Icon.png')):
    img.save(p)
    print('saved', p)
