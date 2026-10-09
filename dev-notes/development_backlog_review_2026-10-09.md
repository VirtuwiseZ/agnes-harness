# 项目开发待办回顾（2026-10-09）

> 整理方法：不是凭印象列，是逐条对照 `git status --short`、最近 15 条 commit、
> `dev-notes/self-tests/02/commit_summaries_round2.md`、`dev-notes/self-tests/03/
> test3_report_charting_design.md`、`charting_extension_scenarios_assessment.md`、
> `test3_scientificity_vs_reference.md`、`.agh/skills/physics-agent-governance/
> SKILL.md` 里已有但未落地/未收尾的条目，一条一条归位；每条都标了"证据来源"，
> 没有证据来源的条目没有列进来（不猜）。
> 本轮（深挖 FEM 参考文件 + 落地 3 条 `interactive_live` 可选增强）已经做完、
> 不需要你再做的部分，只在末尾"已收尾"一节里一句话带过，不再混进待办里。

## 一、本轮（2026-10-09）之后仍未提交进 git 的改动（最紧迫）

`git status --short` 当前状态：

- `M .agh/skills/physics-agent-governance/SKILL.md`
- `M dev-notes/self-tests/03/charting_generic_architecture.md`
- `M "dev-notes/第三轮数据/figtest/test_heatmap_nasa_power.py"`
- `M program-design/hooks/make_report_figures.py`
- `M program-design/hooks/requirements.txt`
- `M program-design/hooks/trace_visualizer.py`
- `M program-design/parser_requirements.md`
- `M program-design/problem_state_schema.md`
- 另外一大片 `??`（untracked，未纳入 git）：
  - `dev-notes/interactive_figure_design.md`（含本轮新增的 §7）
  - `dev-notes/self-tests/03/figures_interactive_test/`（整个目录，含本轮新增的
    `reference_fem_realtime_simulation_notes.md`、`build_sasando_interactive_live.py`、
    `build_sasando_interactive_live_enhanced.py`、`check_enhanced_frag.cjs`、
    `problem_state_2025A_sasando_with_interactive_live_enhanced.json`、
    `sasando_live_enhanced_out/`）
  - `dev-notes/self-tests/03/` 下其余一批 `??`（`commit_assessment.py`、
    `commit_charting.py`、`commit_polish.py`、`commit_skill_fix.py` 这些"分门别类
    写好的 commit message 草稿脚本"本身也还是 untracked，尚未被真正执行/提交）
  - `dev-notes/self-tests/02/` 下一大批探针脚本 + `commit_summaries_round2.md`
    （见第二节）

**需要做的**：按约定（未经明确指示不 `git commit`/`git push`），这批改动一直
留着等你点名。建议至少拆成这几个逻辑上独立、可单独审阅的 commit（跟上面
`commit_*.py`/`commit_summaries_round2.md` 里已经写好的草稿对得上）：
1. `interactive`/`interactive_live` 两个新 figure kind + 相应 schema/SKILL 文档
   （`M make_report_figures.py`、`M requirements.txt`、`M trace_visualizer.py`、
   `M parser_requirements.md`、`M problem_state_schema.md`、
   `M .agh/skills/physics-agent-governance/SKILL.md`、
   `M charting_generic_architecture.md`、`?? interactive_figure_design.md`）
2. 本轮（第 1 节之外的补充）3 条 `interactive_live` 可选增强
   （`y_range_pin`/`verify_reference_*`/状态条三态）+ 3 份文档同步
   （`reference_fem_realtime_simulation_notes.md`、`charting_generic_architecture.md`
   §11、`interactive_figure_design.md` §7、SKILL.md §7 末段）—— 跟第 1 条其实
   都改的是同一批文件（`make_report_figures.py`/`problem_state_schema.md`/
   `SKILL.md`/两份 dev-note），如果希望"一次审阅一个逻辑改动"，建议把这两条
   合成一个 commit（都是 `interactive_live` 这条线的连续演进，拆开反而易读性
   更差），或者明确拆两个 commit 但都在同一次审阅窗口里。
3. 上一轮遗留、跟 `interactive` 这条线无关的独立改动：
   `M dev-notes/第三轮数据/figtest/test_heatmap_nasa_power.py`（heatmap 数据源
   扩展那一批 commit 之后又动过一次，需要确认这次改了什么、要不要单独一条
   `fix(test_heatmap_nasa_power)` 还是并进之前的 heatmap 扩展 commit）。

