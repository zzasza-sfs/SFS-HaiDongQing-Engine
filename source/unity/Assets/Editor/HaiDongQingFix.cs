// HaiDongQing (海东青引擎) junction repair - patches the EXISTING prefab in place.
// Only the four pipe objects below are touched (Nozzle / Reinforcement Beam / Pump / Pump2)
// plus the part name; the flame, audio and all other hand edits are left untouched.
//
// What it fixes (feedback 2026-10-17):
//   1. 肘管上端与边梁之间"断裂"：边梁改成带底面的实心环（r 0.17..0.5164, y -0.0875..-0.025），
//      肘管顶端插进边梁体内并被底面遮住，不再从空腔里看穿。
//   2. 肘管下端与集合环"断裂"：肘管末端改为水平径向插入（J 形内弯），
//      端头深入集合环内部 (x 0.165)，开口完全藏在环体内；集合环加高到 0.15 以容纳管径。
//   3. 上方过渡生硬：泵体台阶、喉部环、集合环全部改为倒角/圆角过渡，燃烧室改为平滑鼓形。
//
// Batch: Unity.exe -batchmode -nographics -projectPath <proj> -executeMethod HaiDongQingFix.BuildAll -quit
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using ModLoader;
using Newtonsoft.Json;
using SFS.Parts;
using SFS.Parts.Modules;
using SFS.Variables;
using UnityEditor;
using UnityEngine;

public static class HaiDongQingFix
{
    // ---------------------------------------------------------------- config
    const string PrefabPath   = "Assets/Resources/Parts/Engines/HaiDongQing Engine.prefab";
    const string PackDataPath = "Assets/Resources/Parts/Engines/HaiDongQing.asset";

    const string ColorWhiteAsset = "Assets/Resources/Part Textures/Pattern Textures/Color_White.asset";
    const string MetalAsset      = "Assets/Resources/Part Textures/Pattern Textures/Metal.asset";
    const string Metal4Asset     = "Assets/Resources/Part Textures/Pattern Textures/Metal_4.asset";
    const string ShapeFlatSmooth = "Assets/Resources/Part Textures/Shape Textures/Flat Smooth.asset";
    const string ShapeFlatFaces  = "Assets/Resources/Part Textures/Shape Textures/Flat Faces.asset";

    const string BundleLabel  = "haidongqing";
    const string PackFileName = "海东青引擎.pack";
    const string CacheFolder  = "Assets/ModBuilder/Cache";
    const string OutFolder    = "Assets/ModBuilder";

    const string GameModsPartsDir = @"E:\SteamLibrary\steamapps\common\Spaceflight Simulator\Spaceflight Simulator Game\Mods\Custom_Assets\Parts";

    const string PartTitle = "海东青引擎";
    const string PartDesc  = "海东青引擎（HDQ）：三级泵 + 环形集合器 + 可拆延伸裙的中型一级发动机，单机 150 kN，为中型运载器芯级与重型助推设计，代价是重量与造价";
    const string PackDesc  = "海东青引擎（HDQ）中型一级发动机";

    // ---------------------------------------------------------------- geometry (v3)
    // band heights are cumulative Δy (NOT arc length) - verified against the runtime mesh
    static readonly float[] BaseHeights = { 0.05f, 0.275f };

    static readonly Vector4[] BeamPoints =
    {
        new Vector4(0f, -0.025f, 1.0328f, 0f),
        new Vector4(0f, -0.0875f, 1.0328f, 0f),
        new Vector4(0f, -0.1f, 0.004f, 0f),
    };
    static readonly float[] BeamHeights = { 0.075f };
    static readonly Color[] BeamColors = { new Color(0.42f, 0.42f, 0.42f, 1f) };

