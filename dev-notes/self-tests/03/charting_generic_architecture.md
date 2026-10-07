# 通用图表呈现层：架构设计与指令规范（v2）

> 目标：给"报告里呈现数据"这件事定一套**通用、题目无关**的机制。2025A/2025B 只作为
> **试运行数据源**用一次，验证通用机制本身跑通，不为这两道题做专门设计。
>
> 本版本（v2）在初版基础上做了两处实质修订：
> 1. 绘图后端从"手写 SVG 字符串"改为"matplotlib（默认）+ 手写 SVG（备选）"。
> 2. 新增 kind：`error_bar`（误差棒）和 `heatmap`（二维参数场：热力图/等高线）；
>    暂不做柱状图、饼图、3D 交互曲面（初版结论不变）。

## 1. 设计原则（跟题目无关的部分，先立住）

1. **数据源永远是 `problem_state.json` 的 `numerical_artifacts` 字段**，绘图脚本不
   读模型 `.py` 文件、不碰 `report_<slug>.md` 正文里的文字描述——也就是说"AI 判断该
   画什么图、图里有什么数据"这件事，**必须先把数据落成 `numerical_artifacts` 里一个
   结构化的、通用的数据块，再交给绘图脚本**，不是让绘图脚本自己从散落的字段里
   "猜"。这是跟"量纲门/边界门只读确定性字段、不读自由文本"同一个精神。
2. **绘图脚本本身不认识任何物理量**（不知道 `v0` 是什么、`f_Hz` 是什么）——它只认
   通用的数据块 schema（见 §2），只描述"这张图有几条曲线/散点/误差棒/区间高亮/
   二维网格、横纵轴各自叫什么名字"这些**纯呈现事实**，不做任何"这个数是多少是
   物理上对的"判断。
3. **判断权分配（v2 修订，初版是"全部定死在 schema 里"，现在改为"主路径+确定性
   兜底层"，判断权只发生在 agent 填 schema 这一步，脚本本身零判断）**：
   - **主路径（agent 负责）**：写 `numerical_artifacts.figures` 时，agent 必须为
     每条 `series` 指定 `kind_hint`（line/scatter/line+scatter 混合）和 `x`/`y`
     数据，以及 `series.name`（图例名字，**约定写成"物理量+单位"的字符串**，如
     `"v0 (m/s)"`、`"f (Hz)"`——这个约定是主路径里唯一的"硬性格式要求"，因为
     脚本要用它做下面兜底层的轴标签取值，不是审美要求，是功能要求）。
   - **兜底层（脚本内置，纯确定性规则，不是 AI 判断）**：
     * 缺 `axes.x.label` / `axes.y.label`：直接取第一条 `series.name`（x 轴）
       和唯一 y 轴系列的 `name`（y 轴）作为轴标签——因为 `series.name` 约定
       里已经写了单位，这一步不需要"推断"，是**照约定取值**，无歧义。
     * 缺 `title`：留空，渲染成"（无标题）"占位，**不猜**。
     * `series` 里 `x`/`y` 长度不一致：直接报错，不画这张图，报给上游（这是
       数据完整性问题，不是绘图脚本该"修"的问题——跟量纲门/边界门"发现不对
       就拦下来"的精神一致）。
     * 出现 `NaN`/`Inf`：matplotlib 本身能画（会自动跳过/截断），脚本**额外**
       在生成的图下方加一行脚注"本图 N 个数据点为 NaN/Inf，已按 matplotlib
       默认行为处理（跳过/截断），未做物理层面的判断"——**只标注，不掩盖、
       不自己"修"成有限值**，跟项目"不许静默 paper over"的原则一致。
   - **没有第三层"AI 在调用绘图脚本时再做一次判断"的设计**——图型/数据点/
     series 角色这些判断全部发生在写 schema 那一步（agent 做的），脚本层面
     **只有上面列出的、写死在代码里的确定性兜底规则**（缺 label 就照约定取
     series.name，缺 title 就留空，维度不对就报错），不让脚本也"判断"一遍：
     脚本再判断一遍，出问题排查路径比"翻一下 schema 里 agent 当时填的是什么"
     要绕，且跟"判断权单一来源"的原则冲突。
