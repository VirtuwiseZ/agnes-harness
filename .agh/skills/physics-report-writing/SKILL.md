---
name: physics-report-writing
description: 每个 pipeline 节点（Node 1/1.5/2a/2b）结束时都要增量追加一段写给用户的 markdown 汇报；Node 3 收尾阶段把所有增量段整合成完整研究汇报。触发信号是"该写/该更新这次分析的用户可见汇报了"，不是建模/求解本身。
---

> **③第 1 点定稿（10/12）**：`physics-agent/knowledge/report_structure_guide.md` 已新增 3 条约束（第 4/5/6 条，跟原有 3 条并列，该 guide 标题已从"三条约束"改为"六条约束"）——
> 4. 公式必须用 LaTeX 定界符（`$...$` 行内、`$$...$$` 行间），不使用 Unicode 上下标字符冒充公式排版；
> 5. 数据表格必须用真实 markdown 管道语法（`|` 分隔 + 表头下方一行分表线），不允许把表格数据写成普通文本行冒充表格；
> 6. 小节标题不带元注释/自我评价式括号（"本轮说明"之类集中放在报告开头一段说一次，不在各节标题里重复）。
>
> 这三条跟原有第 1/2/3 条（结论先行 / 假设显式化 / 验证独立于建模）构成 Node 3 撰写报告时行文层面的完整约束集，Node 4（HTML 渲染）侧的配套改动（KaTeX 公式渲染、markdown 管道表格渲染）见 `physics-report-charting` 子 skill（③第 2 点），两侧要同步改、同步验收，不能只改一侧。

**当前范围（不占位、已稳定）**：Node 3（Research Report, incremental）这一段的职责划分——"什么时候该追加汇报、追加什么、怎么在收尾时整合"——这个是稳定的协议级划分，不受③第 1 点影响，下面照搬原文，不改动。

**Node 3 原文（不占位，逐字照搬）**：

5. **Node 3 (Research Report, incremental)**: From the very first analysis node, and at the end of *each* node (1 / 1.5 / 2a / 2b, not just once at the very end), append a short markdown section — written **for the user, not for the developer log** — to the task's own report draft file `physics-agent/runtime/report_<task-slug>.md` (created on first append; path is stable for the whole task, one file per task, never mixed with a different task's draft). Each section must answer, in the user's language: what was done at this step, what evidence/assumption it relied on, what error or fallback happened and how it was corrected or routed back to an earlier assumption, and how this step's result compares against the model built so far. This file is the **primary narrative source** for Node 4 (the HTML render) — not the raw trace log — so it must be written *as the work happens*, not reconstructed from memory at the very end (by which point an earlier node's reasoning detail may no longer be in active context). The final Node 3 pass (after Node 2b) integrates all prior appended sections into a coherent concluding section (final answer, sanity check of why the conclusion is or is not reasonable, what would need to change for it to be wrong) without deleting the earlier incremental sections. **When organizing the final integrated report's section order (abstract / introduction / assumptions / modelling / verification / results / strengths-weaknesses / discussion), refer to `physics-agent/knowledge/report_structure_guide.md` for the standard ordering convention and the six style rules (conclusion-first framing per section, assumptions grouped and numbered in a dedicated section, verification data source must be independent of the modelling data source, formulas must use LaTeX delimiters rather than Unicode subscript/superscript characters, data tables must use real markdown pipe syntax rather than plain-text lines, and section headings must not carry meta-commentary or self-evaluating parentheticals). That document is a methodology-level structural guide distilled from published competition reference solutions; it is NOT an answer source — §5's reference-answer containment rule applies in full: no value, formula, or conclusion in this task's report may be copied from `dev-notes/reference-solutions/`.