证据来源：`git status --short` 输出（本轮会话中已实际读取）+
`dev-notes/self-tests/03/commit_assessment.py`/`commit_charting.py`/
`commit_polish.py`/`commit_skill_fix.py` 四个"分门别类写好的 commit message
草稿"文件本身还都挂在 `??` 未提交状态。

## 二、`self-tests/02` 量纲门（dimensional_gate）修复线：草稿已写好，尚未提交

`dev-notes/self-tests/02/commit_summaries_round2.md` 里已经按"分门别类、单段
commit message、直接复制即可"的格式写好了 3 个 commit：

1. `fix(dimensional-gate)`：DIM_ALIAS 从 15 键扩到 60 余键 + 齐次性判定改成
   排序后量纲项做判定键（100% 稳定）+ SymPy Derivative 处理缺陷修复 + 测试
   从 4 个扩到 13 个全过（涉及 `program-design/hooks/dimensional_gate.py` +
   `dev-notes/self-tests/test_dimensional_gate.py`，两者均已 `M`/tracked）。
2. `chore(gitignore)`：补 `__pycache__/`、`*.pyc` 忽略规则 + 删掉本轮跑量纲门
   测试产生的 `program-design/hooks/__pycache__/` 整个目录。
3. `docs(self-tests)`：把走查 1 三件套迁入 `01/`，新增 `02/` 下完整的
   agent 真实产物 + 官方 trace 导出 + 完整性核验脚本 + §5 隔离核验证据 +
   量纲表检索提示词及两份 AI 答复与研判（全部 untracked，一次性 `git add`）。

这份文档还明确划了一条线：**"不进 git、仅保留在本地工作区"**——`02/` 目录下
约 20 个 `probe_*.py`、2 个 `repro_*.py`、若干一次性 diff/中间产物，按"开发
过程留痕、数量多、不适合作为长期维护的仓库内容"处理，不 `git add`；并明确
记录了一条可选的后续动作（"如果之后想把这些探针脚本也一并纳入 git……可以
单独再做一次性 `chore(self-tests): 归档量纲门修复全程探针脚本` 的 commit，但那
属于另一件事，这次先不做"）。

**需要做的**：确认 1/2/3 三条 commit 是否按草稿直接执行（目前仍是草稿，没执行）；
以及是否要做那句"另一件事"（把探针脚本也归档进 git）—— 目前文档里明确写的是
"先不做"，等你对这条单独点头。

证据来源：`commit_summaries_round2.md` 全文（本轮已读）+ `git status --short`
里 `dev-notes/self-tests/02/` 下大量 `?? probe_*.py`/`repro_*.py` 仍挂着。

## 三、图表功能扩展线（6 个候选场景，已评估未实现，等 5+2 种 kind 打磨完再挑）

`dev-notes/self-tests/03/charting_extension_scenarios_assessment.md`（107 行，
本轮已全文读取）评估了第三方反馈的 6 个未覆盖场景，按常见性/实现成本排好序：

1. **曲线族（参数化曲线扫一族）**：常见性高，建议是下一个要实现的扩展
   （比双 y 轴/茎图/极坐标都优先），但文档明确写"先等 5 种 kind 打磨完、真实
   数据验证过再动手"—— 这个"5 种 kind 打磨完"的节点本身尚未被明确宣布达成，
   目前 `make_report_figures.py` 已经扩展到 7 种 kind（`curve`/`scatter`/
   `error_bar`/`interval_highlight`/`heatmap` + 本轮之前的 `interactive` +
   本轮的 `interactive_live` 可选增强），**这条评估文档本身写的还是"5 种 kind"
   的旧口径，需要回头更新一句，标明当前实际是 7 种 kind、评估里"等 5 种打磨
   完"的触发条件现在是否已经满足/由谁确认已经满足了。**
2. **多子图（subplot）**：常见性高，且可以复用现有 kind 只需在 `render_all`
   外层加一层 dispatch，底层 5 种 kind 绘制代码不用改，风险低—— 同①一样
   排在下一个实现批次。
3. **对数坐标**：常见性中，实现成本低但需要跟"数据里有 0/负值时 log 轴会崩"
   这个准确性细节一起设计，不适合单独抢跑，等 ①② 做完后一并处理。
