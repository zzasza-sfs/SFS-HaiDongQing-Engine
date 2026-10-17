# -*- coding: utf-8 -*-
"""Parse a Unity YAML file (prefab/asset): hierarchy, components, key values, asset refs."""
import sys, os, re, glob
import yaml

PROJ = r"G:/xiangmuweizhi/Modding Toolkit"
ASSETS = PROJ + "/Assets"

# ---- Build guid -> asset path map ----
guid_map = {}
for meta in glob.glob(ASSETS + "/**/*.meta", recursive=True):
    try:
        with open(meta, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(300)
        m = re.search(r"guid:\s*([0-9a-f]{32})", head)
        if m:
            asset_path = meta[:-5]
            guid_map[m.group(1)] = os.path.relpath(asset_path, PROJ).replace("\\", "/")
    except Exception:
        pass

class UnityLoader(yaml.SafeLoader):
    pass

def unity_tag(loader, tag_suffix, node):
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node, deep=True)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    else:
        return loader.construct_scalar(node)

UnityLoader.add_multi_constructor("tag:unity3d.com,2011:", unity_tag)

def load_unity_file(path):
    """Return dict fileID -> (className, body)."""
    raw = open(path, "r", encoding="utf-8", errors="replace").read()
    blocks = re.split(r"(?m)^--- ", raw)
    docmap = {}
    for b in blocks:
        m = re.match(r"!u!(\d+) &(\d+)(?: stripped)?\s*\n(\w+):", b)
        if not m:
            continue
        cname = m.group(3)
        # body: everything after first line
        body_text = b.split("\n", 1)[1]
        try:
            body = yaml.load(body_text, Loader=UnityLoader)
            if isinstance(body, dict) and len(body) == 1 and cname in body:
                body = body[cname]
        except Exception as e:
            body = {"__parse_error__": str(e)}
        docmap[m.group(2)] = (cname, body)
    return docmap

def resolve_ref(v):
    """Resolve a {fileID, guid} dict to asset path if it has a guid."""
    if isinstance(v, dict) and v.get("guid"):
        return f"->{guid_map.get(v['guid'], v['guid'])}"
    if isinstance(v, dict) and v.get("fileID"):
        fid = v["fileID"]
        if fid == 0:
            return None
        return f"fileID:{fid}"
    return None

def dump(parsed, title, show_scripts=True, maxv=300):
    gos, trs, comps_of_go = {}, {}, {}
    for fid, (cname, body) in parsed.items():
        if not isinstance(body, dict):
            continue
        if cname == "GameObject":
            gos[fid] = body
            comps_of_go[fid] = body.get("m_Component", [])
        elif cname in ("Transform", "RectTransform"):
            trs[fid] = body
    go_of_tr, tr_of_go = {}, {}
    for fid, body in trs.items():
        g = body.get("m_GameObject", {})
        gid = str(g.get("fileID"))
        go_of_tr[fid] = gid
        tr_of_go[gid] = fid

    def go_name(gid):
        b = gos.get(gid)
        return b.get("m_Name", "?") if b else f"?{gid}"

    print("=" * 100)
    print(f"HIERARCHY: {title}")
    print("=" * 100)
    def children_of(tr_fid):
        b = trs.get(tr_fid, {})
        return [str(c.get("fileID")) for c in b.get("m_Children", [])]
    roots = []
    for fid, body in trs.items():
        f = body.get("m_Father", {})
        fv = f.get("fileID") if isinstance(f, dict) else None
        if not fv or str(fv) == "0":
            roots.append(fid)
    def walk(tr_fid, depth=0):
        gid = go_of_tr.get(tr_fid, "0")
        body = trs.get(tr_fid, {})
        pos = body.get("m_LocalPosition", {})
        scl = body.get("m_LocalScale", {})
        pos_s = f"({pos.get('x')},{pos.get('y')},{pos.get('z')})"
        scl_s = f"({scl.get('x')},{scl.get('y')},{scl.get('z')})"
        active = gos.get(gid, {}).get("m_IsActive")
        layer = gos.get(gid, {}).get("m_Layer")
        print("  " * depth + f"[{gid}] {go_name(gid)}  pos={pos_s} scale={scl_s} active={active} layer={layer}")
        for c in children_of(tr_fid):
            walk(c, depth + 1)
    for r in roots:
        walk(r)

    print()
    print("=" * 100)
    print(f"COMPONENTS: {title}")
    print("=" * 100)
    for gid in comps_of_go:
        name = go_name(gid)
        for c in comps_of_go.get(gid, []):
            cfid = str(c.get("component", {}).get("fileID"))
            if cfid not in parsed:
                continue
            cname, body = parsed[cfid]
            if not isinstance(body, dict):
                continue
            if cname == "MonoBehaviour":
                sc = body.get("m_Script", {})
                g = sc.get("guid")
                script = guid_map.get(g, g) if g else "?"
                base = os.path.basename(script) if script else "?"
                print(f"\n--- [{name}] MonoBehaviour({base}) fid={cfid}")
                for k, v in body.items():
                    if k.startswith("m_") and k not in ("m_Enabled",):
                        continue
                    if isinstance(v, dict):
                        ref = resolve_ref(v)
                        if ref:
                            print(f"    {k}: {ref}")
                        else:
                            sv = yaml.safe_dump(v, allow_unicode=True, default_flow_style=True, width=250).strip()
                            print(f"    {k}: {sv[:maxv]}")
                    elif isinstance(v, list):
                        # check if list of refs
                        sv = yaml.safe_dump(v, allow_unicode=True, default_flow_style=True, width=250).strip()
                        print(f"    {k}: {sv[:maxv]}")
                    else:
                        print(f"    {k}: {v}")
            elif cname in ("SpriteRenderer", "MeshRenderer", "MeshFilter", "SpriteMask", "BoxCollider2D", "PolygonCollider2D", "CircleCollider2D", "EdgeCollider2D", "Rigidbody2D", "Camera", "Animator", "ParticleSystem", "AudioSource", "Canvas", "CanvasRenderer", "LineRenderer"):
                print(f"\n--- [{name}] {cname} fid={cfid}")
                for k, v in body.items():
                    if k in ("m_ObjectHideFlags", "m_CorrespondingSourceObject", "m_PrefabInstance", "m_PrefabAsset", "m_GameObject", "m_Component"):
                        continue
                    if isinstance(v, dict):
                        ref = resolve_ref(v)
                        if ref:
                            print(f"    {k}: {ref}")
                        else:
                            sv = yaml.safe_dump(v, allow_unicode=True, default_flow_style=True, width=250).strip()
                            print(f"    {k}: {sv[:maxv]}")
                    elif isinstance(v, list):
                        sv = yaml.safe_dump(v, allow_unicode=True, default_flow_style=True, width=250).strip()
                        print(f"    {k}: {sv[:maxv]}")
                    else:
                        print(f"    {k}: {v}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else ASSETS + "/Resources/Parts/Engines/HaiDongQing Engine.prefab"
    title = os.path.basename(target)
    parsed = load_unity_file(target)
    print(f"# documents parsed: {len(parsed)}", file=sys.stderr)
    dump(parsed, title)
