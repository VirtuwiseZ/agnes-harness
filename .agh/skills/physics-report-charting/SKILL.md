---
name: physics-report-charting
description: '数值求解结果（Node 2b 完成后）值得以曲线/散点/误差棒/区间高亮/二维参数场/交互 widget 呈现时，填写 problem_state.json 的 figures 字段，并在 Node 4 生成自包含公式与图表的单文件 HTML。触发信号是“这一题的结果该不该画图、画哪类图”以及“Node 4 渲染公式与图表内联”。'
---

> **状态说明（10/13 已定稿，移除历史占位符）**：本 Skill 涵盖 **Node 2.7（数值结果绘图，含 6 种静态 kind 与 `interactive` / `interactive_live` 两个可选分支）** 以及 **Node 4 的公式（LaTeX）与图表（base64 / Plotly）100% 离线自包含内联渲染要求（E1 铁律）**。完整字段规范见 `physics-agent/problem_state_schema.md` §Figures。

**触发时机与必画规则（10/13 升级，解决 Test 3/Test 6 漏画图与 Test 5 空白废图问题）**：
- 进入 Node 2b 完成数值求解之后、Node 4 渲染之前，**只要本题包含以下任一情形，Node 2.7 即为强制必做项（不得留空跳过）**：
  1. 多方案 / 多天体 / 多候选参数对比（如四颗伽利略卫星减速上限对比、不同发射角/材料对比）；
  2. 参数连续扫描或单调性扫描（如边界门 `sweep`、减速量随偏转角 $\delta$ 或入射速度 $v_\infty$ 的连续变化曲线）；
  3. 微分方程（ODE/PDE）时间/空间演化轨迹或频响曲线。
- **防“近乎空白/水平死线”铁律（Test 5 教训）**：
  - 严禁把在横轴范围内几乎恒定不变的量（极差 $\approx 0$）单独画成一条主曲线（`make_report_figures.py` 的 `_check_degeneracy_and_scale` 门禁会直接报错拦截）；恒定基准值（如入轨需求 $\Delta v_{req} = 15.59\ \text{km/s}$）必须声明在 `thresholds` 字段中作为水平/垂直参考线绘制！
  - 若正值数据跨度超过 50 倍且集中在低值区，应优先设置 `axes.y.scale = "log"` 防止线性轴把曲线压在底边形成“假空白”。

### 1. Node 2.7 — 数值结果静态与交互绘图（9 种静态科学绘图 + 2 种交互分支）