4. **双 y 轴**：常见性中低，且和多子图功能重叠，建议先做 ②（子图），真正
   撞见"必须同轴对比"的题再补，不预先开发。
5. **频谱图 / 极坐标**：常见性低，不需要提前开发，撞到再评估。

**需要做的**：确认"①②（曲线族 + 多子图）是否要现在进入实现"，还是继续等
下一批真实题目撞到再动手；以及回头把这份评估文档里"5 种 kind"的口径更新为
当前实际的 7 种 kind（`interactive`/`interactive_live` 两个新 kind 出现后，
"曲线族该排在多子图前面/后面"这个相对优先级是否仍成立，值得顺手核对一遍，
因为"曲线族"和"interactive_live 的参数扫描滑块"在概念上已经有一部分功能
重叠——滑块扫一个参数、实时重画一族曲线，跟"曲线族（参数化曲线扫一个参数、
颜色随参数连续变化）"这个静态 kind 是**两回事**（一个是交互操作、一个是纯
静态出图），但两者的触发场景（"扫一个参数看一族曲线"）有重叠，值得在文档里
记一句，避免以后实现时重复发明。

证据来源：`charting_extension_scenarios_assessment.md` §结论/§尚未实现的原因
（本轮已全文读取）。

## 四、`test3_report_charting_design.md` §5 "待你拍板" 的 4 件事，是否已经拍板

这份文档（139 行，本轮已全文读取）是 `make_report_figures.py` 最早的设计评估，
§5 列了 4 件"都还没动手"、等你确认的事：

1. 方案 2（`make_report_figures.py` + `trace_visualizer.py` 加最小 SVG 内联
   规则）vs 方案 4（交互式 JS 渲染）—— 目前看 `make_report_figures.py` 已经
   实际存在（commit `fc20d04a`），并且后续已经演进出 `interactive`/
   `interactive_live` 两个带 JS 的 kind，**这条实际上已经朝着方案 4 的方向
   走了很远**（`interactive`/`interactive_live` 就是"报告正文写数据，HTML 侧
   用 JavaScript 现场画图"这条路，虽然用的库是内置的 `plotly` 内联而不是
   Chart.js/Plotly.js CDN，仍然符合"零外部 CDN、自包含单文件"的约束）——
   需要在文档里把"方案 2 vs 方案 4 二选一"这条过时的待办更新为"实际走了
   一条方案 2 和方案 4 的混合：静态 kind 走 SVG/PNG（`trace_visualizer.py`
   内联），交互 kind（`interactive`/`interactive_live`）走内联 Plotly.js"，
   而不是继续挂着"还没拍板"。
2. 2025B 那张"三条典型弹道叠图"要不要做（需要补跑一次
   `artillery_model.py` 存下 x(t)/z(t) 采样点，是唯一需要补跑脚本才能拿到
   画图数据的点）—— 目前 `problem_state_2025B_artillery.json`（本轮已读）里
   **没有**存轨迹采样点，这条仍然挂着未做。
3. 2025A 那组"Lorentzian 多峰叠加图"/"EQ 曲线图"要不要做—— 文档已确认
   `ei_curve_sample_dB` 12 点数据全部现成、不需要补跑，只剩"要不要画"这一个
   决定—— 这条是否已经做过，目前会话里没有证据表明已经画过。
4. 上面 3 项都确认后，重跑 2025A/2025B 两份报告渲染，出"带图版" HTML 对照
   看效果，再单独确认"要不要推广到以后所有题目的报告"—— 目前没有证据表明
   这一步也做过。

**需要做的**：逐条确认 1/2/3/4 当前的真实状态（1 大概率已经隐含推进了，需要
回头在文档里更新口径；2/3/4 目前是明确未做的，需要你点名要不要做）。

## 五、`test3_scientificity_vs_reference.md` §4 的 4 个"改进项"，尚未落地

这份文档（200 行，本轮读取了末尾部分）§4 列了 4 条"下一轮做"的改进项，目前
没有证据表明已经做完：

1. 把叶振膜模态频率（211.84/686.57/1430.96/2446.11 Hz）和 70 cm 封闭管驻波
   公式（`f = n·v/(4L)`，奇数谐波）单独算的 245/490/735/980 Hz 这 4 个峰
   **放进同一张图/同一个表里对比**（目前两套数字各说各话，没人把它们放到
   一起看过）。