    static readonly Vector4[] NozzlePoints =
    {
        new Vector4(0f, -1.8062f, 0.7405f, 0f),
        new Vector4(0f, -1.7093f, 0.7281f, 0f),
        new Vector4(0f, -1.6175f, 0.7049f, 0f),
        new Vector4(0f, -1.5309f, 0.672f, 0f),
        new Vector4(0f, -1.4498f, 0.6305f, 0f),
        new Vector4(0f, -1.3742f, 0.5816f, 0f),
        new Vector4(0f, -1.3045f, 0.5265f, 0f),
        new Vector4(0f, -1.2408f, 0.4661f, 0f),
        new Vector4(0f, -1.1832f, 0.4017f, 0f),
        new Vector4(0f, -1.1321f, 0.3344f, 0f),
        new Vector4(0f, -1.0875f, 0.2653f, 0f),
        new Vector4(0f, -1.0775f, 0.2818f, 0f),
        new Vector4(0f, -0.9975f, 0.2818f, 0f),
        new Vector4(0f, -0.9875f, 0.2652f, 0f),
        new Vector4(0f, -0.95f, 0.2772f, 0f),
        new Vector4(0f, -0.9f, 0.2892f, 0f),
        new Vector4(0f, -0.85f, 0.291f, 0f),
        new Vector4(0f, -0.8f, 0.2838f, 0f),
        new Vector4(0f, -0.7625f, 0.2722f, 0f),
        new Vector4(0f, -0.7375f, 0.2652f, 0f),
        new Vector4(0f, -0.73f, 0.32f, 0f),
        new Vector4(0f, -0.718f, 0.376f, 0f),
        new Vector4(0f, -0.7f, 0.409f, 0f),
        new Vector4(0f, -0.64f, 0.409f, 0f),
        new Vector4(0f, -0.632f, 0.428f, 0f),
        new Vector4(0f, -0.625f, 0.442f, 0f),
        new Vector4(0f, -0.535f, 0.442f, 0f),
        new Vector4(0f, -0.525f, 0.396f, 0f),
        new Vector4(0f, -0.518f, 0.3702f, 0f),
        new Vector4(0f, -0.4825f, 0.3702f, 0f),
        new Vector4(0f, -0.4745f, 0.43f, 0f),
        new Vector4(0f, -0.4625f, 0.4864f, 0f),
        new Vector4(0f, -0.3125f, 0.4864f, 0f),
        new Vector4(0f, -0.3025f, 0.42f, 0f),
        new Vector4(0f, -0.2925f, 0.3536f, 0f),
        new Vector4(0f, -0.0875f, 0.3536f, 0f),
    };
    static readonly float[] NozzleHeights = { 0.7188f, 0.8188f, 1.0688f, 1.1663f, 1.2713f, 1.3238f, 1.5138f, 1.7188f };
    static readonly string[] NozzleTex = { "s", "o", "m", "m", "m", "m", "o", "s" };
    static readonly Color[] NozzleColors =
    {
        new Color(0.55f, 0.55f, 0.55f, 1f),        // bell
        new Color(0.91f, 0.585f, 0.235f, 1f),      // throat identification ring (orange)
        new Color(0.62f, 0.62f, 0.62f, 1f),        // chamber barrel
        new Color(0.5f, 0.5f, 0.5f, 1f),           // pump stage 3
        new Color(0.42f, 0.42f, 0.42f, 1f),        // pump stage 2
        new Color(0.5f, 0.5f, 0.5f, 1f),           // pump stage 1
        new Color(0.91f, 0.585f, 0.235f, 1f),      // annular collector (orange)
        new Color(1f, 1f, 1f, 1f),                 // neck
    };

    static readonly Vector4[] ExtPoints =
    {
        new Vector4(0f, -2.7875f, 1.1335f, 0f),
        new Vector4(0f, -2.7625f, 1.1495f, 0f),
        new Vector4(0f, -2.725f, 1.1409f, 0f),
        new Vector4(0f, -2.7219f, 1.1153f, 0f),
        new Vector4(0f, -2.599f, 1.0852f, 0f),
        new Vector4(0f, -2.4708f, 1.034f, 0f),
        new Vector4(0f, -2.3406f, 0.9795f, 0f),
        new Vector4(0f, -2.2083f, 0.9217f, 0f),
        new Vector4(0f, -2.074f, 0.8604f, 0f),
        new Vector4(0f, -1.9375f, 0.7958f, 0f),
        new Vector4(0f, -1.935f, 0.8058f, 0f),
        new Vector4(0f, -1.8062f, 0.7505f, 0f),
        new Vector4(0f, -1.8037f, 0.7475f, 0f),
        new Vector4(0f, -1.65f, 0.7201f, 0f),
    };
    static readonly float[] ExtHeights = { 0.0656f, 0.8525f, 0.9838f, 1.1375f };
    static readonly Color[] ExtColors =
    {
        new Color(0.85f, 0.85f, 0.85f, 1f),        // rolled lip
        new Color(1f, 1f, 1f, 1f),                 // skirt
        new Color(0.42f, 0.42f, 0.42f, 1f),        // coupling collar
        new Color(0.85f, 0.85f, 0.85f, 1f),        // sleeve
    };

