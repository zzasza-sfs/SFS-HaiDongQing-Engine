// Probe: reverse-engineer how PipeMesh interprets the colour-layer `height`
// (metric + whether it marks the start or the end of a band).
// Batch: Unity.exe -batchmode -nographics -projectPath <proj> -executeMethod PipeMeshProbe.Run -quit
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Globalization;
using SFS.Parts;
using SFS.Parts.Modules;
using SFS.Variables;
using UnityEditor;
using UnityEngine;

public static class PipeMeshProbe
{
    public static void Run()
    {
        var meshType = typeof(PipeMesh);
        Debug.Log("[Probe] === PipeMesh members ===");
        foreach (var f in meshType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            Debug.Log("[Probe] field " + f.FieldType.Name + " " + f.Name);
        foreach (var m in meshType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            Debug.Log("[Probe] method " + m.ReturnType.Name + " " + m.Name + "(" + string.Join(",", m.GetParameters().Select(p => p.ParameterType.Name)) + ")");

        // ---- build a controlled pipe: a straight cylinder y = -3 .. 0, radius 0.5
        var go = new GameObject("probe");
        var vars = go.AddComponent<VariablesModule>();
        var pipe = go.AddComponent<CustomPipe>();
        var mesh = go.AddComponent<PipeMesh>();
        mesh.pipeData = pipe;
        var mf0 = go.AddComponent<MeshFilter>();
        mf0.sharedMesh = new Mesh();
        var mr = go.AddComponent<MeshRenderer>();
        mr.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Part 1.mat");

        // profile: 4 points, y = -3, -1, 1, 3  (total y span 6, arc 6)
        var pts = new[]
        {
            new Vector4(0f, -3f, 1.0f, 0f),
            new Vector4(0f, -1f, 1.0f, 0f),
            new Vector4(0f,  1f, 1.0f, 0f),
            new Vector4(0f,  3f, 1.0f, 0f),
        };
        var so = new SerializedObject(pipe);
        var arr = so.FindProperty("composedShape.points");
        arr.arraySize = pts.Length;
        for (int i = 0; i < pts.Length; i++)
        {
            var e = arr.GetArrayElementAtIndex(i);
            e.FindPropertyRelative("variables").objectReferenceValue = vars;
            e.FindPropertyRelative("position.variables").objectReferenceValue = vars;
            e.FindPropertyRelative("position.x.variables").objectReferenceValue = vars;
            e.FindPropertyRelative("position.y.variables").objectReferenceValue = vars;
            e.FindPropertyRelative("position.x.input").stringValue = "0";
            e.FindPropertyRelative("position.y.input").stringValue = pts[i].y.ToString(CultureInfo.InvariantCulture);
            e.FindPropertyRelative("width.variables").objectReferenceValue = vars;
            e.FindPropertyRelative("width.x.variables").objectReferenceValue = vars;
            e.FindPropertyRelative("width.y.variables").objectReferenceValue = vars;
            e.FindPropertyRelative("width.x.input").stringValue = pts[i].z.ToString(CultureInfo.InvariantCulture);
            e.FindPropertyRelative("width.y.input").stringValue = "0";
        }
        so.ApplyModifiedPropertiesWithoutUndo();

        // three bands at heights 2 / 4 / 6: red, green, blue
        var soM = new SerializedObject(mesh);
        soM.FindProperty("colors.mode").enumValueIndex = 1;
        var carr = soM.FindProperty("colors.colors");
        carr.arraySize = 3;
        var cols = new[] { Color.red, Color.green, Color.blue };
        var hs = new[] { 2f, 4f, 6f };
        for (int i = 0; i < 3; i++)
        {
            var e = carr.GetArrayElementAtIndex(i);
            e.FindPropertyRelative("color.type").enumValueIndex = 0;
            e.FindPropertyRelative("color.colorBasic").colorValue = cols[i];
            e.FindPropertyRelative("height").floatValue = hs[i];
        }
        // textures are mandatory: mode Multiple, one band covering the whole profile
        soM.FindProperty("textures.textureMode").enumValueIndex = 1;
        var tarr = soM.FindProperty("textures.textures");
        tarr.arraySize = 1;
        var te = tarr.GetArrayElementAtIndex(0);
        te.FindPropertyRelative("texture.colorTexture").objectReferenceValue =
            AssetDatabase.LoadAssetAtPath<ColorTexture>("Assets/Resources/Part Textures/Pattern Textures/Color_White.asset");
        te.FindPropertyRelative("texture.shapeTexture").objectReferenceValue =
            AssetDatabase.LoadAssetAtPath<ShapeTexture>("Assets/Resources/Part Textures/Shape Textures/Flat Faces.asset");
        te.FindPropertyRelative("height").floatValue = 6f;

        var baseCol = soM.FindProperty("colors.color.colorBasic");
        baseCol.colorValue = Color.magenta;     // so 0..h1 shows up clearly
        soM.ApplyModifiedPropertiesWithoutUndo();

        // generate the mesh
        var gen = meshType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
                          .FirstOrDefault(m => m.GetParameters().Length == 0 &&
                                               (m.Name.ToLower().Contains("generat") || m.Name.ToLower().Contains("build") ||
                                                m.Name.ToLower().Contains("update") || m.Name.ToLower().Contains("refresh")));
        Debug.Log("[Probe] generation method: " + (gen == null ? "not found" : gen.Name));
        if (gen != null)
        {
            try { gen.Invoke(mesh, null); }
            catch (Exception e)
            {
                var ie = e.InnerException ?? e;
                Debug.LogWarning("[Probe] invoke failed: " + ie.GetType().Name + ": " + ie.Message);
                Debug.LogWarning("[Probe] stack: " + ie.StackTrace);
            }
        }

        var mf = go.GetComponent<MeshFilter>();
        var mesh0 = mf != null ? mf.sharedMesh : null;
        if (mesh0 == null) { Debug.LogError("[Probe] no mesh generated"); return; }

        var verts = mesh0.vertices;
        var colors = mesh0.colors;
        Debug.Log($"[Probe] mesh verts={verts.Length} colors={colors.Length}");
        if (colors.Length == 0) { Debug.LogError("[Probe] mesh has no vertex colours"); return; }

        // sample bands by y
        var buckets = new SortedDictionary<int, (Color c, int n)>();
        for (int i = 0; i < verts.Length; i++)
        {
            int k = Mathf.RoundToInt(verts[i].y * 10f);
            var c = colors[i];
            if (!buckets.ContainsKey(k)) buckets[k] = (c, 0);
            var cur = buckets[k];
            buckets[k] = (cur.c, cur.n + 1);
        }
        foreach (var kv in buckets)
            Debug.Log($"[Probe] y={kv.Key / 10f,6:F1}  colour=({kv.Value.c.r:F2},{kv.Value.c.g:F2},{kv.Value.c.b:F2})  verts={kv.Value.n}");

        UnityEngine.Object.DestroyImmediate(go);
        Debug.Log("[Probe] done");
    }
}
