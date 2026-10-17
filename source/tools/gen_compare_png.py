# -*- coding: utf-8 -*-
# NOTE: 本脚本产出的文档含与 青鹰SE Pro（112 kN 级）的横向对比；该机型不随本仓库分发。
"""Standalone PNG of the SE Pro vs HaiDongQing performance comparison (same data as the whitepaper)."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = r"C:/Users/xjx20/WorkBuddy/sfs发动机/design"
W, H = 1280, 860
BG = (14, 17, 23)
PAN = (21, 26, 34)
LINE = (36, 43, 54)
TXT = (214, 218, 226)
SUB = (139, 149, 166)
SIL = (159, 176, 198)
ACC = (232, 150, 60)
GOOD = (127, 192, 138)
BAD = (201, 123, 90)

def font(sz, bold=False):
    for p in ([r"C:/Windows/Fonts/msyhbd.ttc", r"C:/Windows/Fonts/msyh.ttc"] if bold
              else [r"C:/Windows/Fonts/msyh.ttc"]):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()

SE = dict(thrust=100, isp=290, mass=3.5, cost=45)
PRO = dict(thrust=112, isp=311, mass=3.8, twr=112 / (3.8 * 9.81), cost=70, gimbal=7, length=2.5923, dia=1.0005)
HDQ = dict(thrust=150, isp=318, mass=5.0, twr=150 / (5.0 * 9.81), cost=95, gimbal=8, length=2.900, dia=1.1495)

rows = [
    ('推力 (kN)',        PRO['thrust'], HDQ['thrust'], '%.0f', 'up'),
    ('真空比冲 (s)',      PRO['isp'],    HDQ['isp'],    '%.0f', 'up'),
    ('推重比',           PRO['twr'], HDQ['twr'], '%.2f', 'up'),
    ('万向摆角 (±°)',     PRO['gimbal'], HDQ['gimbal'], '%.0f', 'up'),
    ('干重 (t)',         PRO['mass'],   HDQ['mass'],   '%.2f', 'down'),
    ('造价 (生涯)',       PRO['cost'],   HDQ['cost'],   '%.0f', 'down'),
    ('总长 (m)',         PRO['length'], HDQ['length'], '%.2f', 'down'),
    ('出口直径 (m)',      PRO['dia'],    HDQ['dia'],    '%.2f', 'up'),
]

img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)

# header
d.text((48, 40), '青鹰SE Pro  vs  海东青  ·  关键性能对比', font=font(32, True), fill=(238, 241, 246))
d.text((50, 86), '数据取自现役 prefab 与 PackData；百分比为海东青相对青鹰SE Pro 的变化', font=font(16), fill=SUB)

# legend
lx, ly = 50, 126
d.rounded_rectangle([lx, ly, lx + 14, ly + 14], radius=3, fill=SIL)
d.text((lx + 22, ly - 3), '青鹰SE Pro', font=font(16), fill=SIL)
d.rounded_rectangle([lx + 150, ly, lx + 164, ly + 14], radius=3, fill=ACC)
d.text((lx + 172, ly - 3), '海东青', font=font(16), fill=ACC)
d.text((W - 50, ly - 3), '绿色 = 更优，红色 = 代价', font=font(14), fill=(110, 120, 136), anchor='ra')

# rows
top, rowh = 176, 76
label_x, bar_x, bar_w = 62, 262, 640
for i, (label, a, b, fmt, better) in enumerate(rows):
    y = top + i * rowh
    if i % 2 == 0:
        d.rounded_rectangle([40, y - 6, W - 40, y + rowh - 14], radius=8, fill=PAN)
    d.text((label_x, y + 24), label, font=font(17), fill=(170, 179, 193))
    m = max(a, b)
    wa = max(3, int(bar_w * a / m))
    wb = max(3, int(bar_w * b / m))
    # Pro bar
    d.rounded_rectangle([bar_x, y + 6, bar_x + wa, y + 26], radius=4, fill=SIL)
    d.text((bar_x + wa + 12, y + 8), fmt % a, font=font(16), fill=(206, 213, 224))
    # HDQ bar
    d.rounded_rectangle([bar_x, y + 34, bar_x + wb, y + 54], radius=4, fill=ACC)
    d.text((bar_x + wb + 12, y + 36), fmt % b, font=font(16), fill=(243, 196, 139))
    # delta
    pct = (b - a) / a * 100.0
    col = GOOD if (pct > 0) == (better == 'up') else BAD
    d.text((W - 62, y + 26), ('%+.1f%%' % pct), font=font(19, True), fill=col, anchor='ra')

# footer insight
fy = H - 86
d.line([(50, fy - 18), (W - 50, fy - 18)], fill=LINE)
d.text((50, fy), '推力 +34%、干重 +32%、造价 +36%：几乎是一次线性放大；'
                 '单位推力造价 0.625 → 0.633，边际成本基本持平，而比冲 +2.3%、摆角 +14% 属于净增益。',
       font=font(15), fill=(150, 160, 175))
d.text((50, fy + 30), '青鹰SEPro & 海东青 产品白皮书 · 配套对比图 · zzasza · 2026-10-17',
       font=font(13), fill=(96, 106, 122))

img.save(os.path.join(OUT, '两款发动机_性能对比图.png'))
print('saved 两款发动机_性能对比图.png')