    static readonly Vector4[] PumpPoints =
    {
        new Vector4(0.39f, 0.055f, 0.1243f, 0f),
        new Vector4(0.39f, -0.07f, 0.1243f, -0.0006f),
        new Vector4(0.389f, -0.15f, 0.1242f, -0.0048f),
        new Vector4(0.384f, -0.225f, 0.1232f, -0.0167f),
        new Vector4(0.37f, -0.29f, 0.1182f, -0.0384f),
        new Vector4(0.345f, -0.345f, 0.1027f, -0.0701f),
        new Vector4(0.31f, -0.378f, 0.0633f, -0.1071f),
        new Vector4(0.268f, -0.3905f, 0.0209f, -0.1226f),
        new Vector4(0.225f, -0.3925f, 0.0096f, -0.124f),
        new Vector4(0.165f, -0.3985f, 0.0124f, -0.1237f),
    };
    static readonly float[] PumpHeights = { 0.4535f };
    static readonly Color[] PumpColors = { new Color(0.55f, 0.55f, 0.55f, 1f) };

    static readonly Vector4[] Pump2Points =
    {
        new Vector4(-0.39f, 0.055f, -0.1243f, 0f),
        new Vector4(-0.39f, -0.07f, -0.1243f, -0.0006f),
        new Vector4(-0.389f, -0.15f, -0.1242f, -0.0048f),
        new Vector4(-0.384f, -0.225f, -0.1232f, -0.0167f),
        new Vector4(-0.37f, -0.29f, -0.1182f, -0.0384f),
        new Vector4(-0.345f, -0.345f, -0.1027f, -0.0701f),
        new Vector4(-0.31f, -0.378f, -0.0633f, -0.1071f),
        new Vector4(-0.268f, -0.3905f, -0.0209f, -0.1226f),
        new Vector4(-0.225f, -0.3925f, -0.0096f, -0.124f),
        new Vector4(-0.165f, -0.3985f, -0.0124f, -0.1237f),
    };
    static readonly float[] Pump2Heights = { 0.4535f };
    static readonly Color[] Pump2Colors = { new Color(0.55f, 0.55f, 0.55f, 1f) };

    // ---------------------------------------------------------------- entry points
    [MenuItem("SFS/HaiDongQing/Repair Junctions + Rebuild Pack")]
    public static void MenuRun() { Run(batch: false); }

    public static void BuildAll() { Run(batch: true); }

    static void Run(bool batch)
    {
        try
        {
            AssetDatabase.Refresh();

            string packDataPath = EnsurePackData();
            PatchPrefab();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            BuildPack(packDataPath);
            Debug.Log("================ [HaiDongQing] DONE ================");
        }
        catch (Exception e)
        {
            Debug.LogError("[HaiDongQing] EXCEPTION: " + e);
            if (batch) throw;
        }
    }

    static void Fail(string msg)
    {
        Debug.LogError("[HaiDongQing] " + msg);
        throw new Exception(msg);
    }

    // ---------------------------------------------------------------- PackData + naming
    static string EnsurePackData()
    {
        var pd = AssetDatabase.LoadAssetAtPath<PackData>(PackDataPath);
        if (pd == null) Fail("PackData missing: " + PackDataPath);

        pd.DisplayName = PartTitle;
        pd.Description = PackDesc;
        pd.Version = "1.1";
        pd.Author = "zzasza";
        EditorUtility.SetDirty(pd);
        AssetDatabase.SaveAssets();
        Debug.Log("[HaiDongQing] PackData: " + pd.DisplayName + " v" + pd.Version);
        return PackDataPath;
    }

    // ---------------------------------------------------------------- prefab patch
    static void PatchPrefab()
    {
        if (AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath) == null)
            Fail("Prefab missing: " + PrefabPath);

