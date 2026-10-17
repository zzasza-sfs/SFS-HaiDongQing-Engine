# -*- coding: utf-8 -*-
"""Dump full hierarchy (with parents), transforms and key component fields of a prefab."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_prefab as P

TARGET = sys.argv[1]
SHOW_ALL = '--all' in sys.argv

docs = P.load_unity_file(TARGET)
gos = {fid: b for fid, (cn, b) in docs.items() if cn == 'GameObject'}

# transform fid -> gameobject fid
tr2go = {}
for fid, b in docs.items():
    if b[0] == 'Transform':
        tr2go[fid] = str(b[1].get('m_GameObject', {}).get('fileID'))

children = {}
gofather = {}
for fid, b in gos.items():
    father = None
    for entry in b.get('m_Component') or []:
        cfid = str(entry.get('component', {}).get('fileID'))
        if cfid in docs and docs[cfid][0] == 'Transform':
            f = docs[cfid][1].get('m_Father', {}).get('fileID')
            father = tr2go.get(str(f)) if f else None
    gofather[fid] = father
    children.setdefault(father, []).append(fid)


def tr_of(gofid):
    for entry in gos[gofid].get('m_Component') or []:
        cfid = str(entry.get('component', {}).get('fileID'))
        if cfid in docs and docs[cfid][0] == 'Transform':
            return docs[cfid][1]
    return None


def comps(gofid):
    out = []
    for entry in gos[gofid].get('m_Component') or []:
        cfid = str(entry.get('component', {}).get('fileID'))
        if cfid in docs:
            out.append((docs[cfid][0], docs[cfid][1]))
    return out


def script_name(cb):
    g = cb.get('m_Script', {}).get('guid')
    p = P.guid_map.get(g, '')
    return os.path.basename(p).replace('.cs', '') if p else '?'


roots = [fid for fid in gos if gofather[fid] is None]
print('# docs=%d, gameobjects=%d, roots=%d' % (len(docs), len(gos), len(roots)))

SKIP = ('m_ObjectHideFlags', 'm_CorrespondingSourceObject', 'm_PrefabInstance',
        'm_PrefabAsset', 'm_GameObject', 'm_Enabled', 'm_EditorHideFlags',
        'm_Script', 'm_Name', 'm_EditorClassIdentifier', 'm_Component', 'm_LocalRotation')


def fmt(v, n=700):
    if isinstance(v, dict) and 'fileID' in v and len(v) == 1:
        return '@%s' % v['fileID']
    sv = P.yaml.safe_dump(v, allow_unicode=True, default_flow_style=True, width=400).strip()
    sv = sv.replace('\n', ' ')
    return sv[:n]


def show(fid, depth):
    b = gos[fid]
    t = tr_of(fid)
    print('%s%s  pos=(%s,%s,%s) scale=(%s,%s,%s) active=%s layer=%s' % (
        '  ' * depth, b.get('m_Name'),
        t.get('m_LocalPosition', {}).get('x'), t.get('m_LocalPosition', {}).get('y'),
        t.get('m_LocalPosition', {}).get('z'),
        t.get('m_LocalScale', {}).get('x'), t.get('m_LocalScale', {}).get('y'),
        t.get('m_LocalScale', {}).get('z'),
        b.get('m_IsActive'), b.get('m_Layer')))
    for cn, cb in comps(fid):
        if cn == 'Transform':
            continue
        if cn == 'MonoBehaviour':
            label = script_name(cb)
            items = ['%s=%s' % (k, fmt(v)) for k, v in cb.items() if k not in SKIP and not k.startswith('m_')]
            print('%s[%s] %s' % ('  ' * depth, label, '  '.join(items)))
        elif SHOW_ALL or cn in ('BoxCollider2D', 'PolygonCollider2D', 'MeshRenderer'):
            items = ['%s=%s' % (k, fmt(v, 200)) for k, v in cb.items() if k not in SKIP and not k.startswith('m_')]
            print('%s[%s] %s' % ('  ' * depth, cn, '  '.join(items)))
    for c in children.get(fid, []):
        show(c, depth + 1)


for r in roots:
    show(r, 0)
