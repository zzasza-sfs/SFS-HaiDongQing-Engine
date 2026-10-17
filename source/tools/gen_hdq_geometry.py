# -*- coding: utf-8 -*-
"""HDQ geometry + band spec generator.

Input: the 2D design sheet's main view (1 px = 6.25 mm)
  * widths are re-based to the mating flange (Φ1.000, the same flange the part ships with):
        world_radius = px_half * (0.50 / 152) = px_half * 0.00328947
  * heights keep the design's 1:1 metres, anchored at the mating plane
        world_y = +0.1125 - (py - 76) * 0.00625      => total length exactly 2.90 m
Outputs
  * hdq_spec.json     - profiles, bands, cumulative heights
  * hdq_arrays.cs     - the C# arrays pasted into the builder
  * hdq_preview.png   - 2D check render
"""
import json, math, os

DESIGN = r"C:/Users/xjx20/WorkBuddy/sfs发动机/design"
TOOLS = r"C:/Users/xjx20/WorkBuddy/sfs发动机/tools"

CX, TOP, MM, Y0 = 340.0, 76.0, 0.00625, 0.1125
W = 0.50 / 152.0          # 法兰锚定（1.00 宽）时的 px->半径
KB = 0.84                 # 机体宽度系数：把设计图的身形收进家族实机比例（出口 ≈ 1.15）

def R(px):   return px * W * KB          # 机体（设计图比例 x 家族系数）
def Y(py):   return Y0 - (py - TOP) * MM
def RX(px):  return abs(CX - px) * W * KB

def cubic(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
                    u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]))
    return out

def quad(p0, p1, p2, n):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
                    u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))
    return out

# ---------------------------------------------------------------- palette
ORANGE = (0.91, 0.585, 0.235)
C = dict(plate_hi=0.90, plate_lo=0.45, beam=0.42, neck=1.00,
         step_a=0.50, step_b=0.42, chamber=0.62, bell=0.55,
         collar=0.42, sleeve=0.85, skirt=1.00, lip=0.85, elbow=0.55)

def g(v):  # grey
    return (v, v, v)

# texture presets: (colorTexture, shapeTexture)
TEX = dict(
    plate_hi=('Assets/Resources/Part Textures/Pattern Textures/Metal.asset',
              'Assets/Resources/Part Textures/Shape Textures/Edges Faces Bottom.asset'),
    plate_lo=('Assets/Resources/Part Textures/Pattern Textures/Color_White.asset',
              'Assets/Resources/Part Textures/Shape Textures/Edges Faces.asset'),
    machined=('Assets/Resources/Part Textures/Pattern Textures/Metal.asset',
              'Assets/Resources/Part Textures/Shape Textures/Flat Faces.asset'),
    smooth=('Assets/Resources/Part Textures/Pattern Textures/Metal_4.asset',
            'Assets/Resources/Part Textures/Shape Textures/Flat Smooth.asset'),
    orange=('Assets/Resources/Part Textures/Pattern Textures/Color_White.asset',
            'Assets/Resources/Part Textures/Shape Textures/Flat Faces.asset'),
)

# ---------------------------------------------------------------- profiles
# (y, radius); ordered bottom -> top (first point = the mesh's "bottom" edge)
bell_px = cubic((292, 268), (250, 290), (210, 330), (206, 383), 10)
bell = [(Y(py), RX(px)) for (px, py) in bell_px]           # top -> bottom
bell.reverse()                                             # bottom -> top

nozzle = []
nozzle += bell                                              # 0..10  bell, bottom -> top
# v2: 上方过渡改为带圆角/倒角的连续轮廓（原 90° 台阶过生硬）
nozzle += [(-1.0775, 0.1409), (-0.9975, 0.1409), (-0.9875, 0.1326)]   # 11..13 喉部识别环（倒角）
nozzle += [(-0.9500, 0.1386), (-0.9000, 0.1446), (-0.8500, 0.1455),   # 14..18 燃烧室鼓形（平滑）
           (-0.8000, 0.1419), (-0.7625, 0.1361)]
nozzle += [(-0.7375, 0.1326)]                                          # 19 腰
nozzle += [(-0.7300, 0.1600), (-0.7180, 0.1880), (-0.7000, 0.2045),    # 20..23 三级泵（底部圆角）
           (-0.6400, 0.2045)]
nozzle += [(-0.6320, 0.2140), (-0.6250, 0.2210), (-0.5350, 0.2210)]    # 24..26 二级
nozzle += [(-0.5250, 0.1980), (-0.5180, 0.1851), (-0.4825, 0.1851)]    # 27..29 一级
# v3: 集合环加高到 0.19，使 0.1243 的肘管径向插入后四周仍有余量（避免与倒角相切）
nozzle += [(-0.4745, 0.2150), (-0.4625, 0.2432), (-0.3125, 0.2432),    # 30..32 集合环
           (-0.3025, 0.2100), (-0.2925, 0.1768)]                       # 33..34 上部圆角