4. **图是报告正文（Node 3 markdown）里显式引用的，不是自动塞进去的**——绘图
   脚本生成一批**图片文件（默认 PNG，v2 从初版的 SVG 改为 PNG，理由见 §3）**
   放在固定目录下，报告正文里用统一的、简单的引用语法（见 §4）指向这些文件，
   `trace_visualizer.py` 只负责"把被引用的图片按 base64 内联进 HTML"，不做
   任何"这张图配不配这个章节"的判断——判断"哪张图放在哪一段"这件事，仍然是
   Node 3 写报告时 AI 自己按题面组织出来的，通用机制不替 AI 做这个决定。

## 2. 通用数据块 schema（`numerical_artifacts` 里要新约定的一种块，v2）

任何一道题，只要想让报告里出现一张图，就在 `numerical_artifacts` 下加一个
`figures` 字段（可以是对象，每张图一个 key，值是下面这个结构）：

```json
{
  "figures": {
    "<figure_id>": {
      "kind": "curve" | "scatter" | "error_bar" | "interval_highlight" | "heatmap",
      "title": "可选：一句话图注（缺了按 §1 兜底层规则处理，不猜）",
      "axes": {
        "x": {"label": "可选（缺了按 §1 兜底层规则取）", "unit": "可选"},
        "y": {"label": "可选", "unit": "可选"},
        "z": {"label": "仅 kind=heatmap 需要：颜色轴/网格第三维名字", "unit": "可选"}
      },
      "series": [
        {
          "name": "图例名字，约定写成'物理量+单位'字符串（如 v0 (m/s)）",
          "role": "可选：'theory'|'experiment'|'simulation'|'residual'|'fit'",
          "kind_hint": "可选：这条 series 单独是 'line'/'scatter'/'line_scatter'",
          "points": {"x": [...], "y": [...]},
          "y_err": "可选：kind=error_bar 或单独带误差棒时给，与 y 等长",
          "grid": "仅 kind=heatmap：{'x_values': [...], 'y_values': [...], 'values_2d': [[...],[...]]}"
        }
      ],
      "highlights": [{"x0": ..., "x1": ..., "label": "可选：这段区间叫什么"}],
      "markers": [{"x": ..., "y": ..., "label": "可选：这个点叫什么"}]
    }
  }
}
```

- **`kind` 现在共 5 种**（v2 修订，初版只有 `line_scatter`+`interval_highlight`
  两种）：`curve`/`scatter`/`error_bar`/`interval_highlight`（沿用初版的
  `line_scatter` 拆成 `curve`（纯线）+`scatter`（纯点）两种，同一张图里可以
  混合——比如"散点+拟合线"就是两条 series，一条 `kind_hint=scatter`、一条
  `kind_hint=line`，不需要单独开一种"混合 kind"）和 `heatmap`（二维参数场，
  用 `pcolormesh`（热力图）或 `contourf`（等高线）渲染，同一个 `grid` 字段
  两套画法，靠 `heatmap_style: "pcolormesh"|"contourf"` 一个可选开关切换，
  不做两套数据格式）。**仍然故意不做**：柱状图、饼图、3D 交互曲面（跟初版
  一致，不因这次加 `heatmap` 而改变"克制"的边界——`heatmap` 是二维平面
  投影，不是 3D 交互物，不冲突）。
- **`role` 字段（v2 新增）**：给"理论值/实验值/仿真值/残差"这套科研里最常见
  的对照关系一个轻量语义标记。**这只是标签，不是"让脚本自动算残差"的指令**
  ——残差值本身仍然是上游建模 agent 算好之后，作为一条普通 `series`
  （`role:"residual"`，`points` 是算好的残差数组）填进来的；`role` 只让渲染层
  可以用不同的默认线型/颜色惯例区分它们（如残差默认画灰色虚线），不改变任何
  数值本身——跟 §1 第 3 条"脚本零判断"的原则一致，不是新增一层判断，只是
  多一层"照标签套默认样式"的机械映射。
- `highlights`/`markers`/数值本身"该不该进这张图"的判断，沿用初版规则：
  决定"哪些点放进 `series.points`"是上游建模 agent 的责任，不是绘图脚本
  的；脚本拿到什么点就画什么点。

## 3. 新增脚本：`program-design/hooks/make_report_figures.py`（规格，未写代码，v2）

- 读入：`--state problem_state_<slug>.json`（只读 `numerical_artifacts.figures`
  这一个字段，别的字段一律不读）