2. 火炮题的 `verification` 字段里，把"线性偏差系数 vs 完整 ODE 解"作为第二
   道独立验证通道记录下来（跟现有的"真空公式+一阶修正"并列），把
   `verification.benchmark_source` 从单一线扩展成双线索。
3. （这条其实是第 1 条的另一个表述，文档里编号有点重复，实际是同一件事的
   两种说法，整理时应该合并成一条。）
4. （协议层面）`verification.benchmark_source` 扩展成双线索这件事本身。

**需要做的**：确认这 4 条（实际是 3 件不重复的事）是否要在下一轮做、还是
继续挂着；以及把文档里"1 和 3 是同一件事"这个编号重复的问题顺手理顺。

证据来源：`test3_scientificity_vs_reference.md` §4（本轮读取了第 180–199 行，
4 条改进项 + 原文编号 1/2/3/4 中 1 和 3 实质重复）。

## 六、SKILL.md / 两份 dev-note 的口径同步（本轮已经做了，列在这里只是提醒
"这些同步本身是否已经足够、还是还要再补一处"）

本轮已经把 3 条 `interactive_live` 可选增强的事实同步进了：
- `.agh/skills/physics-agent-governance/SKILL.md` §7（`interactive_live` 段落
  末尾追加了一段较长的说明，含 3 条增强 + 验证记录）
- `dev-notes/self-tests/03/charting_generic_architecture.md` §11（同位置追加）
- `dev-notes/interactive_figure_design.md` §7（同位置追加，更精简版本）
- `dev-notes/self-tests/03/figures_interactive_test/
  reference_fem_realtime_simulation_notes.md` §3/§4（完整版拆解 + 验证记录）

**待确认**：SKILL.md 这段追加的文字已经比较长了（一段话里嵌了 3 条增强 +
验证细节），是否要再压缩/或者干脆只在 SKILL.md 里留一句"详见 FEM 借鉴笔记
§3/§4"、把细节全部推到 dev-note 里，避免 SKILL.md（每次 LLM 都会读到的一份
"路由协议"文档）持续膨胀—— 这是一条纯"该不该再精简一下"的自查项，不影响
正确性，只是可维护性权衡。

## 七、已收尾、不再列进待办的部分（本轮实际完成）

- `make_report_figures.py` 的 `_render_interactive_live()` 新增 3 条可选增强
  （`y_range_pin`/`verify_reference_js`/`verify_reference_value`/
  `verify_reference_label` + 状态条三态外露），`ast.parse` 通过，无语法错误。
- 原有 base demo（`build_sasando_interactive_live.py`，不带新字段）重跑，行为/
  输出与改动前一致（未泄漏新逻辑）。
- 新增 `build_sasando_interactive_live_enhanced.py` + `check_enhanced_frag.cjs`，
  实际带新字段跑通，确认 HTML 片段里 `PIN_LO`/`Plotly.relayout`/`VERIFY_FN`/
  状态条 div 全部就位、注入的 JS 块内无 `fetch(`/`XMLHttpRequest`/`eval(`、
  "零外部 CDN"性质与改动前一致。
- `problem_state_schema.md` Figures 子 schema 追加"Optional enhancement fields"
  说明。
- 上表第六节列出的 4 处文档同步，全部完成。

## 汇总（一张清单，按紧急/重要程度排）

1. 【紧急·纯执行】第一节的 commit 拆分/执行（等你对"要不要现在提交"点名，
   以及"3 条增强和 §1 基础 `interactive`/`interactive_live` 是合一个 commit
   还是拆两个"的选择）。
2. 【紧急·纯执行】第二节 3 条 `self-tests/02` 草稿 commit 是否照单执行 +
   那句"探针脚本归档"的"另一件事"要不要单独做。
3. 【待决策】第三节 曲线族/多子图是否现在进入实现（还是继续等真实题目撞到）。
4. 【待决策】第四节 `test3_report_charting_design.md` §5 的 4 件"待拍板"事，
   逐条确认当前真实状态（第 1 条大概率需要更新文档口径，其余 3 条目前是未做）。
5. 【待决策】第五节 `test3_scientificity_vs_reference.md` §4 的 3 件不重复的
   改进项（含那条编号重复问题），是否下一轮做。
6. 【自查·非阻塞】第六节 SKILL.md 是否要再压缩一段。
