---
name: physics-auditability
description: 每次写入 problem_state.json 或跑完任一 hook/外部调用后，必须做的写回校验、审计记录（audit_log.py）、运行资产文件（runlog.py）与可追溯性徽标——触发信号是"我刚写了一个 delta / 刚跑完一次脚本，该确认它真的落地并用中文留痕了"，不是建模/求解本身。
---

### Auditability & Context Management（可审计性与运行留痕铁律）

1. **单一状态真源与归属目录（C2）**：
   - 每个任务在 `physics-agent/runtime/<task-slug>/problem_state.json`（从 `physics-agent/runtime/problem_state_template.json` 复制创建）维护唯一状态真源。完整顶层字段包括：`task`, `session_key`, `stage`, `quota`, `hypothesis_layer`, `dimensional_table`, `internal_prior`, `knowledge_routing`, `data_source_decision`, `numerical_artifacts`, `audit_logs`, `anomalies`, `verification`, `report`。
2. **写回即读回校验（Write-back verification，强制必做）**：
   - 每次对 `problem_state.json` 或任务产物执行 `write` / `edit` 后，必须立即调用 `read` 核对目标字段确实已更新为新值（而非旧值或 `null`）。若写回未生效，按 `physics-permission-shortfall`（§4）权限缺口规则停止并上报，严禁盲目信以为真。
3. **审计记录强制走 `audit_log.py`，且 `args.note` 必须使用纯正简体中文（C3 + E5 + E6 铁律）**：
   - 任何外部能力调用、数据源决策（Node 1.5）、知识路由（Node 2a）、门禁脚本或求解脚本运行，都必须通过 `physics-agent/hooks/audit_log.py` 追加结构化记录，严禁手改 `audit_logs` 数组。
   - **语言与内容硬约束**：`audit_logs` 中每条记录的 `args.note` 字段以及 `runlogs/<artifact_id>.txt` 中的说明文字**必须使用面向用户可读的简体中文**（1–2 句清晰说明本次调用的物理目的与结果），**严禁写英文段落，严禁夹杂 `Level 0`、`Node 1.5`、`A4 6-key extras attached` 等开发侧内部黑话**。
   - **正确中文范例**：
     - 数据源记录（Node 1.5，需附带 `script_path` 指向参数文件或数据源说明标识，确保前端数据源子项正常归集）：`note: "采用公开发表的木星与四颗伽利略卫星标准轨道常数（引力参数与轨道半长轴），并以双体弹性飞掠解析几何上界与齐奥尔科夫斯基公式作为独立验证基准。"`
     - 建模求解记录（Node 2b）：`note: "第 2 次运行木星卫星引力弹弓减速模型：修正入轨所需速度增量符号后重新求解，木卫一（Io）单次飞掠最大减速达 24.51 km/s，可完全覆盖 15.59 km/s 的入轨减速需求。"`
4. **脚本执行 6 扩展键与 `runlogs/<artifact_id>.txt` 资产文件同步生成（4a + 4c + E6 单一真源）**：
   - 凡是执行脚本（`physics-agent/hooks/*.py` 或任务专属求解脚本如 `gravity_assist_model.py`），调用 `audit_log.append_record(..., extras={...})` 时必须附带 6 个扩展键：`script_path`、`stdin_or_argv`、`stdout_tail`、`stderr`、`exit_code`、`iteration_index`。
   - 若执行的是**本任务现场编写的求解/验证脚本**（非 `physics-agent/hooks/` 下的通用脚本），必须在拿到 `artifact_id` 后立即调用 `physics-agent/hooks/runlog.py` 的 `write_runlog()`，将**中文作用说明 + 完整脚本源码 + 完整命令行参数 + 完整 stdout/stderr + 退出码**写入 `physics-agent/runtime/<task-slug>/runlogs/<artifact_id>.txt`，确保 Node 4 右侧常驻预览窗格有完整、真实的中文资产可读。
5. **数值结论可追溯徽标**：
   - 报告中的核心数值结论必须在 `problem_state.json` 的 `report.traceability` 中锚定到具体的 `artifact_id`。
