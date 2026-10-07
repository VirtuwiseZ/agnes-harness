# 反馈报告：physics-agent-governance SKILL 的 2025B Artillery 运行产物

> 面向开发者。本次运行按 SKILL 完整走完 6 节点流水线，产物（`report_2025B_artillery.md`、
> `research_report_2025B_artillery.html`、`problem_state_2025B_artillery.json`、trace JSONL）
> 均在 `program-design/runtime/`。以下 5 条反馈按严重度排序，每条含：现象 → 根因定位
> （具体到文件/函数）→ 建议修改。

---

## F1（高优先级）trace 交叉核验整列全 ⚠：`cross_check` 的匹配机制与"artifact_id 实际出现在哪里"脱节

**现象（用户报告 ②）**：HTML 里每个章节的"核验附证"板块，"trace 里是否找到对应调用"
一列全是 ⚠、"匹配到 seq"全是 "—"，即 15 条 traceability 声明全部核验失败。用户无法
据此确认 AI 到底做了什么，板块形同虚设。

**根因（已在 `trace_capture_converted_5f6ef764.jsonl` 上实证定位）**：

`trace_visualizer.py::cross_check()`（约 L183–197）的匹配方式是对每个 claim 做
**子串搜索**，搜索空间限定为：

```python
blob = json.dumps(c.get("args") or {}) + ((c.get("result") or {}).get("text") or "")
```

即：只搜 **tool/call 的 args + tool/result 的 result text**。
但本运行里，`problem_state.json` 的 `artifact_id`（sha256）是由
`audit_log.py::_artifact_id()` 计算的，**只出现在 agent 自己脚本的 stdout 里**——即
`tool/result` 事件 content 文本块中。实测：

```
c8399d1bd4e5d6ae in-call-args: 0  in-result-content: 1
0245adae2e665d11 in-call-args: 0  in-result-content: 1
2770455c4fdcf58b in-call-args: 0  in-result-content: 1
```

三个抽查的 artifact_id **全部**在 tool/result 的 content 里出现一次、在 args 里零次。
而 `cross_check` 的 result 侧只取 `result.text`（经 `_first_text()` 聚合）——
若 `_first_text` 聚合路径或 `extract_tool_calls` 的 result 装配与实际 JSONL 的
`data.content` 结构不一致（本 trace 里 result 的 content 块是
`[{type:"text", text:...}]`，聚合是对的，但 claim 匹配的是"整段文本里搜 8-hex
前缀"，而 result text 被截断/拼接后哈希前缀可能不在其中），整列就全 ⚠。
**无论哪种微因，机制性结论一致：artifact_id 是脚本输出的派生物，
它天然不会作为调用参数出现，纯子串匹配搜不到它是必然，不是意外。**