nozzle += [(-0.0875, 0.1768)]                                          # 35 颈部

skirt_px = quad((196, 404), (160, 470), (135, 530), 6)
skirt = [(Y(py), RX(px)) for (px, py) in skirt_px]
skirt.reverse()                                             # bottom -2.725 -> top -1.9375

def bell_at(y):
    """interpolated bell radius at world y"""
    for i in range(1, len(bell)):
        y0, r0 = bell[i-1]; y1, r1 = bell[i]
        if y0 - 1e-9 <= y <= y1 + 1e-9:
            return r0 + (y - y0) / (y1 - y0) * (r1 - r0)
    return bell[0][1] if y < bell[0][0] else bell[-1][1]

# v3: every consecutive pair must differ in y — PipeMesh drops zero-height quads
# (that is what left the beam bottom / elbow mouth open). Steps therefore get a 2-3 mm slant.
ext = [(Y(540), R(208) - 0.0080),                       # 0  lip bottom
       (Y(536), R(208)),                                # 1  lip widest (rolled)
       (Y(530), R(205) + 0.0040),                       # 2  lip top
       (Y(529.5), R(205) + 0.0040 - 0.0128)]            # 3  step in to the skirt
ext += skirt[1:]                                        # 4..9  skirt (skip the -2.725 sample)
ext += [(Y(403.6), R(144) + 0.0050),                    # 10 collar bottom (proud)
        (Y(383), R(134) + 0.0050),                      # 11 collar top
        (Y(382.6), R(134) + 0.0035),                    # 12 step in to the sleeve
        (Y(358), bell_at(Y(358)) + 0.0035)]             # 13 sleeve top (proud of the bell)

def elbow_pts(d, mirror=False):
    """side duct: 板下 -> 内弯 -> 水平插入集合环（J 形肘管）

    v2：末端改为水平径向插入并深入集合环内部（不再收窄成尖口），
    顶部插进边梁体内；两端开口都被实体遮住，避免"断裂"观感。
    """
    pts = [(0.3900,  0.0550), (0.3900, -0.0700), (0.3890, -0.1500),
           (0.3840, -0.2250), (0.3700, -0.2900), (0.3450, -0.3450),
           (0.3100, -0.3780), (0.2680, -0.3905), (0.2250, -0.3925),
           (0.1650, -0.3985)]
    wids = [d] * len(pts)
    out = []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            tx, ty = pts[1][0] - x, pts[1][1] - y
        elif i == len(pts) - 1:
            tx, ty = x - pts[i-1][0], y - pts[i-1][1]
        else:
            tx, ty = pts[i+1][0] - pts[i-1][0], pts[i+1][1] - pts[i-1][1]
        L = math.hypot(tx, ty)
        nx, ny = -ty / L, tx / L
        if i == 0:
            nx, ny = 1.0, 0.0          # 顶端水平切面（藏在边梁内）
        s = -1.0 if mirror else 1.0
        out.append((s * x, y, s * nx * wids[i], ny * wids[i]))
    return out

base = [(-0.0250, 0.4870), (-0.0100, 0.5000), (0.0000, 0.5000),
        (0.0500, 0.5000), (0.1125, 0.4750)]
# v2: 边梁做成"有底面的实心环"，堵住壳体空腔（原先从下方能看穿，形成断口感）
beam = [(-0.0250, 0.5164), (-0.0875, 0.5164), (-0.1000, 0.0020)]

# ---------------------------------------------------------------- bands
# (first point index, last point index, tint, texture key)
BANDS = {
    'Base': [
        (0, 2, g(C['plate_lo']), 'plate_lo'),
        (2, 4, g(C['plate_hi']), 'plate_hi'),
    ],
    'Beam': [
        (0, 2, g(C['beam']), 'machined'),
    ],
    'Nozzle': [
        (0, 10, g(C['bell']), 'smooth'),
        (10, 13, ORANGE, 'orange'),
        (13, 19, g(C['chamber']), 'machined'),
        (19, 23, g(C['step_a']), 'machined'),
        (23, 26, g(C['step_b']), 'machined'),
        (26, 29, g(C['step_a']), 'machined'),
        (29, 34, ORANGE, 'orange'),
        (34, 35, g(C['neck']), 'smooth'),
    ],
    'Nozzle Extension': [
        (0, 3, g(C['lip']), 'machined'),
        (3, len(ext) - 4, g(C['skirt']), 'smooth'),
        (len(ext) - 4, len(ext) - 2, g(C['collar']), 'machined'),
        (len(ext) - 2, len(ext) - 1, g(C['sleeve']), 'smooth'),
    ],
    'Pump': [(0, 9, g(C['elbow']), 'smooth')],
    'Pump2': [(0, 9, g(C['elbow']), 'smooth')],
}