4a. **静态科学图表分支（默认路径，支持 9 种科研级图表种类与 `thresholds` 物理基准线）**：
   - 在 `problem_state.json` 的 `numerical_artifacts.figures` 下添加图表定义，根据物理场景精准选型：
     - **连续动态响应或参数扫描**：`kind: "curve"` / `"scatter"`（支持多条 `series` 对比，通过 `"thresholds": [{"axis": "y", "value": 15.59, "label": "入轨所需 Δv = 15.59 km/s"}]` 叠加物理安全/达标线）；
     - **离散多方案/多天体定量对比**：`kind: "bar"`（传入 `"categories": [...]` 与 `"series": [...]`，自动在柱顶标注精确数值并支持叠加 `thresholds` 基准线）；
     - **二维连续物理场或参数敏感性矩阵**：`kind: "heatmap"`：
       - 物理发散量（冷热温差、正负速度扰动、误差残差）：设置 `"diverging": true` 或 `"cmap": "coolwarm"`，引擎自动应用以 $0$ 为中心的 `TwoSlopeNorm(vcenter=0.0)`；
       - 跨数量级物理场（光通量、恒星密度、能量谱）：设置 `"norm": "log"` 启用 `LogNorm` 对数色标；
       - 连续空间等值线：设置 `"heatmap_style": "contourf"`，引擎自动叠加等高线轮廓并内联标注物理数值（`contour_labels: true`）；
       - 离散参数相关性矩阵：设置 `"annot": true`，自动在格子中心标注数值并根据背景色自适应黑白对比度文本；
     - **空间三维运动轨迹**：`kind: "3d_curve"`（每个 series 包含等长 `x, y, z` 坐标；支持传入 `"ground_projection": true` 在底面自动投射半透明灰色投影虚线，大幅增强三维深度感；支持传入 `"view": {"elev": 26, "azim": -60}` 调整透视视角）；
     - **三维势能曲面 / 二维能量景观 / 波函数分布**：`kind: "3d_surface"`（传入二维标量网格 `grid`，支持底部等高线切片投影 `"bottom_contour": true` 与三维立体色标）；
     - **统计分布对比**：`kind: "boxplot"` / `"error_bar"` / `"interval_highlight"`。
   - **图例零遮挡铁律（Zero-Occlusion Legend Rule）**：
     - 在所有 2D 与 3D 图表中，**严禁图例框压盖数据曲线、数据散点或初始运动段**；
     - 绘制 $\ge 3$ 条曲线时，引擎自动启用外挂式布局（`legend_position="outside"`，置于画布右侧独立边距）；
     - 在编写手绘 SVG/HTML 报告时，必须使用外置 Flex 胶囊图例栏（`.legend-bar` + `.legend-pill`），绘图区 100% 留给数据。
   - 调用 `python physics-agent/hooks/make_report_figures.py --state physics-agent/runtime/<task-slug>/problem_state.json --out-dir physics-agent/runtime/<task-slug>/figures` 生成图表文件（必须落在 `<task-slug>/figures/` 下）。
   - 在 Node 3 报告正文中通过独立成行的 `{{figure: <figure_id>}}` 语法引用对应图表。

4b. **可选交互图表分支（`interactive` 与 `interactive_live`，按需触发）**：
   - **`kind: "interactive"`**：当题目本身要求展示三维立体轨道（支持鼠标 360° 旋转、缩放、悬停拾取坐标）或多参数预计算结果切换时使用（字段含 `backend: "plotly"`, `layout_3d`, `switcher`，详见 `physics-agent/problem_state_schema.md` §Figures）。由 `make_report_figures.py` 渲染为自包含 HTML 片段（内置 plotly.js，零外部 CDN），仅在预计算序列之间切换，不宣称能在浏览器端实时重算重型微分方程。
   - **`kind: "interactive_live"`**：仅适用于闭合初等解析表达式的滑块实时重算（如 GeoGebra 式调参实时重绘；绝不用于需要重型数值积分的 ODE/PDE）。

### 2. Node 4 配套铁律（E1）：LaTeX 公式与图表 100% 单文件离线自包含内联

1. **严禁依赖外部 CDN 或本地 `file://` 相对路径 `fetch()`**：
   - 浏览器在本地双击打开 `file://` 协议的 HTML 报告时，任何 `fetch('vendor/katex/...')` 都会因跨域策略（CORS）直接失败，且分发给用户的单文件 HTML 不得假设同级目录存在 `vendor/katex/`。
   - 因此，`physics-agent/hooks/trace_visualizer.py` 必须将 **LaTeX 数学公式排版引擎（CSS 样式 + 离线数学排版 JS / KaTeX 内联包）** 直接内联进生成的 `.html` 单文件内部，确保用户在无网环境下双击 HTML 文件即可看到完整渲染的数学公式（分式、根式、上下标、希腊字母、积分求和、矩阵等全部正常排版），**绝不允许把裸 `$...$` 或 `$$...$$` 源码直接暴露给用户**。
2. **图表与右侧预览资产内联**：
   - 调用 `trace_visualizer.py` 时，若存在图表则传入 `--figures-dir physics-agent/runtime/<task-slug>/figures`，所有静态图以 base64 `<img>` 内联，所有交互图以自包含 `<div>+<script>` 内联。
   - 生成 HTML 后，必须运行 `python physics-agent/hooks/report_quality_check.py` 验证公式排版引擎已内联、无未渲染的 Markdown/LaTeX 源码、无死链，实测通过后方可交付。