**建议修改**：
1. `cross_check` 增加第二匹配通道：把 claim 拆成 (a) 在 tool/result content 全文中
   搜完整/前缀哈希；(b) 语义匹配——claim 若是 artifact_id，反向取该
   `audit_log` 记录的 `source` 字段（如 `dimensional_gate_run`），
   去 trace 里搜"哪个 shell 调用跑了 `dimensional_gate.py`/`audit_log.py --source
   dimensional_gate_run`"，命中即 ✅ 并挂上那个 shell 调用的 seq。
2. 报告 md 里（Node 3 产出）的 artifact 引用，同时写 `source` 名 + 短哈希，
   让 HTML 的交叉表用户可读（"dimensional_gate_run · 0245ae…" 而非裸哈希）。
3. 加一个生成期自检：若 ⚠ 占比 100%，在 HTML 顶部打一条醒目的
   "cross-check 机制不可用"横幅，而不是让用户逐格解读 ⚠。

---

## F2（中优先级）"数据快照"板块标题与内容是给程序员的，物理用户看不懂（用户报告 ③）

**现象**：HTML 每章节下挂的 `<details>数据快照 — problem_state.json 中本节写入/更新的内容</details>`
直接 `json.dumps` 整个 `audit_logs`（截断 1500 字符）、`anomalies`、`verification`
原文贴出（`_state_snapshot_block()`，L480–499）。对"问火炮怎么打的人"，
看到的是 JSON 碎片，不知道这是"第 X 步留下的审计凭证"，更不知道和物理结论的对应关系。

**根因**：`_state_snapshot_block` 是纯机械渲染——dump 整文件、截断、完事。
SKILL 本身没有规定"快照板块要面向谁"，trace_visualizer 默认当成了开发者自检工具。

**建议修改**（二选一或叠加）：
1. 快照板块改为**人话摘要 + 原文折叠**：每节只列该节相关的 2–4 条
   （source 名 + 一句话解释，如 "dimensional_gate_run：4 条运动方程量纲校验全部通过"），
   完整 JSON 折到第二层 `<details>`。解释文案可由 Node 3 在报告 md 里以
   约定格式（如每节末尾 `> 审计凭证: source=..., 说明=...`）随文写出，
   HTML 直接渲染，不做机器翻译。
2. 或者干脆把"数据快照"板块默认从正文撤下，只保留在页尾"核验附证（汇总）"
   区一处，正文只留 F1 修好后的"核验附证"。现在的"每节两份折叠面板"
   对终端用户是噪音。

---

## F3（中优先级）报告语言：SKILL 未规定语言，本次英文是合理执行，但用户侧体验差（用户报告 ①）

**核实结果**：SKILL.md（`physics-agent-governance`）全文 **没有**任何"用中文汇报"
的条款；`problem_state_schema.md`、`data-source-routing.md` 等模板也都没有。
唯一涉及语言的是 trace_visualizer 的 HTML 壳（`<html lang='zh'>`、中文标题"物理研究汇报"、
板块名"核验附证/数据快照"都是中文），但正文叙事完全来自 agent 写的 Node 3 md。
SKILL 的 Node 3 规定只有一句"written **for the user**, in the user's language"——
"the user's language" 本应指**出题用户的语言**（本题用户是中文提问），
但措辞太弱，agent 完全可以合理理解为"我用什么语言都行，只要面向用户"。

**建议修改**：
1. SKILL.md Node 3 小节把"in the user's language"改成硬约束：
   "报告 md 的语言必须与用户对 agent 提问所用语言一致（本会话用户提问语言）"；
   若一次会话混合多语言提问，默认用最后一条提问的语言或让用户指定。
2. 同步改 `task_params_template.json` / `problem_state_template.json` 的
   `_note` 字段：补一句"task 描述与报告语言跟随用户提问语言"。
3. 给 agent 一个可审计的落点：在 `problem_state.json` 里加 `report_language`
   字段（Node 1 写），Node 3 写报告时声明所用语言，HTML 顶部 meta 区显示。

---

## F4（低优先级）报告只有文字表格，无图表（用户报告 ④）

**现象**：Node 3 报告与 HTML 全部是段落 + 简单列表；v0–theta 候选表、
miss(v0) 单调性、不同 R/风况下的 v0 需求这些**天然适合画图**的数据
（本次运行里都有：6 个角度候选点、7 点单调扫描、7 个泛化工况）
只以 markdown 表格形式存在，HTML 原样渲染为纯文本表格。

**根因**：`trace_visualizer.py` 的 md 渲染子集（`md_to_html_blocks` +
`_md_body_to_html`，L227–278）刻意只支持 段落/列表/加粗/code/pre，
**不支持表格、不支持图片**（md 里的 `|` 表格被当普通段落逐行包进 `<p>`，
HTML 里连表格边框都没有——这点比用户感知的"只有文字"更糟，建议顺带修）。
图表不是没数据，是渲染管线根本没这条通路。

**建议修改**（按投入产出排序）：
1. 最小改动：`_md_body_to_html` 增加 markdown 表格 → `<table>` 的解析
   （十几行），本次的 4 张表格立刻可读。
2. 图表本体：让 Node 3 在报告旁产出**自包含** SVG（agent 手写 SVG 路径，
   或 Python 端 `matplotlib` 存 `*_fig.svg` 再内联 `<img src="data:image/svg+xml;utf8,...">`），
   HTML 保持"零外部资源"约束不变。SKILL.md Node 3 加一条软约定：
   "数值结论章节尽量附一张对应的 SVG 轨迹/扫描图"。
3. （可选）在 trace_visualizer 里加一个"若同目录存在 `report_<slug>.svg`
   则内联"的识别逻辑，避免 agent 每次手写内联。

---

## F5（低优先级）HTML 在文件系统深处，用户需手动进文件管理器（用户报告 ⑤）

**现象**：产物路径是
`E:\agh-test3\program-design\runtime\research_report_2025B_artillery.html`。
AGH 聊天界面回复里，agent 只能输出这段路径字符串；用户要看到报告得：
打开文件管理器 → 逐层进 4 级目录 → 双击 html。

**建议修改**（按可行性排序）：
1. **会话内直链**：AGH 前端若支持在消息文本里把
   `file://`（或 AGH 自定义协议，如 `agh://artifact/<path>`）渲染为可点链接，
   则 SKILL.md Node 4 的"link the resulting HTML"一句应明确要求
   "以可点击链接形式给出，不只是路径字符串"。
2. **托管兜底**：若无直链机制，AGH 可提供一个"本会话产物"侧栏
   （列出本 session 内 write/edit 过的文件，可点即开/下载），
   SKILL.md 不感知、纯宿主能力。
3. **约定产物目录**：把报告 HTML 固定生成到一个浅层、易找的目录
   （如工作区根目录 `reports/<task-slug>.html`），并在回复中给出
   最短相对路径。改动点在 trace_visualizer 的默认 `--out` 参数
   （现在是 `research_report.html` 裸文件名，落哪取决于调用方 cwd，
   本次是 agent 自己传的 runtime/ 深层路径——SKILL.md Node 4 可加
   "默认输出到工作区根下 reports/ 目录"）。

---

## 附：本次运行中暴露的 1 个非 SKILL 问题（顺带报告）

- 开发侧 hook 健壮性：`audit_log.py` 的 `_acquire_lock` 使用
  `os.O_CREAT|os.O_EXCL` 但**不创建父目录**；运行中一次低级脚本错误
  （open-for-write 后读回自己）把 `problem_state.json` 截断成 0 字节，
  后续任何走 audit_log 的写入直接 FileNotFoundError。建议在
  `_acquire_lock`/`_write_state` 前加 `os.makedirs(dirname, exist_ok=True)`
  之类的防御，并在 SKILL.md §3 的 write-back-verification 小节补一条
  "写前先 `os.path.getsize` 确认非 0 字节；若为 0，视为状态文件损坏，
  走恢复流程而非继续 append"。（本次已恢复并作为 anomaly 记录在案，
  非静默处理。）

---

*报告生成：AGH session 5f6ef764-8685-4831-9489-c3744616b56a，
基于 2025B_Artillery 运行的实际产物与 trace 实证。*
