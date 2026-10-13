---
name: physics-report-writing
description: 每个 pipeline 节点（Node 1/1.5/2a/2b）结束时都要增量追加一段写给用户的 markdown 汇报；Node 3 收尾阶段把所有增量段整合成完整研究汇报。触发信号是"该写/该更新这次分析的用户可见汇报了"，不是建模/求解本身。
---

> **行文规范（10/13 升级为七条铁律）**：`physics-agent/knowledge/report_structure_guide.md` 现已确立完整的**七条行文风格约束**：
> 1. **结论先行**：摘要与每节开头先给结论，再给推导过程；
> 2. **假设显式化**：所有简化假设集中放在"假设"章节并按编号列出，正文中直接用"由假设 N 可知"引用，不加任何复述规则的元导语；
> 3. **验证独立于建模**：验证章节的数据源或校验方法独立于建模输入，并用自然语言写明来源与偏差，严禁在正文中出现 `independent_of`、`data_source_decision` 等内部字段名；
> 4. **公式必须使用 LaTeX 定界符**（`$...$` 行内、`$$...$$` 行间），严禁使用 Unicode 上下标字符冒充公式排版；
> 5. **数据表格必须使用真实 Markdown 管道语法**（`|` 分隔表头 + `|---|---|` 分表线 + 数据行），严禁使用空格/逗号对齐的纯文本冒充表格；
> 6. **各级标题纯粹表达物理与逻辑主题**，严禁携带"（本轮说明）""（先给结论）"等元注释括号，报告开头与结尾也严禁附加"本轮执行说明"等汇报流水线节点的段落；
> 7. **严禁正文行内元导语、自我标榜及内部协议字段透传**（详见 `report_structure_guide.md` 第 7 条反例与正例对照表及确定性 Lint 黑名单）：严禁出现 `题目（原样引用）：`、`逐条列出（正文里用编号引用，不再临时引入新假设）：`、`本报告是 governance 6 节点 pipeline 的正式产物`、`Node 2b`、`Level 0` 等开发侧黑话。

**当前范围（已定稿）**：Node 3（Research Report, incremental）职责划分——何时追加汇报、追加到哪个路径、如何在收尾时整合并通过 `report_quality_check.py` 交付前自检。

### Node 3（研究汇报，增量式写作与整合）

5. **Node 3 (Research Report, incremental)**:
   - **唯一合法路径（严禁放错目录，C2 铁律）**：从第一个分析节点开始，在每个节点（Node 1 / 1.5 / 2a / 2b）结束时，向本任务专属子目录下的报告文件 `physics-agent/runtime/<task-slug>/report.md`（亦兼容 `physics-agent/runtime/<task-slug>/report_<task-slug>.md`，**但必须位于 `<task-slug>/` 子文件夹内，绝对禁止直接放在 `physics-agent/runtime/` 根目录或工作区根目录**）增量追加或更新对应章节。完整目录约定见 `physics-agent/knowledge/path_convention.md` §1。
   - **面向物理研究读者写作，而非开发日志**：每节内容必须用严谨、自然的中文科研报告语言回答：本步解决了什么物理子问题、依赖了哪条编号假设或哪组公开常数、推导与数值结果是什么、如何与前序分析衔接。
   - **收尾整合与八章标准结构**：Node 2b 完成后，按 `physics-agent/knowledge/report_structure_guide.md` 规定的八章顺序（1. 摘要 → 2. 引言与背景 → 3. 假设 → 4. 建模 → 5. 验证 → 6. 结果 → 7. 优缺点 → 8. 讨论与未来方向）整合为连贯、完整的科研报告，并在 `problem_state.json` 的 `report.conclusion` 与 `report.traceability` 中记录核心结论数值到 `artifact_id` 的映射。
   - **写完必跑确定性 Lint 自检（B1 + E2）**：Node 3 报告写完或任何修改后，在进入 Node 4 渲染前及 Node 4 渲染后，必须对照 `report_structure_guide.md` 的"第 7 条典型反例与正例改写对照表"并运行 `python physics-agent/hooks/report_quality_check.py` 扫描 Markdown 与 HTML；若命中任何元导语、自我标榜或内部字段名，必须立即改写直至检查全部通过。