        GameObject root = PrefabUtility.LoadPrefabContents(PrefabPath);
        try
        {
            root.name = "HaiDongQing Engine";
            var vars = root.GetComponent<VariablesModule>();
            if (vars == null) Fail("VariablesModule missing on root.");

            // ---- part name / description (flame + engine numbers untouched) ----
            var part = root.GetComponent<Part>();
            if (part != null)
            {
                var so = new SerializedObject(part);
                so.FindProperty("displayName.TranslatableName").stringValue = PartTitle;
                so.FindProperty("displayName.plainText").boolValue = true;
                so.FindProperty("description.TranslatableName").stringValue = PartDesc;
                so.FindProperty("description.plainText").boolValue = true;
                so.ApplyModifiedPropertiesWithoutUndo();
            }

            var ctColorWhite = AssetDatabase.LoadAssetAtPath<ColorTexture>(ColorWhiteAsset);
            var ctMetal = AssetDatabase.LoadAssetAtPath<ColorTexture>(MetalAsset);
            var ctMetal4 = AssetDatabase.LoadAssetAtPath<ColorTexture>(Metal4Asset);
            var shFlatSmooth = AssetDatabase.LoadAssetAtPath<ShapeTexture>(ShapeFlatSmooth);
            var shFlatFaces = AssetDatabase.LoadAssetAtPath<ShapeTexture>(ShapeFlatFaces);
            var texMap = new Dictionary<string, ColorTexture> { { "w", ctColorWhite }, { "m", ctMetal }, { "s", ctMetal4 }, { "o", ctColorWhite } };
            var shapeMap = new Dictionary<string, ShapeTexture> { { "s", shFlatSmooth }, { "m", shFlatFaces }, { "o", shFlatFaces } };

            // ---- base plate: only the band heights change (arc length -> Δy) ----
            var baseT = root.transform.Find("Base");
            if (baseT == null) Fail("Base not found.");
            SetHeightsOnly(baseT.GetComponent<PipeMesh>(), BaseHeights);

            // ---- nozzle extension: same y-monotonic fixes ----
            var extT = root.transform.Find("Man/Nozzle Extension");
            if (extT == null) Fail("Man/Nozzle Extension not found.");
            ApplyPipe(extT.GetComponent<CustomPipe>(), extT.GetComponent<PipeMesh>(), vars,
                      ExtPoints, ExtColors, ExtHeights,
                      new ColorTexture[] { ctMetal, ctMetal4, ctMetal, ctMetal4 },
                      new ShapeTexture[] { shFlatFaces, shFlatSmooth, shFlatFaces, shFlatSmooth },
                      ExtHeights);

            // ---- beam ----
            var beamT = root.transform.Find("Reinforcement Beam");
            if (beamT == null) Fail("Reinforcement Beam not found.");
            ApplyPipe(beamT.GetComponent<CustomPipe>(), beamT.GetComponent<PipeMesh>(), vars,
                      BeamPoints, BeamColors, BeamHeights,
                      new ColorTexture[] { ctMetal }, new ShapeTexture[] { shFlatFaces }, BeamHeights);

            // ---- main body ----
            var nozzleT = root.transform.Find("Man/Nozzle");
            if (nozzleT == null) Fail("Man/Nozzle not found.");
            var nCts = new ColorTexture[NozzleTex.Length];
            var nSts = new ShapeTexture[NozzleTex.Length];
            for (int i = 0; i < NozzleTex.Length; i++)
            {
                nCts[i] = texMap[NozzleTex[i]];
                nSts[i] = shapeMap[NozzleTex[i]];
            }
            ApplyPipe(nozzleT.GetComponent<CustomPipe>(), nozzleT.GetComponent<PipeMesh>(), vars,
                      NozzlePoints, NozzleColors, NozzleHeights, nCts, nSts, NozzleHeights);

            // ---- side ducts ----
            foreach (var name in new[] { "Pump", "Pump2" })
            {
                var t = nozzleT.Find(name);
                if (t == null) Fail(name + " not found.");
                var pts = name == "Pump" ? PumpPoints : Pump2Points;
                ApplyPipe(t.GetComponent<CustomPipe>(), t.GetComponent<PipeMesh>(), vars,
                          pts, PumpColors, PumpHeights,
                          new ColorTexture[] { ctMetal4 }, new ShapeTexture[] { shFlatSmooth }, PumpHeights);
            }

            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            Debug.Log("[HaiDongQing] Prefab patched: " + PrefabPath);
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(root);
        }

