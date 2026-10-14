---
name: physics-defense-lines
description: '数值执行前必须跑完的三条确定性防线（量纲门/边界门/配额回滚），触发信号是要进入建模-数值求解-验证环节之前，确认这三道检查都实际跑过、不是手工代跑。'
---

### Three Deterministic Defense Lines (Do Not Bypass)
You must execute the following hooks before advancing to the next pipeline node:
- **`shell` 工具精确调用规范（Tool Invocation Invariant）**：调用 `shell` 工具执行任何门禁脚本或求解程序时，传参必须是顶层扁平属性 `command: "..."`（纯字符串），**绝对禁止**包装为 `{"input": ...}` 嵌套结构；若需指定目录传入 `cwd`。正确格式示例：`shell(command="python physics-agent/hooks/dimensional_gate.py ...")`。
1. **Dimensional Gate**: After writing down the physical governing equations, you MUST invoke `physics-agent/hooks/dimensional_gate.py` (Pint-engine dimensional homogeneity check, SymPy for parsing) before any numerical execution. A mismatch MUST hard-block downstream computation; do not hand-roll your own dimensional check. **Expression form matters, not just the physics**: if the governing equation contains a derivative/ODE term, write it as SymPy's explicit `Derivative(function, variable, *count)` call in the `--equation` argument (and declare the differentiated function's own symbol, e.g. `u`, in `--dims` alongside the independent variable) — do NOT hand-write differential notation like `du/dx` or `dv/dt`; that notation does not parse at the gate's SymPy layer and produces a confusing `symbols without declared dimensions` error rather than a real PASS/FAIL verdict (see `dimensional_gate.py`'s docstring usage examples, which include a worked ODE-form example).
2. **Boundary Gate**: Run extreme physical degenerate cases (e.g. $h \to 0$, $m \to \infty$, zero-drag) using `physics-agent/hooks/boundary_gate.py` driven by a spec JSON. Only when these boundary tests yield physically valid limits may the pipeline advance to the report node.
3. **Quota & Annealing Rollback**: Downstream code error-correction has a strict quota of $N \le 3$ retries. If continuous numerical divergence, crashes, or exceeding the quota occurs, you MUST trigger the Annealing Strategy: roll back the state machine to the **Hypothesis Layer** (re-evaluate physical boundary conditions and parameters like $C_D$), and forbid silently patching the physical assumptions within downstream code.
