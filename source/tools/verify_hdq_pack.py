# -*- coding: utf-8 -*-
"""Verify the built 海东青引擎.pack: decode -> UnityFS -> inspect assets and key values."""
import json, base64, io, os, sys, tempfile
import UnityPy

PACK = sys.argv[1] if len(sys.argv) > 1 else r"G:/xiangmuweizhi/Modding Toolkit/Assets/ModBuilder/海东青引擎.pack"
data = json.load(open(PACK, encoding='utf-8'))
print('pack keys:', list(data.keys()))
for k, v in data.items():
    if not v: 
        print('  %-12s (empty)' % k); continue
    raw = base64.b64decode(v)
    print('  %-12s %6d bytes  magic=%r' % (k, len(raw), raw[:8]))

raw = base64.b64decode(data['WindowsBuild'])
tmp = os.path.join(tempfile.gettempdir(), 'hdq_win.bundle')
open(tmp, 'wb').write(raw)

env = UnityPy.load(tmp)
print('\nobjects:')
kinds = {}
for obj in env.objects:
    kinds[obj.type.name] = kinds.get(obj.type.name, 0) + 1
print(' ', kinds)

from UnityPy.classes import MonoBehaviour, Texture2D, AudioClip

def read_typetree(obj):
    try:
        return obj.read_typetree()
    except Exception as e:
        return None

print('\n--- MonoBehaviours of interest')
for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    tt = read_typetree(obj)
    if not tt:
        continue
    name = tt.get('m_Name') or ''
    keys = set(tt.keys())
    if 'DisplayName' in keys:
        print('PackData: DisplayName=%r Version=%r Description=%r Author=%r ShowIcon=%s Icon=%s' % (
            tt.get('DisplayName'), tt.get('Version'), tt.get('Description'), tt.get('Author'),
            tt.get('ShowIcon'), bool(tt.get('Icon', {}).get('m_PathID')) if isinstance(tt.get('Icon'), dict) else '?'))
    if 'thrust' in keys:
        def val(d):
            return d.get('input') if isinstance(d, dict) else d
        print('EngineModule: thrust=%s ISP=%s thrustPos.y=%s' % (
            val(tt.get('thrust')), val(tt.get('ISP')),
            val(tt.get('thrustPosition', {}).get('y')) if isinstance(tt.get('thrustPosition'), dict) else '?'))
    if 'mass' in keys and 'variants' in keys:
        def val(d):
            return d.get('input') if isinstance(d, dict) else d
        dn = tt.get('displayName')
        print('Part: name=%r desc=%r mass=%s com.y=%s cost=%s' % (
            dn.get('TranslatableName') if isinstance(dn, dict) else dn,
            (tt.get('description') or {}).get('TranslatableName') if isinstance(tt.get('description'), dict) else '',
            val(tt.get('mass')),
            val((tt.get('centerOfMass') or {}).get('y')),
            tt.get('variants', [{}])[0].get('variants', [{}])[0].get('cost') if tt.get('variants') else '?'))
    if 'composedShape' in keys:
        pts = tt['composedShape'].get('points', [])
        def f(d):
            return float(d.get('input')) if isinstance(d, dict) and d.get('input') not in (None, '') else 0.0
        ys = [f(p['position']['y']) for p in pts]
        rs = [f(p['width']['x']) for p in pts]
        print('CustomPipe: pts=%d y %.4f..%.4f  maxWidth %.4f' % (len(pts), min(ys), max(ys), max(abs(r) for r in rs)))

print('\n--- textures')
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        tt = read_typetree(obj)
        if tt:
            print('  Texture2D %-24s %sx%s' % (tt.get('m_Name'), tt.get('m_Width'), tt.get('m_Height')))
    if obj.type.name == 'AudioClip':
        tt = read_typetree(obj)
        if tt:
            print('  AudioClip %s' % tt.get('m_Name'))
