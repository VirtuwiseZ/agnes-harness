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

- **`kind` 现在共 6 种**（v2.1 修订，v2 初版 5 种，另加 `boxplot`）：
  前 5 种沿用 v2 的说明（`line_scatter` 拆成 `curve`（纯线）+
  `scatter`（纯点）两种，同一张图里可以混合；`heatmap` 是二维参数场，
  用 `pcolormesh`（热力图）或 `contourf`（等高线）渲染，同一个 `grid`
  字段两套画法，靠 `heatmap_style: "pcolormesh"|"contourf"` 一个可选
  开关切换，不做两套数据格式），外加 `boxplot`（类别×分布对比，每条
  `series` 是 `{name: 类别名, values: [该类别下的一组 y 值]}`，渲染走
  matplotlib 原生 `ax.boxplot()`，**不强依赖 seaborn**——seaborn 本身
  不画任何现有 kind，见下方"seaborn 的定位"条目）。
- **`heatmap` 的坐标轴可以是数值型或类别型（v2.1 补充，第三方数据测试中撞出）**：
  `grid` 的 `x_values`/`y_values` 不要求必须是数值——如果某一维（或两维）是
  字符串（如特征名、国家名、年份等类别标签），脚本自动检测并改用 `imshow`
  直接画矩阵+类别刻度标签（`pcolormesh`/`meshgrid` 遇到字符串会直接崩溃，
  这是本次 UCI Wine 特征名矩阵、OWID CO2 国家名×年份矩阵测试中实际撞出
  的真实缺陷，不是预防性设计）；如果两维都是数值，仍走原来的
  `pcolormesh`/`contourf` 路径，数值分支行为完全不变。
  **`heatmap_style:"contourf"` 只能用于两维都是数值的情况**（等高线插值
  需要坐标数值），如果对类别坐标轴指定了 `contourf`，脚本会直接报错
  而不是画错或静默降级。**仍然故意不做**：柱状图、饼图、3D 交互曲面、
  小提琴图、regplot 自动拟合、pairplot（跟初版一致，不因本次加
  `boxplot` 而改变"克制"的边界——`boxplot` 是类别×分布二维结构，
  不是把"克制"边界又往外扩）。
- **对数坐标轴（v2.1 新增，落地评估文档场景①）**：`axes.x.scale` /
  `axes.y.scale` 字段，取值 `"linear"`（默认，缺省等于这个）或 `"log"`，
  对全部 6 种 kind（含 `boxplot` 的 y 轴）生效。设计依据：跨 1 个以上
  数量级的物理量（dB 声压级、指数衰减、功率谱密度）在**坐标值本身**
  跨数量级时应改用对数坐标轴（本条），而不是对数**色标**（色标是
  heatmap 专属、应对"值域跨度大、少数大值压扁其余格点颜色区分度"
  这一不同症状的另一个独立特性，本次未加，见
  `charting_extension_scenarios_assessment.md` ①的完整评估——log
  坐标轴和 log 色标是两件事，不要混用）。**准确性底线**：数据里有
  0 或负值时 log 轴下无法绘制/无意义，本脚本不静默截断或跳过——会像
  NaN/Inf 一样加脚注说明"N 个值 ≤ 0，log 轴下无法绘制，已按
  matplotlib 默认行为处理，本脚本未擅自截断"，而不是假装这些点没
  出现。**类别坐标轴不允许 log**：类别值本身没有"数量级"概念，对类别
  轴指定 `scale:"log"` 会直接报错（跟"对类别轴指定 contourf 会报错"
  是同一类一致性校验），而不是静默忽略；`boxplot` 的 x 轴（类别位置）
  只有 linear 一种取值，指定 log 直接报错，只有 y 轴（实际数值）
  支持 log。
- **seaborn 的定位（v2.1 新增，仅为将来扩展预留的可选依赖，不是当前
  任何 kind 的必需项）**：seaborn 真正的增量价值是高层统计图（violinplot/
  regplot 的自动拟合+置信带、pairplot 等）。本次评估后确认：`regplot`
  的核心价值是"自动拟合+自动算置信区间"，而这恰是本项目"脚本不做
  物理判断"原则明确划给上游建模层（Node 2b）的活——拟合参数应由上游
  算好、脚本只负责画（现有 `curve` + `y_err` 风格的置信带数据已足够
  表达"拟合线+置信带"的呈现），所以 **regplot 不作为独立 kind 加入**；
  `violinplot` 偏小众（2-4 个条件、强调分布形状场景），暂不加；
  `pairplot` 属探索性分析工具而非报告主线结论图，暂不加。故本次
  `requirements.txt` 里 seaborn 只是"预留一行，装不装都不影响当前
  任何 kind 的正确性"，不是为了让某个现有/新增 kind 硬依赖它。

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

