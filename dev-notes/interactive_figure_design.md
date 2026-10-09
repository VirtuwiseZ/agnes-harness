# Node 2.7 交互图表分支 — 设计方案（v1，待动手实现）

> 状态：**设计已定、代码未写**。这份文档先把"交互分支"的边界、schema 改动、
> 代码改动点、依赖改动列清楚，等确认后一起动手（不抢跑）。
> 触发前提：本轮"报告呈现理念"讨论中确认的 —— 当"题目本身要求答案是一个可
> 调参交互的科学图"（一两张静态图无法承载）时，允许选择比默认静态 matplotlib
> 路径更复杂的技术路线；**不是**把静态路径废弃，而是在 Node 2.7 里多一个可
> 选的 kind 分支。

## 1. 实测结论（Plotly 7.1.0，本机 Python 3.13，2026-10-08 跑过，不是猜测）

- **能做到的**：`plotly.io.to_html(fig, include_plotlyjs="inline")` 产出的 HTML
  片段，**完全不依赖任何外部 CDN/JS 依赖**（实测 3D surface 一例，4.8 MB，
  grep 确认没有任何 `src="https://...plotly..."` 外部引用），直接内联进
  项目现有的"绝对只读、静态、单文件"HTML 报告里，浏览器打开后 3D 可旋转、
  可悬停看数值、可缩放；`Updatemenu`（按钮在几组**已经算好**的数据集之间
  切换，用 `method="restyle"` + `args=[["visible"], [True, False]]` 的
  dict 形式构造，不是 Python 端回调）在纯静态导出下也实测能正常渲染、
  能点。
- **做不到的（必须写进 schema/docstring，防止之后误判为"能实现"）**：
  "用户拖一个滑块改某个物理参数 → 图实时重新解一次 ODE/重新算一遍数值"
  —— 这需要**运行时**重新计算，纯静态 HTML 片段做不到（Python 端代码已经
  跑完了，浏览器端没有重新解方程的机制）。唯一能做的"最接近"效果是：
  上游（Node 2b/2.7）一次性把**几组典型参数值对应的结果都预先算好**，
  存进同一条 `figures` 记录的多个 `series` 里，`Updatemenu` 按钮在这几组
  预计算结果之间切换 —— 这是"参数扫描 + 展示层切换"，不是"实时改参数
  实时重算"。这条边界要在 `make_report_figures.py` 的新 kind docstring 里
  写死，跟"脚本不做物理判断"的原则完全一致（"该扫哪几组参数、每组算出来的
  数值是多少"仍然是上游的事，脚本只负责照单画出来 + 加切换按钮）。
- **没有选 Bokeh/Manim 的理由**（按"避免重复造轮子、优先用成熟开源"）：
  Bokeh 的等价"纯静态导出 + 交互"能力需要实测确认（不假设），且社区成熟
  度/文档明确程度不如 Plotly 的 `include_plotlyjs="inline"` 写得一清二楚；
  Manim 是出**视频**不是出可内联图表，跟"HTML 报告里嵌入一个可交互图"这
  个需求形状不匹配，本轮不接，除非以后明确要"参数扫描动画视频"这种呈现
  形式，单独再评估。

## 2. schema 改动（`problem_state_schema.md` §Figures + `charting_generic_architecture.md` §2）

- 现有 6 种 kind（curve/scatter/error_bar/interval_highlight/heatmap/boxplot）
  全部不动。
- 新增第 7 种 kind：`interactive`。字段约定（**复用现有 series 结构，不另起
  一套数据格式**）：
  ```json
  {
    "kind": "interactive",
    "title": "可选",
    "backend": "plotly",
    "layout_3d": true,   // 可选：true 时按 3D 曲面/散点渲染，false/缺省按 2D
    "series": [
      {"name": "v0=30 (m/s)", "points": {"x": [...], "y": [...]}, "z": [可选, layout_3d=true 时需要]},
      {"name": "v0=60 (m/s)", "points": {...}, "z": [可选]},
      ...
    ],
    "switcher": {"label": "v0", "type": "buttons"}  // 可选：是否要一个 Updatemenu 在几组 series 间切换
  }
  ```
  - `series` 里每一条对应一组"已经算好的结果"，`switcher` 只是声明"这几条
    series 是可以互相切换看的"，脚本不重新算任何东西。
  - `backend` 目前只实现 `"plotly"`；如果以后要加 Bokeh/别的库，加一个新的
    `backend` 值，不影响现有静态 6 种 kind。
  - **跟现有静态 6 种 kind 的关系**：一张图只会是一种 kind（要么静态
    `curve`/`heatmap`/... 走现有 matplotlib 路径，要么 `interactive` 走
    Plotly 路径），不是"一张图同时两种"——如果同一份数据既想要静态版
    （打印/截图友好）又想要交互版（可点），就填两条不同 `figure_id` 的
    记录（一条 kind=curve，一条 kind=interactive，指向同一份 `points`），
    报告正文按需引用不同 `{{figure: <id>}}`，两条记录互不干扰。

## 3. 代码改动点（都是新增分支，不改任何现有 kind 的行为）

