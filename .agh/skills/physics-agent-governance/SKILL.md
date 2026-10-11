---
name: physics-agent-governance
description: 当会话收到任何物理分析、物理建模、数值求解类题目时，应主动检查并加载本 Skill，按其中的 6 节点流水线执行，而非凭直觉自由建模。
---

> 环境提醒：本项目 Python hooks（`program-design/hooks/*.py`）如果本机没有可用的 Python，先检查 `program-design/third_party/portable-runtime/`（内置离线 Python 3.13.9 + 烘焙好的 wheel + CJK 字体，不碰系统）能不能直接用，不要直接把“没 Python”当成环境问题停下来等用户装——详见 §4a-0，以及 `PORTABLE_RUNTIME.md` 里的完整设计/伦理边界说明。

You are now acting under the **Physics Agent Governance Protocol**.
Before executing any physics modeling or numerical computation task, you MUST enforce the following constraints and state transitions. Do not rely on model intuition for safety or physical correctness.

### 0. State Check (Cross-Session Bootstrapping)
指针：完整规则见 skill `physics-state-check`（`.agh/skills/physics-state-check/SKILL.md`）。触发信号 = 收到任何物理任务后的第一步，判断该任务该从哪个已有阶段恢复还是全新开始、以及要不要/能不能记录本次会话的 `session_key`。

### 1. Three Deterministic Defense Lines (Do Not Bypass)
指针：完整规则见 skill `physics-defense-lines`（`.agh/skills/physics-defense-lines/SKILL.md`）。触发信号 = 要进入建模-数值求解-验证环节之前，确认量纲门/边界门/配额回滚这三道检查都实际跑过、不是手工代跑。

### 2. Execution Pipeline
指针：Node 1 / 1.5 / 2a / 2b（任务规范、数据源路由、知识路由+模板适配检查、建模-数值求解-验证）完整规则见 skill `physics-pipeline`（`.agh/skills/physics-pipeline/SKILL.md`）。触发信号 = 要开始实际建模/求解/验证阶段时，依次进入这四个节点。
4a. **Node 2.7（可选，按需触发）— 数值结果绘图**：指针，完整规则见 skill `physics-report-charting`（`.agh/skills/physics-report-charting/SKILL.md`，跟③第 2 点“trace_visualizer.py 渲染层升级”是同一批待改内容，本指针先占位，待③第 2 点定稿后同步更新）。
5. **Node 3（研究汇报，增量式）**：指针，完整规则见 skill `physics-report-writing`（`.agh/skills/physics-report-writing/SKILL.md`，跟③第 1 点“report_structure_guide.md 补 3 条新约束”是同一批待改内容，本指针先占位，待③第 1 点定稿后同步更新）。
6. **Node 4 (Trace Visualizer Render)**: Call `program-design/hooks/trace_visualizer.py` with `--trace <raw trace export> --report <the report draft md from Node 3> --state <problem_state.json>` and, if Node 2.7 produced any `figures` blocks, additionally `--figures-dir <the directory make_report_figures.py wrote its .png/.svg files into>` (without it, every `{{figure: <id>}}` placeholder in the report renders as an explicit "missing figure source" box, not a silently-blank one). This renders a self-contained, static single-file HTML. The HTML's main narrative is the Node 3 markdown report; the trace is used only as an **on-demand verification appendix** ("did this claim actually have a supporting tool call?" expandable per section, not the headline content). Absolute read-only frontend — the HTML never writes back to anything.
   - **Trace source — automatic first, manual fallback second**: read `session_key` from this task's `problem_state.json` (written at Node 0/1, see §0). If it is non-null and a live AGH named pipe is reachable on this machine, obtain the trace automatically with `node program-design/hooks/trace_capture.cjs <session_key>` — this script discovers the live `agnes-*` pipe on its own (no hardcoded hash), connects, and streams this session's full history back via the AGH `session/load` mechanism, converting it on the fly into exactly the JSONL shape `trace_visualizer.py`'s `--trace` argument expects (written under `program-design/runtime/` alongside the task's other artifacts). No user action, no `agh export` step, no human-supplied file is involved in this path. Only if `session_key` is null (the case where the runtime context did not expose it at Node 0/1 — see §0's fallback rule) OR the pipe is not reachable from this environment, fall back to a user-supplied `--trace <file>` argument (e.g. a manually exported `agh export --raw` JSONL); do not invent a session key or silently use another session's trace to stand in for the missing one.
   - **Timing rule**: issue this call **before** your final user-facing reply of the session (i.e. it is a closing action, not something you finish and then keep chatting about) — this is what makes it possible for the HTML to cover "everything the agent actually did" without needing to include its own generation step (per project decision: the HTML does not report on itself). If you need to keep working on the analysis after this point, do not call Node 4 yet; call it only at the true end.
   - **User confirmation pause (optional, not mandatory) — must be plain reply text, never an approval/dialog prompt**: you MAY, at the end of your final user-facing *reply text*, add a fixed one-line offer such as: "我可以生成本次研究的网页版报告供您查看，需要的话说一声即可。" If the user confirms in a normal reply, call Node 4 and link the resulting HTML file in your next reply. If you do not want to add a confirmation pause, simply generate and link the HTML at the end of the same reply that delivers the conclusion — no extra turn needed. **Do not require this confirmation unconditionally** — it is a convenience the user may opt out of by asking you to just produce the link directly. **This offer/pause must never be delivered as a tool-call approval request, a native dialog, or any modal that intercepts the user's attention with a yes/no button** (this project has already hit, more than once, the situation where such a prompt timed out and the agent was left to auto-reply in place of the user — that is exactly the failure mode this wording avoids). It is ordinary text at the bottom of the reply, and the user answers it (or doesn't) in their own next message, in the same channel as everything else.