## 3. 新增脚本：`program-design/hooks/make_report_figures.py`（v2.1 已实现，见该文件本体）

> 注：本节的"规格"部分在 v2 定稿时脚本尚未实现；后续多个版本（v2.1，
> 类别轴支持、log 坐标轴、`boxplot` kind、脚注溢出自动收缩等）已直接落在
> `program-design/hooks/make_report_figures.py` 里，代码本体是现在的事实
> 基准，本节文字仅作历史规格记录，不保证与代码逐字同步。

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

## 9. v2.2 修订：新增可选交互分支（kind='interactive'，Plotly）——放宽"克制"边界，不是删除它

> 触发背景：用户（项目 owner）2026-10-08 明确——"报告绘图规则可以设计
> 多种选择，之前比较死板的原设计（静态 matplotlib 出图）可以松动成'按需
> 选择其他技术路线'，比如当用户的课题比较泛、一两张死图无法展现 AI 的科
> 研成果时，或者用户明确要求得到一定参数范围内的可交互科学图时，可以选
> 择更复杂专业的绘制技术。设计时注意先利用开源成熟的项目，避免重复造
> 轮子"。
>
> 本节据此新增；**不是**推翻 §8 的克制原则，是**在静态路径之外多一条
> 按需分支**——默认仍然是 §1-§7 的静态 matplotlib 路径（"克制"不变），
> 交互分支只在"题目本身要求答案形状是交互式的"这个信号出现时才用，跟
> Node 2.7 "可选节点"的定法完全一致（多一种可选的 kind，不是新增一个
> 必须做的节点）。

- **选型：Plotly（plotly>=5.0），不用 Bokeh**——理由见
  dev-notes/interactive_figure_design.md §1（已实测，不是猜测）：Plotly
  官方明确支持 to_html(include_plotlyjs="inline") 产出自包含、零外部
  依赖的 HTML 片段，跟本项目"绝对只读、静态、单文件 HTML 报告"原则的兼容
  成本最低；Bokeh 等价能力未实测，不预先开两条并行技术路线。
- **能做到的边界（实测确认，2026-10-08，Plotly 7.1.0）**：纯静态 HTML
  片段里，3D 可旋转/悬停/缩放；Updatemenu 按钮在**几组已经算好**的
  series 之间切换可见性（"参数扫描 + 展示层切换"）—— 实测字节数约
  4.8 MB（plotly.js 本体被内联，不是引用 CDN）。
- **做不到的边界（必须写死在 schema/docstring，防止后续误判为"能实现"）**：
  "拖滑块改某个物理参数 → 图实时重新解一次 ODE/重新算数值" 做不到——纯
  静态片段没有 Python 端回调路径，浏览器端没有重新解方程的机制。如果某
  道题"需要实时改参重算"级别的交互，不在本分支范围，需要引入 Bokeh
  server 或 Jupyter 级活体环境，属于完全不同的部署形态，不在"静态单文件
  报告"这个约束内讨论。
- **schema 改动**：§2 的 kind 枚举加第 7 种 interactive，新增可选字段
  backend（当前只实现 "plotly"）、layout_3d（bool，缺省 false）、
  switcher（可选：声明这几条 series 是可互相切换看的，加 Updatemenu
  按钮）；series 复用现有结构（name/points），layout_3d=true 时
  每条 series 额外需要 z 字段（跟 points.x/points.y 等长）。
  详见 dev-notes/interactive_figure_design.md §2。
- **代码改动点**：make_report_figures.py 加 _render_interactive()
  （惰性 import plotly，只有 kind=='interactive' 才真正用到，不影响
  纯静态任务不装 plotly 也能跑；产物是 <figure_id>.html 片段，不是
  .png/.svg）；trace_visualizer.py 的 --figures-dir 内联逻辑加
  一条分支：遇到 .html 文件（interactive kind 的产物）直接内联其
  div+script 主体，不套 img。详见 §3。
- **对既有静态 6 种 kind 的影响：零**——本分支是纯新增（新 kind 值 + 新
  函数 + 新依赖行 + 新渲染分支），不改动 curve/scatter/error_bar/
  interval_highlight/heatmap/boxplot 任何一条现有渲染路径的代码，
  跟 §1 第 3 条"判断权单一来源"的原则不冲突（判断"这道题要不要出交互图"
  仍然发生在 agent 填 numerical_artifacts.figures 那一步，脚本本身只做
  "照单画"，没有新增判断层）。