- 输出：`--out-dir` 下每张图一个 `<figure_id>.png`（**v2 从初版的 `.svg` 改为
  `.png`**，理由：matplotlib 出 PNG 是一行 `savefig()`，出 SVG 需要额外关掉
  一部分默认样式才不出"matplotlib 风格泄漏"，PNG 没有这个问题；且下游
  `trace_visualizer.py` 内联进 HTML 用的是 base64，PNG 通常比带全套内嵌
  样式的 SVG 更小、更不容易撞到"某个浏览器渲染 SVG 有 bug"的兼容性问题。
  如果某张图确实需要矢量清晰度（要打印放大），可以单独为那张图开
  `--format svg`，脚本支持两种格式，默认 PNG。）
- 绘图后端：**matplotlib 为默认**（折线/散点/误差棒/区间高亮/热力图/等高线
  全部用现成 API 一行搞定，不再手写 SVG）；**手写 SVG 字符串作为备选**，
  仅当某张图需要精确到像素级控制时才用，不再是"唯一路径"（初版的决定，
  v2 已按本次确认的方向改为 matplotlib 优先）。
- 健壮性检查（§1 第 3 条兜底层列的那些）：维度不一致直接报错、不画；
  NaN/Inf 加脚注不掩盖；缺 label/title 按约定兜底，不猜。
- **不**做任何单位换算/量纲检查（那是量纲门的活）；**不**判断"这个数值物理
  上对不对"（那是建模+验证层的活）——这条边界不因 v2 加新 kind 而改变。

（本次任务范围：先把这份规格写完并跟你对齐，不立即写脚本代码——脚本代码本身
  属于"实现层"，等你确认 v2 这套通用架构本身没问题后再动手写，不抢跑。）

## 4. 报告正文里引用图的统一语法（Node 3 写 `report_<slug>.md` 时要遵守）

固定成一种、最简单的形式，不引入"图注要单独写在哪"这种复杂约定：

```
{{figure: <figure_id>}}
```

（一行、单独成行、跟 `figure_id` 精确对应 `numerical_artifacts.figures` 里的
哪个 key；图注文字写在 `figures.<figure_id>.title` 里，不在报告正文里重复写一遍，
避免两处不一致。）

`trace_visualizer.py` 需要的小改动（沿用初版描述，只是"SVG 文件名"改成
"PNG/SVG 文件名，看 `make_report_figures.py` 实际产的是哪种"，其余不变）：
- `_md_body_to_html` 里遇到 `{{figure: xxx}}` 这一行，不转成 `<p>`，转成一个
  `<figure>` 占位符（带 `data-figure-id` 属性）
- 新增一个 `--figures-dir` 参数（指向 `make_report_figures.py` 的输出目录）；渲染时
  把占位符替换成"读该目录下对应 `<figure_id>.png`（或 `.svg`，看实际产的是哪种）
  的 base64，内联进 `<img src="data:image/png;base64,...">`，下方跟一行小字图注
  （来自 `figures.<figure_id>.title`，缺了显示"（无标题）"）"
- 如果报告里引用了某个 `figure_id`，但 `--figures-dir` 下找不到对应图片文件，
  **不静默吞掉**：在最终 HTML 里渲染成一个醒目的、明确写着"引用了
  `<figure_id>` 但找不到对应文件"的占位框（跟项目"不许静默 paper over"
  的原则一致，具体做法：渲染成带红边框的 `<div>`，里面写清楚"哪个图缺失"，不
  假装这张图存在）

## 5. SKILL 需要新增/改动的一小段（通用规则，跟题目无关）

在 `physics-agent-governance` SKILL 里加一条，位置放在 Node 2b 和 Node 3 之间
（因为"要不要在报告里画图、画哪些图"的判断，逻辑上发生在"Node 2b 数值结果已经
出来、Node 3 开始组织报告"这个时间点）：

> **Node 2.7（可选，题目相关）— 数值结果图表化**：如果这道题的数值结果适合
> 用曲线/散点/区间图呈现（例如：某个关键量随另一个关键量的变化关系、某个验证
> 扫描的单调性曲线、某个理论频率/振幅落在题面给定区间内外的位置关系），在
> `problem_state.json` 的 `numerical_artifacts` 下新增 `figures` 字段（schema 见
> `make_report_figures.py` 的 docstring，跟题目无关的通用结构），把要呈现的
> 每条曲线/每个高亮区间/每个标注点，按 §2 的通用 schema 填进去——**填的是
> "这些点画成图之后长什么样"这个呈现事实，不是"这些点物理上对不对"（那是
> 量纲门/边界门已经负责过的事，不在这里重复判断）**。然后在 Node 3 写报告
> 正文时，用 `{{figure: <figure_id>}}` 语法（§4）引用你刚才填的每张图。如果
> 这道题的数值结果**不适合**画图（例如：只有一个离散的最优解、没有"曲线"这个
> 概念，或者整个分析过程没有产生任何"一个量随另一个量变化"的结构化数据），
> **不要强行造一张图**——`figures` 字段可以为空/不存在，报告正文里就不用
> `{{figure:...}}`，这是允许的，不是遗漏。