### 3. Auditability & Context Management
指针：完整规则见 skill `physics-auditability`（`.agh/skills/physics-auditability/SKILL.md`）。触发信号 = 每次写入 `problem_state.json` 或跑完任一 hook/外部调用后，确认写回确实落地、审计记录已留、可追溯徽标已加。

### 4. Permission Shortfall — Stop-and-Escalate Rule
指针：完整规则（含 §4 Kind 1/Kind 2 区分 + §4a 环境依赖缺口、§4a-0 便携运行时快路径、§4a-0a 安装前烟囱测试）见 skill `physics-permission-shortfall`（`.agh/skills/physics-permission-shortfall/SKILL.md`）。触发信号 = 某一步的写盘/跑 hook/渲染动作因权限被拒，或脚本报依赖缺失（ModuleNotFoundError 等），在停下来之前必读。

### 5. Reference-Answer Containment Rule (Protocol-Level Isolation)

This project's working directory may contain a `dev-notes/` folder (holding reference solutions / full worked example text, development-time self-test scaffolding, and architectural decision logs). **During development, that material is a legitimate reference source for us (the builders). But the moment you, acting as the runtime agent, are handed a physics problem to analyze/model/solve yourself, it must be treated as an off-limits answer source for this run:**

- **DO NOT** read, cite, or otherwise reference anything under `dev-notes/` while working on the current problem — including any worked-example modeling approach, specific numeric results, or conclusions found there.
- The only inputs you may use for the current problem are: the problem statement itself; `program-design/knowledge/` method templates; `program-design/hooks/` deterministic gate scripts; `program-design/runtime/problem_state_template.json` (and the task-specific instance file it spawns under); and `program-design/problem_state_schema.md`.
- If you are ever unsure whether a file counts as a legitimate input vs. an off-limits answer source (e.g. you notice a file in the workspace that looks suspiciously like a finished solution to this exact problem type), **default to not using it**, and log a note in `problem_state.json`'s `audit_logs` via `audit_log.py`: `{ source: "agent-decision", args: { note: "refused to reference <filename> as answer source" } }`.
- This rule exists so that this analysis is genuinely *independent work*, not a re-derivation of something already computed during development — which is what makes the final result credible and reproducible.
- This is a **behavioral/protocol-level** isolation (the file is still physically present and technically readable; you are simply instructed not to use it as an answer source). A stronger, physical-level isolation (removing `dev-notes/` from the working tree before packaging) is planned as a later step before the final demo handoff; until that physical step happens, this rule is the active safeguard.

### 6. User-Specified Document Parsing (On-Demand, Not a Fixed Pipeline Step)
指针：完整规则见 skill `physics-doc-parsing`（`.agh/skills/physics-doc-parsing/SKILL.md`）。触发信号 = 用户明确指向一个自己读不了的文档（PDF/扫描图/docx），不是每个物理任务都要读，问题本身难不构成触发条件。

## 7. Report Charting (Optional Node)

本节不再重复绘图规则已写过的内容——那份说明的正文现在完整收在 skill `physics-report-charting`（`.agh/skills/physics-report-charting/SKILL.md`，跟③第 2 点"trace_visualizer.py 渲染层升级"是同一批待改内容，本指针先占位，待③第 2 点定稿后同步更新）里，本节只做一件事：给出指针，避免两处各写一遍同一份 kind 说明导致以后改了一处忘了另一处。

- 完整 spec（字段结构、每个 kind 的边界、`make_report_figures.py` 的尺寸不匹配/NaN-Inf/缺 CJK 字体时的具体行为）：`program-design/problem_state_schema.md` §Figures（稳定的协议级摘要）+ `dev-notes/self-tests/03/charting_generic_architecture.md`（更详细的设计文档，跟 `physics-report-charting` skill 里指向的是同一份）。
- `interactive`/`interactive_live` 两个可选分支的能力边界（什么情况下该用 `interactive` 而不是 `interactive_live`、为什么不能拿 `interactive_live` 去做"参数变化时重新解一个重型 ODE/PDE"）：`physics-report-charting` skill 里的 Node 2.7 章节末尾两段（"Optional interactive branch" 和 "Live-parameter branch"）已经写清楚，本节不再重复。
- 本节跟 `physics-report-charting` 里那两段的关系：**以后如果要改"静态 6 种 kind 的说明"或"interactive/interactive_live 的边界说明"，只改 `physics-report-charting` skill 那一处，本节（§7）永远只是指针，不随内容更新而需要单独维护**——这是把 §7 从"重复展开"改成"纯指针"的目的，跟 2.5 判断的"分层没收敛"（同一信息在两层里各写一遍）是针对同一个问题的修复。

