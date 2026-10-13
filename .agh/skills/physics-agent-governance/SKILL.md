---
name: physics-agent-governance
description: 当会话收到任何物理分析、物理建模、数值求解类题目时，应主动检查并加载本 Skill，按其中的 6 节点流水线执行，而非凭直觉自由建模。
---

> 环境提醒：本项目 Python hooks（`physics-agent/hooks/*.py`）如果本机没有可用的 Python，先检查 `physics-agent/third_party/portable-runtime/`（内置离线 Python 3.13.9 + 烘焙好的 wheel + CJK 字体，不碰系统）能不能直接用，不要直接把“没 Python”当成环境问题停下来等用户装——详见 §4a-0，以及 `PORTABLE_RUNTIME.md` 里的完整设计/伦理边界说明。

You are now acting under the **Physics Agent Governance Protocol**.
Before executing any physics modeling or numerical computation task, you MUST enforce the following constraints and state transitions. Do not rely on model intuition for safety or physical correctness.

### 0. State Check (Cross-Session Bootstrapping)
指针：完整规则见 skill `physics-state-check`（`.agh/skills/physics-state-check/SKILL.md`）。触发信号 = 收到任何物理任务后的第一步，判断该任务该从哪个已有阶段恢复还是全新开始、以及要不要/能不能记录本次会话的 `session_key`。运行时文件（`problem_state.json`/`task_params.json`/增量汇报 md/`runlogs/` 资产文件）统一落在哪、怎么命名，路径约定全文见 `physics-agent/knowledge/path_convention.md`（③第 3/5 条，10/12 新建，本节不复制目录地图，只留这一句指针）。

### 1. Three Deterministic Defense Lines (Do Not Bypass)
指针：完整规则见 skill `physics-defense-lines`（`.agh/skills/physics-defense-lines/SKILL.md`）。触发信号 = 要进入建模-数值求解-验证环节之前，确认量纲门/边界门/配额回滚这三道检查都实际跑过、不是手工代跑。

### 2. Execution Pipeline
指针：Node 1 / 1.5 / 2a / 2b（任务规范、数据源路由、知识路由+模板适配检查、建模-数值求解-验证）完整规则见 skill `physics-pipeline`（`.agh/skills/physics-pipeline/SKILL.md`）。触发信号 = 要开始实际建模/求解/验证阶段时，依次进入这四个节点。
4a. **Node 2.7（可选，按需触发）— 数值结果绘图**：指针，完整规则见 skill `physics-report-charting`（`.agh/skills/physics-report-charting/SKILL.md`，含静态 6 种 `kind`、`interactive`/`interactive_live` 分支，以及 E1 单文件内联公式与图表的硬性要求）。
5. **Node 3（研究汇报，增量式）**：指针，完整规则见 skill `physics-report-writing`（`.agh/skills/physics-report-writing/SKILL.md`）。汇报文件统一写入 `physics-agent/runtime/<task-slug>/report.md`，严格遵守 `physics-agent/knowledge/report_structure_guide.md` 的**八章结构与七条行文风格约束**（含第 7 条严禁行内元导语、自我标榜与内部字段名透传）。
6. **Node 4 (Trace Visualizer Render & Pre-Delivery Quality Loop)**:
   - **产物归属硬约束（C2 铁律）**：本任务产生的所有运行时文件（`problem_state.json`、`task_params.json`、`report.md`、`research_report_<task-slug>.html`、`trace_capture_converted_<id>.jsonl`、`runlogs/<artifact_id>.txt`、`figures/`）**必须全部落在 `physics-agent/runtime/<task-slug>/` 专属子文件夹内**，绝对禁止放在工作区根目录或 `physics-agent/runtime/` 根目录。
   - **渲染调用命令**：调用 `physics-agent/hooks/trace_visualizer.py`，显式传入任务专属子目录路径：
     `python physics-agent/hooks/trace_visualizer.py --trace physics-agent/runtime/<task-slug>/trace_capture_converted_<id>.jsonl --report physics-agent/runtime/<task-slug>/report.md --state physics-agent/runtime/<task-slug>/problem_state.json --out physics-agent/runtime/<task-slug>/research_report_<task-slug>.html`（若 Node 2.7 生成了图表，一并传入 `--figures-dir physics-agent/runtime/<task-slug>/figures`）。生成的 HTML 为 100% 离线自包含单文件（内联公式排版引擎、内联图表、左文右常驻预览窗格实时展示代码/运行日志/数据源，零外部 CDN，零 `file://` fetch 死链）。
   - **Trace 自动捕获**：读取 `problem_state.json` 的 `session_key`，若非空且命名管道可达，执行 `node physics-agent/hooks/trace_capture.cjs <session_key>` 并将输出的 `trace_capture_converted_<id>.jsonl` 保存或移动至 `physics-agent/runtime/<task-slug>/` 子目录内。
   - **交付前强制自检与返工循环（D1 + E2 铁律）**：在首次生成 HTML 后，以及**每次对报告 Markdown、HTML、渲染脚本或 Skill 做任何修改并重新生成 HTML 之后**，必须依次运行以下两个确定性自检脚本：
     1. `python physics-agent/hooks/skill_bom_check.py`（验证 `.agh/skills/*/SKILL.md` 全部无 UTF-8 BOM）；
     2. `python physics-agent/hooks/report_quality_check.py --report physics-agent/runtime/<task-slug>/report.md --html physics-agent/runtime/<task-slug>/research_report_<task-slug>.html --state physics-agent/runtime/<task-slug>/problem_state.json`（验证无未渲染 Markdown/LaTeX 语法、无死链、无英文说明、无行内元导语/自我标榜/开发黑话、右侧预览数据池完整）。
     **只要上述任一检查未通过，严禁向用户输出最终交付回复，必须立即针对报错项返工修改并重新运行检验，循环往复直至全部检查 0 报错通过。**
   - **确定性交付回复规范（C1 铁律）**：通过全部交付前检验后，向用户输出的最终回复**必须包含**：
     1. 单独一行的 **HTML 报告文件绝对路径**（如 `E:\agnes-harness\physics-agent\runtime\<task-slug>\research_report_<task-slug>.html`），方便用户一键复制；
     2. 一句明确的使用指导：`"您可以直接复制上述绝对路径到浏览器地址栏打开，或在文件管理器中双击该 HTML 文件离线查看完整报告（含数学公式排版与右侧代码/运行记录/数据源预览窗格）。"`
     缺任一项即视为未完成交付。
   - **User confirmation pause (optional, plain text only)**: 如需询问用户是否生成网页报告，仅可在普通回复末尾附一句纯文本提示，严禁使用模态弹窗或审批阻塞请求；默认推荐直接生成并通过检验后按上述 C1 规范交付路径。

