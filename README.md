# 海东青（HDQ）· Spaceflight Simulator 中型发动机

单机 **150 kN** 的液体火箭发动机，面向中型运载器芯级与重型助推。
三级台阶泵体 + 环形集合器 + 三段式钟形喷管；含可直接安装的 `.pack`、Unity 构建脚本、几何生成器与产品文档。

> 适用于 [Spaceflight Simulator](https://store.steampowered.com/app/1286830/)（Team Curiosity）的自定义部件系统。
> 部件、脚本、文档作者：**zzasza**。

---

## 目录结构

```
.
├── packs/                     可直接放进游戏安装的 海东青引擎.pack
├── source/
│   ├── unity/                 本部件的 Unity 工程自研部分
│   │   └── Assets/
│   │       ├── Editor/        构建 / 修复 / 探查脚本（C#）
│   │       ├── Resources/     prefab、PackData、音效资产
│   │       └── Textures/      模组图标
│   └── tools/                 几何生成、渲染校验、文档生成脚本（Python）
├── docs/                      产品白皮书、性能对比图
├── images/                    三维渲染、组件特写、正视轮廓
├── CHANGELOG.md
└── README.md
```

## 规格

| 项目 | 数值 |
|---|---|
| 推力 | 150 kN |
| 真空比冲 | 318 s |
| 干重 | 5.00 t |
| 推重比 | 3.06 |
| 万向摆角 | ±8° |
| 造价（生涯） | 95 |
| 总长 | 2.900 m |
| 最大直径（出口） | Φ1.150 |
| 对接法兰 | Φ1.000 m · 对接口 +0.1125 |
| 推力作用点 | y = -4.10（自对接口向下） |
| 质心 | y = -0.85 |
| 推进剂 | Liquid Fuel |
| 音效基频 | 0.140 |
| 包版本 / 标签 | 1.1 / `haidongqing` |

## 结构特征

1. **双色顶盘 + 桁架加强边梁** —— 顶盘上半 Metal×0.9、下半 Color_White×0.45，分缝在 y=0；下沿一圈深色实心边梁（半宽 1.033，略大于盘面）承担承载叙事。
2. **三级台阶泵体** —— Φ0.370 / 0.442 / 0.408 三级外露台阶，台阶以圆角过渡；两侧内弯肘管先汇入**环形集合器**（橙色识别环）再进入泵。
3. **三段式钟形喷管** —— 主段（中灰）+ 深色套筒联动环（出口上方 0.85 m 接缝）+ 浅色延伸裙 + 卷边厚唇口。
4. **无外露接缝** —— 肘管两端均插入实体（顶端深入顶盘、末端径向插入集合环内部），仰视与转动都不露管口。

## 安装

1. 关闭游戏。
2. 把 `packs/海东青引擎.pack` 复制到：

   ```
   Spaceflight Simulator Game/Mods/Custom_Assets/Parts/
   ```

3. 启动游戏 → 进入**建造界面** → 发动机分类中即可找到（图标为深色底 + 橙色识别环）。
4. 卸载时直接删除该 `.pack` 即可，不残留资源。

## 使用要点

- **燃料**：`Liquid Fuel`，与游戏自带贮箱直接连通，无需额外管线。
- **叠配**：法兰 Φ1.000 / 对接口 +0.1125，可与同规格部件任意叠配、并排、捆绑。
- **万向节**：随发动机点火启用，±8°，可在建造界面关闭。
- **热区**：受热区宽 1.90 m、长 9.2 m，贴近其它部件布置时留出间距。
- **卸裙构型**：延伸裙为独立网格，在 prefab 中停用该节点即可得到海平面短喷管。

## 源码说明

### 环境

| 项 | 版本 |
|---|---|
| Unity | 6000.1.17f1（Unity 6.1） |
| 工程模板 | SFS Modding Toolkit（提供 `Part` / `EngineModule` / `CustomPipe` / `PipeMesh` 等类型） |

### 仓库范围

本仓库只包含**本部件自研的部分**：构建脚本、prefab、PackData、音效资产、图标、工具链与文档。

以下内容**不在仓库内**（版权属于游戏本体与工具链作者，或与本部件的制作无关）：
游戏反编译源码、官方贴图与材质、通用音效素材，以及其它机型的部件与构建脚本。
因此本仓库是**源码归档**，不能脱离游戏本体单独编译；要重建工程，请把 `source/unity/Assets` 下的文件按原相对路径放回 Modding Toolkit 工程。

### 构建

Unity 菜单（需先打开 Modding Toolkit 工程）：

```
SFS → HaiDongQing → Repair Junctions + Rebuild Pack
```

该脚本对**现有 prefab 做局部补丁**（只替换指定管件的点列/色带与部件名，保留手工修改如尾焰），随后打成 AssetBundle 并写入 `Assets/ModBuilder/海东青引擎.pack`，同时复制到游戏 Mods 目录。

批处理（工程被占用时建议先复制一份工程）：

```
Unity.exe -batchmode -nographics -projectPath <工程副本> ^
  -executeMethod HaiDongQingFix.BuildAll -quit -logFile build.log
```

### 脚本职责

| 文件 | 作用 |
|---|---|
| `Editor/HaiDongQingFix.cs` | 构建主流程：改几何/色带/名称 → 校验 → 打 bundle → 部署 |
| `Editor/PartColorProbe.cs` | 生成真实网格并按高度打印顶点色，用于校验色带落位 |
| `Editor/PipeMeshProbe.cs` | 探查 `PipeMesh` 字段与方法，用于逆向色带语义 |
| `tools/gen_hdq_geometry.py` | 由 2D 设计参数生成轮廓与色带数据（输出 C# 数组） |
| `tools/gen_hdq_icon.py` | 生成模组图标（256×256） |
| `tools/gen_whitepaper.py` | 生成产品白皮书（内联 SVG 图表） |
| `tools/gen_compare_png.py` | 生成性能对比图（PNG） |
| `tools/preview_hdq.py` / `render3d_hdq.py` / `render_detail.py` / `render_final.py` | 轮廓数据的离线渲染（z-buffer），无进游戏时的外观校验 |
| `tools/verify_hdq_pack.py` | 解包 `.pack`，核对 PackData / 组件 / 材质 / 音频完整性 |
| `tools/parse_prefab.py` / `inspect_prefab_full.py` | prefab YAML 解析与层级/参数导出 |

## 技术要点（踩过的坑）

1. **色带高度按累计 |Δy| 计**，不是弧长。`PipeMesh` 的 `colors[i].height` 表示该色带的结束高度。
2. **相邻两点 y 相同的线段会被整段丢弃**（斜率计算除以 Δheight）。台阶、底面必须留 ≥2 mm 的 y 差，否则会出现"底面消失、从下方看穿"或"管口贴着表面开口"。
3. **管件是单面壳体**：任何外露管口都会看穿，两端必须埋入实体或被实体面遮住。
4. **两根管斜交**会留下薄片；接到圆柱体上时让管子径向水平插入并深入内部，交线才是干净的椭圆。
5. prefab 改造必须 **Unpack 后另存**，否则会保存成 Variant 并夹带原 prefab。

## 文档

- `docs/青鹰SEPro_海东青_产品白皮书.html` —— 定位、核心功能、适用场景、关键规格、安装部署与四组对比图（单文件，离线可开）
- `docs/两款发动机_性能对比图.png` —— 8 项指标成对条形图

> 这两份文档为横向评测，内部含与一款 112 kN 级发动机（青鹰SE Pro）的对比；该机型**不随本仓库分发**。

## 版本与提交规范

- **主分支**：`main`（线性历史）
- **标签**：`v1.2.0` 为当前状态；变更见 `CHANGELOG.md`
- **提交信息**：Conventional Commits，中文正文

  ```
  <type>(<scope>): <简述>

  - <要点 1>
  - <要点 2>
  ```

  `type`：`feat` 新功能、`fix` 几何或参数修复、`docs` 文档、`chore` 构建与杂项；
  `scope` 取 `hdq` / `geometry` / `docs` / `build`。
- **版本号**：`主.次.修订`。结构或气动变化升次版本，参数与缺陷修复升修订号。

## 版权与致谢

- 部件建模、脚本、文档、图片：**zzasza**，采用署名-非商业性使用（转载/二次开发请注明来源）。
- 游戏本体、Modding Toolkit 及其内置贴图、材质、音效：版权归 **Team Curiosity** 与工具链作者所有，本仓库不分发。
- 仓库中的 `.pack` 仅供在正版游戏中使用。