## 10. v2.3 修订：新增第 8 种 figure kind — `interactive_live`（调参实时重绘，GeoGebra 式）

> 触发背景：用户 2026-10-09 反馈 —— 之前 `interactive` kind 演示的按钮切换
> "太low"，真正想要的是"像 geogebra.org 那样能够让用户自己对一个函数、方程
> 调参数，实时改变图形的演示"。
>
> 核心结论（实测确认，不是猜测）：**纯静态 HTML 导出确实能做到"拖滑块 →
> 曲线实时重绘"，但只对一类函数有效：闭式表达式（closed-form）** —— 即曲线 y
> 对参数 p 的依赖是一次直接的代数/循环求值（比如"4 个阻尼洛伦兹峰的求和"
> 这种 O(n*modes) 浮点运算），而不是需要重新解一遍 ODE/PDE 才拿得到 y 的
> 数值模型。做法：把那个闭式表达式的数学结构原样镜像成一段内联 JavaScript，
> 浏览器端在滑块 'input' 事件里直接重新跑一遍这段 JS、拿到新的 y 数组，再调
> Plotly.restyle() 更新曲线 —— 全程无服务器、无外部 CDN、无 Python 回调，
> 纯静态单文件报告里就能实现。

- **跟 `interactive` kind 的区别（这是新分支存在的理由）**：
  `interactive` = 在**几组已经算好**的 series 之间切换（展示层切换，不算
  任何东西）；`interactive_live` = 一个滑块/几个滑块**实时重新求值**一条
  曲线（真正的"调参看图"，算的是同一个闭式表达式、不同的参数值）。两者输出
  形态相同（都是自包含 .html 片段，走 trace_visualizer.py 的同一条内联路径），
  但 schema 字段完全不同，不共用一套。
- **能做到的边界（写死在 schema 字段 `live_model_note` + 函数 docstring，
  防止误判为"什么都能实时重算"）**：只对"拖某个参数后 y 的变化是一次便宜的
  闭式重算"这种情况有效。如果某道题"调参 → 重解 ODE/PDE"才是拿 y 的真正
  方式，本 kind **不能**用来假装能实时重解 —— 那种需求应该退回
  `interactive` kind（预先扫几组参数值 + 按钮切换）并在标题里如实说明，
  而不是用 `interactive_live` 硬套一个其实没有真实重解语义的滑块。
  `live_model_note` 字段是**必填提示**（缺了会打 WARNING，不是硬报错，但
  要求写明这句话本身，跟"不静默掩盖"原则一致）。
- **安全边界（JS 沙箱，写在 docstring）**：`js_function_body` 是分析 agent
  自己写的字符串，作用域被限制在"能读固定的 x 网格 + 声明的 constants +
  当前滑块值"这一个函数内，没有 DOM 访问、没有 fetch/XMLHttpRequest、没有
  eval、没有网络。刻意保持窄，不扩大成通用脚本环境。
- **JS 数学正确性验证（本轮实际做过，不是口头承诺）**：2025A sasando demo
  （`dev-notes/self-tests/03/figures_interactive_test/
  build_sasando_interactive_live.py`）里，把内联进最终 HTML 的 `LIVE_FN` 用
  Node.js 实际执行，跟 Python 端同一套闭式公式（`h_db_py`，逐行对应同一套
  浮点运算顺序）在 zeta 全量程（0.001/0.005/0.02/0.05/0.15）上逐点对比，
  最大偏差 = 0.0 dB（浮点精度内一致），确认这段 JS 没有算错、跟 Python
  参考实现是同一套数学，不是两套。这一步验证脚本会随该 demo 一起留在
  `figures_interactive_test/` 下，后续任何人改 `js_function_body` 的模板
  结构都可以重跑这个对比，不是只信一次的口头保证。
- **对既有 7 种 kind 的影响：零** —— 纯新增（新 kind 值 + 新函数
  `_render_interactive_live()` + 新 dispatch 分支），不改任何现有静态
  6 种 kind、也不改 `interactive` kind 的代码路径。

## 11. v2.4 补充（2026-10-09）：`interactive_live` 边界的性质澄清（学习记录，不新增 kind）