### 3. Auditability & Context Management
指针：完整规则见 skill `physics-auditability`（`.agh/skills/physics-auditability/SKILL.md`）。触发信号 = 每次写入 `problem_state.json` 或跑完任一 hook/外部调用后，确认写回确实落地、审计记录已留、可追溯徽标已加。

### 4. Permission Shortfall — Stop-and-Escalate Rule
指针：完整规则（含 §4 Kind 1/Kind 2 区分 + §4a 环境依赖缺口、§4a-0 便携运行时快路径、§4a-0a 安装前烟囱测试）见 skill `physics-permission-shortfall`（`.agh/skills/physics-permission-shortfall/SKILL.md`）。触发信号 = 某一步的写盘/跑 hook/渲染动作因权限被拒，或脚本报依赖缺失（ModuleNotFoundError 等），在停下来之前必读。

### 5. Reference-Answer Containment Rule (Protocol-Level Isolation)

This project's working directory may contain a `dev-notes/` folder (holding reference solutions / full worked example text, development-time self-test scaffolding, and architectural decision logs). **During development, that material is a legitimate reference source for us (the builders). But the moment you, acting as the runtime agent, are handed a physics problem to analyze/model/solve yourself, it must be treated as an off-limits answer source for this run:**

- **DO NOT** read, cite, or otherwise reference anything under `dev-notes/` while working on the current problem — including any worked-example modeling approach, specific numeric results, or conclusions found there.
- The only inputs you may use for the current problem are: the problem statement itself; `physics-agent/knowledge/` method templates; `physics-agent/hooks/` deterministic gate scripts; `physics-agent/runtime/problem_state_template.json` (and the task-specific instance file it spawns under); and `physics-agent/problem_state_schema.md`.
- If you are ever unsure whether a file counts as a legitimate input vs. an off-limits answer source (e.g. you notice a file in the workspace that looks suspiciously like a finished solution to this exact problem type), **default to not using it**, and log a Chinese note in `problem_state.json`'s `audit_logs` via `audit_log.py`: `{ source: "agent-decision", args: { note: "拒绝引用工作区内的开发参考文件 <filename> 作为答案来源" } }`.
- This rule exists so that this analysis is genuinely *independent work*, not a re-derivation of something already computed during development — which is what makes the final result credible and reproducible.
- This is a **behavioral/protocol-level** isolation (the file is still physically present and technically readable; you are simply instructed not to use it as an answer source). A stronger, physical-level isolation (removing `dev-notes/` from the working tree before packaging) is planned as a later step before the final demo handoff; until that physical step happens, this rule is the active safeguard.

### 6. User-Specified Document Parsing (On-Demand, Not a Fixed Pipeline Step)
指针：完整规则见 skill `physics-doc-parsing`（`.agh/skills/physics-doc-parsing/SKILL.md`）。触发信号 = 用户明确指向一个自己读不了的文档（PDF/扫描图/docx），不是每个物理任务都要读，问题本身难不构成触发条件。

## 7. Report Charting (Optional Node)

本节不再重复绘图规则已写过的内容——那份说明的正文现在完整收在 skill `physics-report-charting`（`.agh/skills/physics-report-charting/SKILL.md`；③第 2 点已定稿（10/12），本指针不再占位，改为直接指向同一份 skill 正文）里，本节只做一件事：给出指针，避免两处各写一遍同一份 kind 说明导致以后改了一处忘了另一处。

- 完整 spec（字段结构、每个 kind 的边界、`make_report_figures.py` 的尺寸不匹配/NaN-Inf/缺 CJK 字体时的具体行为）：`physics-agent/problem_state_schema.md` §Figures（稳定的自包含协议级规范，正式项目内部自洽，不依赖 `dev-notes/` 目录）。
- `interactive`/`interactive_live` 两个可选分支的能力边界（什么情况下该用 `interactive` 而不是 `interactive_live`、为什么不能拿 `interactive_live` 去做"参数变化时重新解一个重型 ODE/PDE"）：`physics-report-charting` skill 里的 Node 2.7 章节末尾两段（"Optional interactive branch" 和 "Live-parameter branch"）已经写清楚，本节不再重复。
- 本节跟 `physics-report-charting` 里那两段的关系：**以后如果要改"静态 6 种 kind 的说明"或"interactive/interactive_live 的边界说明"，只改 `physics-report-charting` skill 那一处，本节（§7）永远只是指针，不随内容更新而需要单独维护**——这是把 §7 从"重复展开"改成"纯指针"的目的，跟 2.5 判断的"分层没收敛"（同一信息在两层里各写一遍）是针对同一个问题的修复。