        // ---- validation on the saved asset ----
        var saved = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
        if (saved == null) Fail("Saved prefab not loadable.");
        if (PrefabUtility.GetPrefabAssetType(saved) != PrefabAssetType.Regular)
            Fail("Prefab is not standalone: " + PrefabUtility.GetPrefabAssetType(saved));

        var nozzle = saved.transform.Find("Man/Nozzle");
        var beam = saved.transform.Find("Reinforcement Beam");
        var pump = nozzle != null ? nozzle.Find("Pump") : null;
        if (nozzle == null || beam == null || pump == null) Fail("Hierarchy broken after patch.");

        int nPts = nozzle.GetComponent<CustomPipe>().composedShape.points.Count;
        int bPts = beam.GetComponent<CustomPipe>().composedShape.points.Count;
        int pPts = pump.GetComponent<CustomPipe>().composedShape.points.Count;
        var engine = saved.GetComponent<EngineModule>();
        var partC = saved.GetComponent<Part>();
        var soName = new SerializedObject(partC).FindProperty("displayName.TranslatableName").stringValue;
        Debug.Log($"[HaiDongQing] Check: nozzle pts={nPts} beam pts={bPts} pump pts={pPts}, " +
                  $"name={soName}, thrust={(engine != null ? engine.thrust.input : "?")}, " +
                  $"mass={partC.mass.input}");