> 触发背景：用户 2026-10-09 提供了一份第三方自包含 HTML（
> `dev-notes/第三方数据/钢针侵彻仿真_V0.1_apfsds_fem_2d.html`，约 2191 行，
> 一个完整跑在浏览器端的 2D 显式 FEM 侵彻仿真器），要求"参考一下，学习其
> 技术，视情况融入我们的项目通用预案"。已逐段读完该文件（材料库/网格/
> 求解器/诊断/WebGL 渲染/UI 主循环共 6 段），完整分析见
> `dev-notes/self-tests/03/figures_interactive_test/
> reference_fem_realtime_simulation_notes.md`（下称"FEM 借鉴笔记"）。
>
> 本节**不新增任何 figure kind、不改 `make_report_figures.py`、不改 schema
> 字段**，只澄清一条**已有**边界的性质，防止未来误读：

- **`interactive_live` kind 的"只做闭式重算、不重解 ODE/PDE"这条边界本身
  保持不变**（继续写死在 schema 的 `live_model_note` 字段 +
  `_render_interactive_live()` docstring 里，§10 的内容照旧有效）。
- 澄清的是**这条边界为什么这么定**，不是"该不该这么定"：之前（§10、
  `dev-notes/interactive_figure_design.md` §6）的措辞暗示"浏览器做不到
  重数值求解"，这次学习确认**这个说法不够准确 —— 这是范围/成本选择，
  不是浏览器技术做不到**。FEM 借鉴笔记 §1 列出了 6 条通用配方
  （每帧子步时间预算、精度/流畅度档位、手动单步 + 自动连跑并存、
  WebGL 优先 + Canvas2D 回退、便宜解析模型做量级对照、时间历史曲线
  随仿真滚动刷新），证明"静态单文件里跑一个真正的活体数值求解器"在
  原理上是通的，只是**不为某一道题的专用求解器去改通用绘图管线**是
  当前明确的范围选择（违反"克制/最小改动/不把 `js_function_body`
  作用域扩大成通用脚本环境"这条本项目一贯原则，见 §6/§10）。
- **不采用的部分**：该参考文件的材料常数（JC/EOS 参数）自声明"工程近似
  值，不作弹道鉴定依据"，本项目的数据可信度原则不接受把它当成已验证
  物理数据使用；只学"怎么实现"，不学"报出的数值"。
- **将来如果真遇到"某道题确实需要一个能实时重解的重数值模型"**：
  按 FEM 借鉴笔记 §2 第 3 点的建议，应**单独立项评估**是否值得为那一类
  题目引入一个**独立的、带自己依赖与沙箱边界的重型 figure 分支**（类似
  这次参考文件的形态），而不是往现在这条"画已算好结果"的通用管线里
  硬塞重型求解器 —— 那条独立分支如果立项，应另立 dev-note 走完整
  评审，不在本 §11 范围内预先承诺。
- **同步落地（本 §11 的配套动作，不是只澄清文档）**：基于这份参考文件里
  可通用的 3 条交互模式，已经实际增强 `make_report_figures.py` 的
  `_render_interactive_live()`，全部是**可选** schema 字段、向后兼容、不改动
  现有任何必填字段/现有 demo 的行为、不扩大 `js_function_body` 那套 JS
  沙箱边界（无 DOM/fetch/eval/网络）：
  - `y_range_pin`（[lo, hi]）：钉死 y 轴量程，避免 `Plotly.restyle()`
    每次滑块拖动都触发自动量程重算导致轴抖动（对应参考文件 `autoRange`
    时间平滑的通用化，用固定区间而非移动平均实现，因为我们是一维静态
    重绘不是逐帧滚动仿真）。
  - 状态条三态外露（正常/出错都显式可见，替换原有"只有出错才显示一行
    红字、平时完全空白"的单行报错框）：对应参考文件 `sim.done`/`reason`/
    `running` 的三态可见性思路，不改变"出错必须可见、不许静默"的既有
    原则，只是把正常状态也如实说出来。
  - `verify_reference_js`/`verify_reference_value`/`verify_reference_label`
    （可选）：允许 spec 带一个上游独立算好的参考值或 JS 表达式，JS 端实时
    显示"当前闭式结果网格均值 vs 独立参考值的偏差"，把上一轮已落地的
    "JS-vs-Python 数值正确性核对"从构建时一次性检查升级成读报告的人也能
    当场看到的常驻对照读数。JS 表达式若提供，同样受 `js_function_body`
    那套沙箱约束。详见 FEM 借鉴笔记 §3、§4 的完整验证记录（原有 base demo
    重跑确认未泄漏新逻辑；新增 `build_sasando_interactive_live_enhanced.py`
    + `check_enhanced_frag.cjs` 确认新字段就位、沙箱边界未被破坏、"零外部
    CDN"性质与改动前一致）。
- 本轮**不改**：`trace_visualizer.py`、`requirements.txt`（这三条增强不引入
  新依赖，全部复用已有的 plotly 惰性导入 + 标准库 json/re）。
