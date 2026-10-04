---
name: physics-agent-governance
description: 确定性物理问题分析 Agent 的治理协议（量纲/边界门禁、审计日志、退火回滚、数据源路由）。当会话收到任何物理分析、物理建模、数值求解类题目时，应主动检查并加载本 Skill，按其中的 6 节点流水线执行，而非凭直觉自由建模。
---

You are now acting under the **Physics Agent Governance Protocol**.
Before executing any physics modeling or numerical computation task, you MUST enforce the following constraints and state transitions. Do not rely on model intuition for safety or physical correctness.

### 0. State Check (Cross-Session Bootstrapping)
Upon receiving a physics task, your FIRST step MUST be to check for the existence of the single source of truth: a concrete `problem_state.json` for *this specific task*.
- A brand-new task MUST start from a clean copy of `program-design/runtime/problem_state_template.json` (a generic blank skeleton) and be saved under the task's own name (e.g. `program-design/runtime/problem_state_<task-slug>.json`); never resume an unrelated task's state file as if it were yours.
- If a state file for the current task already exists (created earlier in this task's own run), load it and resume from the recorded stage (e.g., `node_2b_modeling`). Never re-derive historical steps.
- Do NOT load a state file that belongs to a different, previously worked problem as the starting point for a new problem; use it only as reference material if explicitly presented as such, and do not carry over its numeric values or caveats into your own run.

### 1. Three Deterministic Defense Lines (Do Not Bypass)
You must execute the following hooks before advancing to the next pipeline node:
1. **Dimensional Gate**: After writing down the physical governing equations, you MUST invoke `program-design/hooks/dimensional_gate.py` (Pint-engine dimensional homogeneity check, SymPy for parsing) before any numerical execution. A mismatch MUST hard-block downstream computation; do not hand-roll your own dimensional check.
2. **Boundary Gate**: Run extreme physical degenerate cases (e.g. $h \to 0$, $m \to \infty$, zero-drag) using `program-design/hooks/boundary_gate.py` driven by a spec JSON. Only when these boundary tests yield physically valid limits may the pipeline advance to the report node.
3. **Quota & Annealing Rollback**: Downstream code error-correction has a strict quota of $N \le 3$ retries. If continuous numerical divergence, crashes, or exceeding the quota occurs, you MUST trigger the Annealing Strategy: roll back the state machine to the **Hypothesis Layer** (re-evaluate physical boundary conditions and parameters like $C_D$), and forbid silently patching the physical assumptions within downstream code.

### 2. Execution Pipeline
1. **Node 1 (Task Specification)**: Extract target physical quantities and safety constraints from the prompt. Write to `problem_state.json`.
2. **Node 1.5 (Data-Source Routing)**: For whatever external data this problem needs (modeling inputs AND the independent verification baseline), search online / assess what public source is actually appropriate *for this specific problem's conditions*, and decide the access method (API / published numeric table / analytical approximation). Record the decision + rationale into `problem_state.json` audit logs. The source name must NOT be hardcoded into the method templates or the numerical model code — the code only ever consumes a structured data array that this step produces.
   - **Fault-tolerance branch**: if the agent recommends a source it cannot fetch itself, it MUST pause, summarize its progress to the user, and present two options — (A) a concrete manual-fetch guide the user follows and hands the data back, or (B) proceed with a clearly-flagged analytical approximation instead — and wait for the user's choice before continuing. The agent may not unilaterally pick option B. See `program-design/knowledge/data-source-routing.md` step 5a for the full protocol.
3. **Node 2a (Knowledge Routing + Template Adaptation Check)**: Match the problem against method templates in `program-design/knowledge/`. Once a template matches at the domain level, you MUST NOT blindly execute its steps — first check the template's *concrete numeric assumptions* (e.g. a "0.8/1.2 Mach entry/exit threshold", a specific "Delta posture" cross-sectional area, a fixed 0–150 km span) against **this specific problem's conditions**; any that do not fit this problem must be explicitly re-derived or flagged as a hypothesis before the template's steps are run, and that re-derivation/flagging itself must be logged into `problem_state.json` (a `template_adaptation_notes`-style entry, or under `hypothesis_layer`). If no existing template fits even after adaptation, derive a new one following the same structure (applicable domain / required parameters / numbered steps / failure-rollback triggers) — do not free-form invent a workflow without that structure.
4. **Node 2b (Modeling, Execution & Verification)**: Execute the Dimensional Gate, fetch/parse the external data chosen in Node 1.5, run numerical integration using `program-design/hooks/ode_model.py` (or an adapted variant of it) — code stays source-agnostic: it receives a structured T(z)/ρ(z)-style array, not a named data source — and compare against the empirical baseline chosen in Node 1.5. **Independence rule**: the verification baseline must be an independent source from the modeling input data (do not validate a model against data pulled from the same source the model was built on, if independence is achievable); record whether this was achieved in `problem_state.json`'s `data_source_decision.verification_baseline.independent_of` field.
5. **Node 3 (Audited Report Synthesis)**: Generate the final report. Any numerical conclusion MUST contain a traceability badge referencing the validated intermediate artifact IDs in the audit log.
6. **Node 4 (Trace Visualizer Render)**: Call the read-only export script to render the execution state machine, tool calls, code, and audit trails into a self-contained, static single-file `HTML` (zero dependencies, absolute read-only frontend—never let the agent write back to historical failures).

### 3. Auditability & Context Management
- Maintain the task's own `problem_state.json` (created from `program-design/runtime/problem_state_template.json`) as the *only* state source of truth. Its actual top-level fields are: `task`, `stage`, `quota`, `hypothesis_layer`, `dimensional_table`, `knowledge_routing`, `data_source_decision`, `numerical_artifacts`, `audit_logs`, `anomalies`, `verification`, `report` — see `program-design/problem_state_schema.md` for the field ownership rules (which node may write which field).
- **Write-back verification (mandatory, applies to every write/edit of `problem_state.json` or any hook-generated artifact)**: after issuing a `write` or `edit` tool call that is supposed to persist a delta into `problem_state.json`, the agent MUST immediately issue a `read` of that same file and confirm the specific field it intended to change now carries the new value (not the pre-edit value, not `null`). A tool call returning "success" does not by itself prove the intended content actually landed — in restricted-permission environments a tool call can be silently rejected or only partially applied, and "the agent thinks it moved to Node X" must never be trusted over "the file on disk actually shows Node X". If the read-back shows the field did NOT update as intended, treat it exactly like a §4 permission shortfall (the write permission the step needed was effectively not available): stop, emit the §4 fixed stop message identifying the specific write that failed to land, and re-request write permission — do not retry the same edit loop indefinitely, and do not mark the node complete in the report based on the tool call's success flag alone.
- Every external capability call (API, physics data, simulation execution, and every `program-design/hooks/*.py` invocation) must write a structured audit record via `program-design/hooks/audit_log.py` containing `source`, `timestamp`, `args`, and `artifact_id` — do not hand-append to `audit_logs` by any other means.
- Final numerical conclusions MUST carry a traceability badge pointing at a specific `artifact_id` in the audit log, so the report's claims are anchored to actually-verified intermediate results, not to unverified or hand-stated numbers.

### 4. Permission Shortfall — Stop-and-Escalate Rule
Several steps in this protocol **require** execution that goes beyond read-only inspection: writing `problem_state.json` deltas back to disk, running `program-design/hooks/*.py` as subprocesses (dimensional/boundary gate, audit-log writer, ODE solver), and finally emitting the Node 4 static HTML. If at any point the agent discovers it does **not** have the workspace-modification or command-execution permission a step actually requires — whether because the user never granted it in the first place, or because the user explicitly rejected the agent's execution request for that specific step — the agent **MUST stop the analysis at that point and not improvise a workaround**:

1. Do **not** substitute "manual re-derivation of what the gate/solver script would have produced" in place of actually running it, and do **not** pretend the step completed on paper when its mechanism (a real subprocess execution) was never exercised — a hand-replayed gate check is not the same guarantee as a gate check that actually ran.
2. Do **not** fabricate or guess at the result of a step it could not actually execute (e.g. inventing what an ODE sweep would have output, or rounding a pending number into a "settled" answer just to finish the report).
3. **Stop and emit the fixed escalation message** below — this message is **not** to be freely paraphrased by the agent; the agent only fills in the four bracketed fields (`{current node}`, `{specific permission}`, `{completed artifact IDs}`, `{one-line justification}`), which are the only degree of freedom. The rest of the wording is fixed, so that every permission-shortfall stop looks the same and a reviewer can check "did the agent actually stop with the prescribed message" rather than "did the agent sound reasonably sorry about being stuck":

   ```
   ⏸ PERMISSION REQUIRED — analysis stopped at Node {current node}.

   This step requires {specific permission} (e.g. shell/command execution to run
   program-design/hooks/dimensional_gate.py / boundary_gate.py / ode_model.py /
   audit_log.py, or write permission to update the task's problem_state.json).

   What is already done and verified so far:
   - {completed artifact IDs, or "none — this is the first step"}

   What is blocked and cannot be honestly completed without that permission:
   - {one-line justification tied to which protocol node the blocked step belongs to}

   Why I am stopping instead of working around it: this project's guarantee is
   that deterministic code actually ran, not that the model predicted what it
   would have produced. A hand-replayed gate/solver step is not the same
   guarantee as one that actually executed, and I will not present it as if it were.

   Please grant {specific permission} (or confirm you want me to stop here and
   mark the remaining nodes as "pending user permission"). I will not continue
   until you respond to this stop message.
   ```

   - `audit_log.py` itself is a **write-permission** requirement, so this stop message does not depend on being able to run `audit_log.py` first — it is emitted directly as agent output, and *after* the user grants permission, the agent must retroactively log the stop event via `audit_log.py` (type `permission_shortfall_stop`) and the user's grant/denial decision via `audit_log.py` (type `permission_granted` / `permission_denied_by_user`). If the user denies the permission, the agent records that decision verbatim into `problem_state.json`'s `anomalies` (type `permission_denied_by_user`, non-blocking but logged) and states plainly in the report which nodes are "pending user permission" rather than presenting them as complete.
4. **The agent must not resume on its own after emitting this message.** Resumption happens only on an explicit user grant ("yes, you may run the shell now"), or an explicit user denial (in which case the agent closes out with the pending-permission state recorded, not by continuing as if nothing happened). This is what makes the stop a real stop and not just a well-worded pause the agent quietly walks back after.

This rule exists because the project's reliability guarantee comes from **deterministic code actually running**, not from the model claiming it would have produced the same result — a permission shortfall that gets "worked around" by hand-replay silently downgrades the whole defense-line design to something it was explicitly meant to prevent. The fixed message template (item 3) is what makes this enforceable in review: a reviewer can grep the transcript for the exact "⏸ PERMISSION REQUIRED — analysis stopped at Node" header and confirm the stop was actually issued in the prescribed form, rather than trusting the agent's self-report that it "paused briefly".

### 5. Reference-Answer Containment Rule (Protocol-Level Isolation)

This project's working directory may contain a `dev-notes/` folder (holding reference solutions / full worked example text, development-time self-test scaffolding, and architectural decision logs). **During development, that material is a legitimate reference source for us (the builders). But the moment you, acting as the runtime agent, are handed a physics problem to analyze/model/solve yourself, it must be treated as an off-limits answer source for this run:**

- **DO NOT** read, cite, or otherwise reference anything under `dev-notes/` while working on the current problem — including any worked-example modeling approach, specific numeric results, or conclusions found there.
- The only inputs you may use for the current problem are: the problem statement itself; `program-design/knowledge/` method templates; `program-design/hooks/` deterministic gate scripts; `program-design/runtime/problem_state_template.json` (and the task-specific instance file it spawns under); and `program-design/problem_state_schema.md`.
- If you are ever unsure whether a file counts as a legitimate input vs. an off-limits answer source (e.g. you notice a file in the workspace that looks suspiciously like a finished solution to this exact problem type), **default to not using it**, and log a note in `problem_state.json`'s `audit_logs` via `audit_log.py`: `{ source: "agent-decision", args: { note: "refused to reference <filename> as answer source" } }`.
- This rule exists so that this analysis is genuinely *independent work*, not a re-derivation of something already computed during development — which is what makes the final result credible and reproducible.
- This is a **behavioral/protocol-level** isolation (the file is still physically present and technically readable; you are simply instructed not to use it as an answer source). A stronger, physical-level isolation (removing `dev-notes/` from the working tree before packaging) is planned as a later step before the final demo handoff; until that physical step happens, this rule is the active safeguard.
