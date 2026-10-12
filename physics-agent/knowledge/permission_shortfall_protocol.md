# 权限/环境缺口处理协议（Permission & Environment Shortfall Protocol）

本文档收纳 `SKILL.md` §4/§4a 里"停下来要念的固定话术模板"全文。`SKILL.md` 正文在
§4/§4a 只保留"遇到这类缺口时，按本协议的固定话术停止并上报"这一句 + 指向本文档的
指针，不再两处并存同一份话术。规则本身（什么时候该停、停了之后不许自己恢复、Kind 1
vs Kind 2 怎么区分等判断逻辑）仍写在 `SKILL.md` §4/§4a 正文里，本文档只收"固定话术
模板"这一层，目的是让 `SKILL.md` 正文更聚焦于"该做什么判断"，而把"停下来那一刻具体
要念什么字"这段高频但机械的内容独立出来，避免每份文档都要重复整段话术。

话术里的 `{...}` 占位符含义与 `SKILL.md` §4 原表述一致，本文档不改变任何占位符语义。

## 权限缺口（Permission Shortfall）固定停止话术

- **Kind 1 — 被明确拒绝（`user_rejected` / `policy_denied`）用的固定话术**：

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

- **Kind 2 — 没人应答（`timeout` / `no_approver`）用的较短变体**（只改最后一句，
  其余跟上面 Kind 1 版相同）：

  ```
  Please confirm whether you were away or do not want this step to run: I could
  not get an answer for {specific permission} (the request timed out / had no
  approver connected). Say "grant it" and I will retry the same call once, or
  say "skip it" and I will record the node as "pending, unanswered" (type
  `permission_unanswered`, distinct from an explicit denial) and close out here.
  ```

  （完整语境见 `SKILL.md` §4 item 2-3：Kind 2 不是"用户说了不"，是"没人做决定"，
  不能当成 Kind 1 那种明确拒绝来记录/处理。）

- 权限缺口停止事件的审计记录规则（话术念完之后要补记的 `audit_log.py` 条目，
  不是话术本身，跟 `SKILL.md` §4 正文里的规则配套，这里一并收录方便查）：
  - `audit_log.py` 本身是需要"写权限"才能调用的，所以停止话术本身**不依赖**先成功
    运行 `audit_log.py`；话术由 Agent 直接作为输出念出来，等用户授权之后，Agent
    再补记一次 `audit_log.py`（type 为 `permission_shortfall_stop`），以及用户的
    授权/拒绝决定（type 为 `permission_granted` / `permission_denied_by_user`）。
  - 用户拒绝授权时，Agent 要把这个决定原样记进 `problem_state.json` 的
    `anomalies`（type 为 `permission_denied_by_user`，不阻塞但要有记录），并在报告里
    明确写清"哪些节点是 pending user permission"，不能当成已完成来写。

## 环境缺口（Environment/Dependency Shortfall）固定停止话术

- 环境缺口版固定话术（刻意比权限缺口版短，因为这是一份"具体卡在哪"的阻塞报告，不是
  权限协商）：

  停止时要具体说明（不是照抄一段模板，是这四项必须逐条写清楚）：
  - 卡住的具体节点/钩子/脚本是哪个；
  - 缺的依赖具体是什么（例如"pint 没装"，不是笼统说"缺了某个依赖"）；
  - 装这个依赖是用户自己能做的机械步骤（例如"按 `program-design/hooks/
    requirements.txt` 跑 `pip install pint`"），还是当前环境里 Agent 无法解决的情况
    （例如没有包管理器访问权、没有网络、或者根本缺一个可用的运行时，比如只有
    Python 没有 Node.js）；
  - 给用户两个选项，Agent 不替用户选：
    - **(A)** "请装好 `<dependency>`，装好之后我原封不动重跑这一步"；
    - **(B)** "把这个节点标记为 `problem_state.json` 的 `anomalies` 里的
      `pending_environment`，先跳过不依赖它的部分继续"。
      选 (B) 等于"主动放弃一道确定性门禁"，跟 §4/§5 的权限/假设取舍是同一性质的
      判断，不能由 Agent 默默替用户做掉。
  - 在念出这段话术**之前**，先把"缺口本身"用 `audit_log.py`（type 为
    `environment_shortfall_stop`）记进 `problem_state.json` 的 `audit_logs`，这样即使
    用户最终没有回应，这条停止记录也已经在审计日志里存在，不依赖用户的最终决定才
    被记录。