D_ELBOW = 45 * W * KB                # 设计图肘管外径 45 px（全宽）
PROFILES = {'Base': base, 'Beam': beam, 'Nozzle': nozzle,
            'Nozzle Extension': ext,
            'Pump': elbow_pts(D_ELBOW, False), 'Pump2': elbow_pts(D_ELBOW, True)}

def _axis(p):
    """(y, radius) for 2-component points, (x, y) for 4-component ones"""
    return (p[1], p[2]) if len(p) == 4 else (p[0], p[1])

def cum(prof):
    """arc length along the profile"""
    out = [0.0]
    for i in range(1, len(prof)):
        a, b = _axis(prof[i-1]), _axis(prof[i])
        out.append(out[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return out

def dy(prof):
    """cumulative |Δy| along the profile — this is what SFS actually uses for band heights
    (verified empirically: assets/Scripts is reference only, the runtime DLL differs)"""
    out = [0.0]
    for i in range(1, len(prof)):
        a, b = _axis(prof[i-1]), _axis(prof[i])
        out.append(out[-1] + abs(b[0] - a[0]))      # a[0] = y for both layouts
    return out

def spec():
    res = {}
    for name, prof in PROFILES.items():
        c = dy(prof)          # band heights are measured in Δy, not arc length
        pts = [[round(p[0], 5), round(p[1], 5)] for p in prof] if len(prof[0]) == 2 else \
              [[round(v, 5) for v in p] for p in prof]
        bands = []
        for (i0, i1, tint, tk) in BANDS[name]:
            bands.append(dict(h=round(c[i1], 4), tint=[round(t, 4) for t in tint], tex=tk))
        res[name] = dict(points=pts, bands=bands, total=round(c[-1], 4))
    return res

# ---------------------------------------------------------------- C# emit
def cs_float(v):
    s = ('%.5f' % v).rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'

def emit_cs(S):
    # local = world / transformScale  (Base keeps the SE's 0.5 scale; all new objects use 1)
    SCL = {'Base': 2.0, 'Beam': 1.0, 'Nozzle': 1.0, 'Nozzle Extension': 1.0,
           'Pump': 1.0, 'Pump2': 1.0}
    L = []
    A = L.append
    A('    // ---- generated by tools/gen_hdq_geometry.py (design v1, 2026-10-17) ----')
    for name in ('Base', 'Beam', 'Nozzle', 'Nozzle Extension', 'Pump', 'Pump2'):
        s = S[name]
        ident = name.replace(' ', '')
        sc = SCL[name]
        A('    static readonly Vector4[] %sPoints =' % ident)
        A('    {')
        for p in s['points']:
            if len(p) == 2:
                A('        new Vector4(0f, %sf, %sf, 0f),' % (cs_float(p[0] * sc), cs_float(p[1] * 2 * sc)))
            else:
                A('        new Vector4(%sf, %sf, %sf, %sf),' % tuple(cs_float(v) for v in p))
        A('    };')
        A('    static readonly float[] %sColorHeights = { %s };' % (ident, ', '.join('%sf' % cs_float(b['h'] * sc) for b in s['bands'])))
        A('    static readonly Color[] %sColorValues =' % ident)
        A('    {')
        for b in s['bands']:
            A('        new Color(%sf, %sf, %sf, 1f),' % tuple(cs_float(v) for v in b['tint']))
        A('    };')
        A('')
    return '\n'.join(L)

if __name__ == '__main__':
    S = spec()
    with open(os.path.join(TOOLS, 'hdq_spec.json'), 'w', encoding='utf-8') as f:
        json.dump(S, f, indent=1, ensure_ascii=False)
    with open(os.path.join(TOOLS, 'hdq_arrays.cs'), 'w', encoding='utf-8') as f:
        f.write(emit_cs(S))
    for k, v in S.items():
        print('%-18s pts=%2d bands=%d total_len=%.4f' % (k, len(v['points']), len(v['bands']), v['total']))
    print('overall: y %.4f .. 0.1125  -> length %.4f' % (
        min(p[0] for p in S['Nozzle Extension']['points']),
        0.1125 - min(p[0] for p in S['Nozzle Extension']['points'])))
    print('max radius %.4f (dia %.4f)' % (max(p[1] for p in S['Nozzle Extension']['points']),
                                          max(p[1] for p in S['Nozzle Extension']['points']) * 2))
    print('wrote hdq_spec.json / hdq_arrays.cs')