- `program-design/hooks/make_report_figures.py`：
  - `render_all()` 里加一个 `kind == "interactive"` 分支：不走
    `matplotlib`，走 `plotly`（新建 `import plotly.graph_objects`、
    `plotly.io`，跟现有 `import matplotlib` 并列，只有 `kind=="interactive"`
    时才真正用到 plotly，不影响纯静态任务不装 plotly 也能跑的情形——
    即 `import plotly` 要做成**惰性导入**，只在 interactive 分支里 import，
    避免把 plotly 变成所有静态任务的硬依赖）。
  - 交互式图的产物不是 `.png`/`.svg`，是一个 `<figure_id>.html` 片段
    （`plotly.io.to_html(..., include_plotlyjs="inline")` 的完整自包含 HTML），
    写进 `--out-dir` 下同目录；`--format` 参数对 interactive kind 无效
    （PNG/SVG 是静态格式，交互式只能是 HTML），需要跟 `trace_visualizer.py`
    的内联逻辑约定好"看文件后缀决定用 base64 img 还是直接内联 html 片段"。
  - 沿用现有"维度不一致/缺数据硬报错、不静默修补"的原则：interactive
    series 缺 `points.x`/`points.y`（或 `layout_3d=true` 时缺 `z`）跟现有
    kind 一样直接报错，不为交互图"放宽"数据完整性要求。
- `program-design/hooks/trace_visualizer.py`：
  - `--figures-dir` 的内联逻辑（现在只认 `.png`/`.svg` 走 base64 `<img>`）
    加一条：遇到 `.html` 文件（interactive kind 的产物）不转成 `<img>`，
    直接把该 HTML 片段里的 `<div id="...">` + `<script>` 主体抠出来内联进
    报告页面（Plotly `to_html` 产出的片段本身带完整 `<div>` + 闭合
    `<script>`，内联方式 = 直接把这段字符串插到 `{{figure: <id>}}` 占位符
    位置，不需要再包一层 `<img>`）；找不到文件时的"红色缺失占位框"兜底
    逻辑对 `.html` 文件同样适用（不能静默吞掉）。
- `program-design/hooks/requirements.txt`：加 `plotly>=5.0`（跟现有
  `matplotlib>=3.8` 那一段并列，注明"仅 kind=interactive 用到，静态 kind
  不需要装"）。
- `dev-notes/self-tests/03/charting_generic_architecture.md`：§2（schema）
  加第 7 种 kind 的字段说明；§8（"明确不做的事"）里"3D 交互曲面：故意不做"
  这一条**改成**"纯静态出图路径不做 3D 交互（保持克制），但 Node 2.7 的
  **可选 interactive kind 分支**（Plotly，本文件 §2 新增第 7 种 kind）
  明确支持 3D/可切换按钮，触发条件是'题目本身要求答案形状是交互式的'，
  不是'所有题默认做'；两条路径并存，静态路径默认，交互路径按需"。
  这一步是**放宽**措辞，不是删除原本"克制"的原则，防止后续 AI 读 schema
  时误以为"图表功能=只能是静态 matplotlib"。

## 4. 实测 demo（已跑通，证明不是纸上谈兵）

- `dev-notes/plotly_static_probe.py`：3D surface + 2D Updatemenu 两例，
  确认 `include_plotlyjs="inline"` 字节数（~4.8 MB）、无外部 JS 引用。
- `dev-notes/plotly_2025b_demo.py` / `plotly_2025b_demo.html`：用
  **真实的 2025B `problem_state.json` 里 `boundary_gate.monotonicity_sweep_v0`
  的 7 个 v0 值** 生成了一张真数据曲线 + 一张演示用 3D 曲面（曲面数据是
  粗网格演示值，**不是**重新解 ODE，demo 里已标注清楚），生成了 4.8 MB
  单文件 HTML，可直接双击打开验证 3D 旋转/按钮切换是否真的可交互。
- 这条 demo 跟 `physics-agent` 分支现有回归测试（合成数据 + 2025A/B 真实
  数据）是同一套数据源习惯（复用已有 `problem_state_*.json`，不新造数据），
  后续正式实现 `kind=interactive` 时，这个 demo 可以直接转成回归测试用例。

## 5. 明确不做（跟静态路径的克制边界保持一致）

- 不引入 Bokeh 作为第二条交互技术路线（等真的撞到 Plotly 表达不了的交互
  类型再说，不预先造两条并行路线）。
- 不把 `interactive`/`interactive_live` 变成每道题必选的 kind（保持 Node
  2.7 "可选节点"的定法不变，只是可选范围里多了一种 kind 可用，不是新增了
  一个必须做的节点）。

## 6. v1.1 补充（2026-10-09）：新增 `interactive_live` kind（调参实时重绘，GeoGebra 式）

用户 2026-10-09 明确反馈"按钮切换太low，要像 geogebra.org 那样调参数实时
改变图形"。本次据此新增第 8 种 figure kind `interactive_live`：