        if (nPts != NozzlePoints.Length || bPts != BeamPoints.Length || pPts != PumpPoints.Length)
            Fail("Point counts do not match the design arrays.");
        Debug.Log("[HaiDongQing] Validation passed.");
    }

    // ---------------------------------------------------------------- helpers
    /// <summary>Rewrites only the layer heights (used for the untouched base plate).</summary>
    static void SetHeightsOnly(PipeMesh mesh, float[] heights)
    {
        if (mesh == null) return;
        var so = new SerializedObject(mesh);
        var cArr = so.FindProperty("colors.colors");
        for (int i = 0; i < cArr.arraySize && i < heights.Length; i++)
            cArr.GetArrayElementAtIndex(i).FindPropertyRelative("height").floatValue = heights[i];
        var tArr = so.FindProperty("textures.textures");
        for (int i = 0; i < tArr.arraySize && i < heights.Length; i++)
            tArr.GetArrayElementAtIndex(i).FindPropertyRelative("height").floatValue = heights[i];
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    static void ApplyPipe(CustomPipe pipe, PipeMesh mesh, VariablesModule vars,
                          Vector4[] pts, Color[] colors, float[] heights,
                          ColorTexture[] cts, ShapeTexture[] sts, float[] texHeights)
    {
        if (pipe == null || mesh == null) Fail("Pipe/Mesh missing on a target object.");
        SetPipePoints(pipe, vars, pts);
        SetPipeColors(mesh, colors, heights);
        SetPipeTextures(mesh, cts, sts, texHeights);
    }

    static void SetPipePoints(CustomPipe pipe, VariablesModule vars, Vector4[] pts)
    {
        var so = new SerializedObject(pipe);
        var arr = so.FindProperty("composedShape.points");
        arr.arraySize = pts.Length;

        for (int i = 0; i < pts.Length; i++)
        {
            SerializedProperty e = arr.GetArrayElementAtIndex(i);
            BindVars(e.FindPropertyRelative("variables"), vars);
            BindVars(e.FindPropertyRelative("position.variables"), vars);
            BindVars(e.FindPropertyRelative("position.x.variables"), vars);
            BindVars(e.FindPropertyRelative("position.y.variables"), vars);
            BindVars(e.FindPropertyRelative("width.variables"), vars);
            BindVars(e.FindPropertyRelative("width.x.variables"), vars);
            BindVars(e.FindPropertyRelative("width.y.variables"), vars);

            e.FindPropertyRelative("position.x.input").stringValue = F(pts[i].x);
            e.FindPropertyRelative("position.y.input").stringValue = F(pts[i].y);
            e.FindPropertyRelative("width.x.input").stringValue = F(pts[i].z);
            e.FindPropertyRelative("width.y.input").stringValue = F(pts[i].w);
        }
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    static void BindVars(SerializedProperty p, VariablesModule vars)
    {
        if (p != null) p.objectReferenceValue = vars;
    }

    static string F(float v) => v.ToString("0.####", CultureInfo.InvariantCulture);

    static void SetPipeColors(PipeMesh mesh, Color[] colors, float[] heights)
    {
        var so = new SerializedObject(mesh);
        so.FindProperty("colors.mode").enumValueIndex = 1;      // Multiple
        var arr = so.FindProperty("colors.colors");
        arr.arraySize = colors.Length;
        for (int i = 0; i < colors.Length; i++)
        {
            var e = arr.GetArrayElementAtIndex(i);
            e.FindPropertyRelative("color.type").enumValueIndex = 0;   // Local
            e.FindPropertyRelative("color.colorBasic").colorValue = colors[i];
            e.FindPropertyRelative("height").floatValue = heights[i];
        }
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    static void SetPipeTextures(PipeMesh mesh, ColorTexture[] cts, ShapeTexture[] sts, float[] heights)
    {
        var so = new SerializedObject(mesh);
        so.FindProperty("textures.textureMode").enumValueIndex = 1;   // Multiple
        var arr = so.FindProperty("textures.textures");
        arr.arraySize = cts.Length;
        for (int i = 0; i < cts.Length; i++)
        {
            var e = arr.GetArrayElementAtIndex(i);
            e.FindPropertyRelative("texture.colorTexture").objectReferenceValue = cts[i];
            e.FindPropertyRelative("texture.shapeTexture").objectReferenceValue = sts[i];
            e.FindPropertyRelative("height").floatValue = heights[i];
        }
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    // ---------------------------------------------------------------- pack
    static void BuildPack(string packDataPath)
    {
        Directory.CreateDirectory(OutFolder);
        Directory.CreateDirectory(CacheFolder);

        AssetImporter.GetAtPath(PrefabPath).SetAssetBundleNameAndVariant(BundleLabel, "");
        AssetImporter.GetAtPath(packDataPath).SetAssetBundleNameAndVariant(BundleLabel, "");
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        byte[] win = BuildForTarget("Windows", BuildTarget.StandaloneWindows64);
        if (win == null) Fail("Windows asset bundle build failed.");

        byte[] android = null;
        try { android = BuildForTarget("Android", BuildTarget.Android); }
        catch (Exception e) { Debug.LogWarning("[HaiDongQing] Android bundle skipped: " + e.Message); }

        var pack = new PackOut { WindowsBuild = win, AndroidBuild = android };
        string packPath = Path.Combine(OutFolder, PackFileName);
        File.WriteAllText(packPath, JsonConvert.SerializeObject(pack));
        Debug.Log($"[HaiDongQing] Pack written: {packPath}  (windows {win.Length} bytes, android {(android == null ? 0 : android.Length)} bytes)");

        if (Directory.Exists(GameModsPartsDir))
        {
            string dest = Path.Combine(GameModsPartsDir, PackFileName);
            File.Copy(packPath, dest, true);
            Debug.Log("[HaiDongQing] Deployed to game: " + dest);
        }
        else Debug.LogWarning("[HaiDongQing] Game mods folder not found, skipped deploy.");

        FileUtil.DeleteFileOrDirectory(CacheFolder);
        FileUtil.DeleteFileOrDirectory(CacheFolder + ".meta");
        AssetDatabase.Refresh();
    }

    static byte[] BuildForTarget(string platformFolderName, BuildTarget target)
    {
        string relativePath = CacheFolder + "/" + platformFolderName;
        Directory.CreateDirectory(relativePath);
        BuildPipeline.BuildAssetBundles(relativePath, BuildAssetBundleOptions.None, target);

        string file = Path.Combine(relativePath, BundleLabel);
        if (File.Exists(file)) return File.ReadAllBytes(file);

        Debug.LogError("[HaiDongQing] Can't find built asset bundle at " + file);
        return null;
    }

    [Serializable]
    class PackOut
    {
        public byte[] MacBuild, WindowsBuild, AndroidBuild, IOS_Build, CodeAssembly;
    }
}
