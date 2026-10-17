# -*- coding: utf-8 -*-
"""Final two-panel render: front close-up of the repaired upper assembly + full 3/4 view."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_detail import build, raster

DESIGN = r"C:/Users/xjx20/WorkBuddy/sfs发动机/design"

tris = build()
A = raster(tris, 680, 820, yaw=-10, pitch=-9, cy=-0.30, scale=520, dist=6.0)     # 正视略仰
B = raster(tris, 700, 820, yaw=-34, pitch=-8, cy=-1.15, scale=250, dist=7.5)    # 整体 3/4

W, H = 1400, 880
img = Image.new('RGB', (W, H), (14, 17, 22))
img.paste(A, (10, 50))
img.paste(B, (700, 50))
d = ImageDraw.Draw(img)
try:
    f1 = ImageFont.truetype(r"C:/Windows/Fonts/msyhbd.ttc", 30)
    f2 = ImageFont.truetype(r"C:/Windows/Fonts/msyh.ttc", 18)
except Exception:
    f1 = f2 = ImageFont.load_default()
d.text((26, 14), '海东青引擎 · 接口修正后（肘管两端插入实体、台阶圆角化）', font=f1, fill=(236, 239, 245))
d.text((30, 840), '左：上方组件正视图（仰视 9°）　右：整体 3/4 视图', font=f2, fill=(140, 148, 165))
d.line([(697, 50), (697, 870)], fill=(44, 50, 60), width=1)
img.save(os.path.join(DESIGN, 'hdq_fix_views.png'))
print('saved hdq_fix_views.png')
