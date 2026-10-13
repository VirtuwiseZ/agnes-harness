---
name: physics-report-charting
description: 数值求解结果（Node 2b 完成后）值得以曲线/散点/误差棒/区间高亮/二维参数场/交互 widget 呈现时，填写 problem_state.json 的 figures 字段，并在 Node 4 生成自包含公式与图表的单文件 HTML。触发信号是"这一题的结果该不该画图、画哪类图"以及"Node 4 渲染公式与图表内联"。
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

### 1. Node 2.7 — 数值结果静态与交互绘图（7 种静态能力 + 2 种交互分支）

4a. **静态图表分支（默认路径，支持 `curve` / `scatter` / `error_bar` / `interval_highlight` / `heatmap` / `boxplot` / `bar` 及 `thresholds` 物理基准线）**：
   - 在 `problem_state.json` 的 `numerical_artifacts.figures` 下添加图表定义：
     - 连续响应或参数扫描曲线用 `kind: "curve"`（支持多条 `series` 对比，并可通过 `"thresholds": [{"axis": "y", "value": 15.59, "label": "入轨所需 Δv = 15.59 km/s"}]` 叠加物理达标线）；
     - 多天体/多方案离散指标对比优先用 `kind: "bar"`（传入 `"categories": [...]` 与 `"series": [{"name": "...", "values": [...]}]~~~~~~~~~~~~~~~~~~~~~~~`，自动在柱顶标注精确数值并支持叠加 `thresholds` 基准线）。
   - 调用 `python physics-agent/hooks/make_report_figures.py --state physics-agent/runtime/<task-slug>/problem_state.json --out-dir physics-agent/runtime/<task-slug>/figures` 生成图表文件（必须落在 `<task-slug>/figures/` 下）。
   - 在 Node 3 报告正文中通过独立成行的 `{{figure: <figure_id>}}` 语法引用对应图表。

4b. **可选交互图表分支（`interactive` 与 `interactive_live`，按需触发）**：
   - **`kind: "interactive"`**：当题目本身要求展示多参数响应面或三维轨道/场分布，静态图不足以承载时使用（字段含 `backend: "plotly"`, `layout_3d`, `switcher`，详见 `physics-agent/problem_state_schema.md` §Figures）。由 `make_report_figures.py` 渲染为自包含 HTML 片段（内置 plotly.js，零外部 CDN），仅在预计算序列之间切换，不宣称能在浏览器端实时重算重型微分方程。
   - **`kind: "interactive_live"`**：仅适用于闭合初等解析表达式的滑块实时重算（绝不用于需要数值积分的重型 ODE/PDE）。

### 2. Node 4 配套铁律（E1）：LaTeX 公式与图表 100% 单文件离线自包含内联

1. **严禁依赖外部 CDN 或本地 `file://` 相对路径 `fetch()`**：
   - 浏览器在本地双击打开 `file://` 协议的 HTML 报告时，任何 `fetch('vendor/katex/...')` 都会因跨域策略（CORS）直接失败，且分发给用户的单文件 HTML 不得假设同级目录存在 `vendor/katex/`。
   - 因此，`physics-agent/hooks/trace_visualizer.py` 必须将 **LaTeX 数学公式排版引擎（CSS 样式 + 离线数学排版 JS / KaTeX 内联包）** 直接内联进生成的 `.html` 单文件内部，确保用户在无网环境下双击 HTML 文件即可看到完整渲染的数学公式（分式、根式、上下标、希腊字母、积分求和、矩阵等全部正常排版），**绝不允许把裸 `$...$` 或 `$$...$$` 源码直接暴露给用户**。
2. **图表与右侧预览资产内联**：
   - 调用 `trace_visualizer.py` 时，若存在图表则传入 `--figures-dir physics-agent/runtime/<task-slug>/figures`，所有静态图以 base64 `<img>` 内联，所有交互图以自包含 `<div>+<script>` 内联。
   - 生成 HTML 后，必须运行 `python physics-agent/hooks/report_quality_check.py` 验证公式排版引擎已内联、无未渲染的 Markdown/LaTeX 源码、无死链，实测通过后方可交付。
