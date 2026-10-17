// Ground truth: generate the real part's PipeMeshes and dump vertex colours per height.
// Batch: Unity.exe -batchmode -nographics -projectPath <proj> -executeMethod PartColorProbe.Run -quit
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using SFS.Parts.Modules;
using UnityEditor;
using UnityEngine;

public static class PartColorProbe
{
    const string PrefabPath = "Assets/Resources/Parts/Engines/HaiDongQing Engine.prefab";

    public static void Run()
    {
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
        if (prefab == null) { Debug.LogError("[CProbe] prefab missing"); return; }

        var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        try
        {
            foreach (var mesh in inst.GetComponentsInChildren<PipeMesh>(true))
            {
                try { mesh.GenerateMesh(); }
                catch (Exception e)
                {
                    var ie = e.InnerException ?? e;
                    Debug.LogWarning("[CProbe] " + mesh.name + " GenerateMesh failed: " + ie.GetType().Name + " " + ie.Message);
                    continue;
                }

                var mf = mesh.GetComponent<MeshFilter>();
                var m = mf != null ? mf.sharedMesh : null;
                if (m == null || m.colors.Length == 0) { Debug.LogWarning("[CProbe] " + mesh.name + ": no mesh/colors"); continue; }

                var verts = m.vertices;
                var cols = m.colors;
                // exact: unique (y, colour) pairs, sorted by y
                var rows = new List<string>();
                var seen = new HashSet<string>();
                for (int i = 0; i < verts.Length; i++)
                {
                    string key = verts[i].y.ToString("F3") + "|" + cols[i].r.ToString("F2") + "," + cols[i].g.ToString("F2");
                    if (!seen.Add(key)) continue;
                    rows.Add(string.Format("y={0,7:F3} c=({1:F2},{2:F2},{3:F2})", verts[i].y, cols[i].r, cols[i].g, cols[i].b));
                }
                rows.Sort((x, y) => string.CompareOrdinal(x, y));
                var sb = new System.Text.StringBuilder();
                sb.Append("[CProbe] ").Append(mesh.name).Append(" verts=").Append(verts.Length).Append("\n");
                foreach (var r in rows) sb.Append("      ").Append(r).Append("\n");
                Debug.Log(sb.ToString());
            }
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(inst);
        }
        Debug.Log("[CProbe] done");
    }
}