（这条规则的关键：是**可选节点**，不是"每道题都必须画图"的强制节点——跟
  `test3_report_charting_design.md` §5 第 4 项"要不要推广成协议固定环节需要单独
  确认"的边界一致，本次只是定"如果要画图，通用做法是什么"，没有定"以后每道题
  都要画图"。）

## 6. 试运行范围（用 2025 两份现成 `problem_state.json`，但不做任何题目专属的
图设计）

按上面这套通用机制，2025A/2025B 两份 `problem_state.json` 里**已经现成存在的**
字段，能直接填进 §2 通用 schema 的有：

- **2025B**：`all_angle_candidates`（θ vs v0，6 个点，1 条曲线）；
  `boundary_gate.monotonicity_sweep_v0`（v0 vs miss，7 个点，1 条曲线）；
  `generalization_sweep`（7 组不同 R/高度/风 的 v0，可以画成"不同环境变量下的
  v0 对比散点"，1 组散点）——这三块**已经现成**，直接照 schema 填进
  `numerical_artifacts.figures`，跑一遍 `make_report_figures.py`（先写出来这个
  脚本，这是本次唯一要新增的代码）+ `trace_visualizer.py` 那条小改动，看
  2025B 报告 HTML 里能不能正确出这 3 张图。
- **2025A**：`headline_eigenfrequencies.f_all_modes_Hz`（4 个模态频率散点 +
  98–1047 Hz 区间高亮，`kind=interval_highlight`，叠加一组散点）；
  `ei_curve_sample_dB`（12 点 EQ 曲线，`kind=curve`）——这两块
  也已经现成，同样直接填 schema，不出任何 2025 专属的"竹管驻波对照图"（那个
  要另外补跑计算，超出本次"用现成数据做通用机制试运行"的范围，不做）。

**本次明确不做的事**：
- 不设计"2025B 弹道叠图"（需要补跑 `simulate()` 存采样点，超出"用现成数据"范围）
- 不设计"2025A 竹管驻波 vs 叶振膜模态对照图"（需要补跑竹管驻波计算，超出范围）
- 不写"哪张图该放在报告哪一段"的固定规则（这是 Node 3 写报告时 AI 自己判断的
  事，通用机制只提供 `{{figure: xxx}}` 这个引用语法，不替 AI 排章节）

## 7. 待拍板/待定（v2 修订后，初版 §7 的第 1 项已解决——误差棒已加入；
第 2、3 项原样保留，不重复列）

1. ~~§2 要不要加"误差棒" kind~~ → 已定：加（本次 v2 修订，同时加了 `heatmap`
   和 `role` 字段）。
2. **动手顺序确认**：先写 `make_report_figures.py`（含 `error_bar`/
   `heatmap` 两条新渲染路径）+ `trace_visualizer.py` 那条小改动，
   拿 2025A/2025B 现成数据试跑初版那 5 张（`curve`/`scatter`/
   `interval_highlight`），再单独造一张合成数据测试 `error_bar`/
   `heatmap` 两条新路径，两步分开做，不把新 kind 硬塞进 2025 报告里
   当"已经支持了"来演示。
3. **要不要把"figures/绘图"正式写进 `physics-agent-governance` SKILL 作为
   长期可选协议节点（Node 2.7）**（初版 §7 第 3 项，原样保留，不因本次
   修订改变"需要单独确认"的边界）。

## 8. 本次 v2 修订明确不做的事（跟初版一致，不因加了新 kind 而扩大范围）

- 不给 2025A/2025B 补跑任何模型计算（2025B 弹道叠图、2025A 竹管驻波对照图
  仍不在本次范围）。
- `error_bar`/`heatmap` 两条新渲染路径，本次只用合成数据验证"跑得通"，
  不用任何 2025 真实数据硬凑（2025 两份 `problem_state.json` 里没有天然
  对应的误差棒/二维参数场数据，硬造出来演示不是"支持了"的证据，是
  造假）。
- 不把"figures/绘图"升级为每道题强制节点（仍是 Node 2.7 可选节点，§7
  第 3 项待单独确认）。