- **能做到什么**：一条 2D 曲线 y = f(x; p)，p 是 1~N 个用户可拖动滑块
  （参数），浏览器端**每次滑块 `input` 事件都重新算一遍 y 数组**（用
  内联 JS 镜像的那段闭式表达式），再 `Plotly.restyle()` 更新曲线 ——
  纯静态单文件 HTML，无服务器，无外部 CDN，无 Python 回调。
- **只对"闭式表达式"这类函数有效，不是通用的"调参重解 ODE"**：如果 y
  对参数的依赖本身需要重新数值积分/重新解方程才能拿到（不是"同一个
  闭式公式换个系数重跑一遍"），本 kind 表达不了，应该退回 `interactive`
  kind（预计算几组参数值 + 按钮切换）并在标题如实说明，不能用
  `interactive_live` 硬套一个其实没有真实重解语义的滑块。这条边界
  写进了 `make_report_figures.py` 的 `_render_interactive_live()` docstring
  + schema 的 `live_model_note` 字段（缺了会打 WARNING，不是硬报错，但
  明确要求写明这句话本身，跟"不静默掩盖"原则一致）。
- **实测的验证方法（不是只信口头承诺）**：demo 脚本
  `dev-notes/self-tests/03/figures_interactive_test/
  build_sasando_interactive_live.py` 里，把内联进最终 HTML 的那段
  `LIVE_FN` 用 Node.js 实际执行，跟 Python 端同一套闭式公式逐行逐点对比，
  最大偏差 = 0.0（浮点精度内一致）才算通过，这一步的验证脚本随 demo 一起
  留在该目录，任何人改 `js_function_body` 模板结构都应重跑这个对比，不是
  只信一次。
- **JS 沙箱边界（写在 docstring，刻意保持窄）**：`js_function_body` 是
  分析 agent 自己写的字符串，作用域被限制在"能读固定的 x 网格 + 声明的
  constants + 当前滑块值"这一个函数内，没有 DOM 访问、没有
  fetch/XMLHttpRequest、没有 eval、没有网络；不允许扩大成通用脚本环境。

`interactive` 和 `interactive_live` 两个 kind 输出形态相同（都是自包含
`.html` 片段，走 `trace_visualizer.py` 同一条内联路径，不需要额外区分），
但 schema 字段完全不同（前者是 `series`+可选 `switcher`，后者是
`x_data`+`params`+`js_function_body`），不共用一套数据格式。

## 7. v1.2 补充（2026-10-09）：`interactive_live` "不重解重模型"边界的性质澄清（学习记录，不新增 kind）

> 触发背景：用户 2026-10-09 提供了一份第三方自包含 HTML（
> `dev-notes/第三方数据/钢针侵彻仿真_V0.1_apfsds_fem_2d.html`，约 2191 行，
> 完整跑在浏览器端的 2D 显式 FEM 侵彻仿真器），要求"参考一下，学习其技术，
> 视情况融入我们的项目通用预案"。

- **§6 里"只做闭式重算、不重解 ODE/PDE"这条边界本身保持不变** —— 这条
  继续有效，继续写死在 `live_model_note` 字段 + `_render_interactive_live()`
  docstring 里，本轮**没有**改 schema 字段枚举、**没有**新增 figure kind、
  没有扩大 `js_function_body` 的 JS 沙箱边界（无 DOM/fetch/eval/网络）。
- 澄清的只是**这条边界的定性**：之前 §6 的措辞容易读成"浏览器做不到
  重数值求解"，其实是**"通用绘图管线不为某一道题的专用求解器去扩大
  自己"的范围选择**，不是浏览器技术上做不到。已逐段读完该参考文件，
  完整的技术拆解（可迁移的 6 条配方 + 明确不迁移的理由 + 将来若真需要
  该走什么流程）见
  `dev-notes/self-tests/03/figures_interactive_test/
  reference_fem_realtime_simulation_notes.md`（下称"FEM 借鉴笔记"），
  以及 `dev-notes/self-tests/03/charting_generic_architecture.md` 新增的
  §11（同一主题的简版对照说明）。
- **不采用的部分**：该参考文件的材料常数自声明"工程近似值，不作弹道鉴定
  依据"，按本项目"数据要有可核查来源、不静默"的原则，只学其工程实现
  手法，不把它报出的任何数值当已验证物理数据使用。
- **将来若某道题确实需要"能实时重解的重数值模型"**：按 FEM 借鉴笔记 §2
  第 3 点，应**单独立项评估**是否值得为那一类题目引入一个独立的、带
  自己依赖与沙箱边界的重型 figure 分支（类似该参考文件的形态），不是
  往现有这条"画已算好结果"的通用管线里硬塞重型求解器；那条分支如果
  立项，应另立 dev-note 走完整评审，不在本 §7 范围内预先承诺。
- **同步落地（本 §7 的配套动作，不是只澄清文档）**：基于这份参考文件里可通用的
  3 条交互模式，已经实际增强 `_render_interactive_live()`，全部是**可选**
  schema 字段、向后兼容，详见 `charting_generic_architecture.md` §11 同位置
  的完整说明（`y_range_pin` 钉死 y 轴量程、状态条三态外露、`verify_reference_*`
  可选独立参考值对照读数），以及 FEM 借鉴笔记 §3、§4 的完整验证记录。
