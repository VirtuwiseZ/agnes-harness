# problem_state.json — Schema Reference

Single source of truth for a physics-agent run. Every pipeline node reads
this file at the start of its turn and writes its deltas back before
handing off. No other file or chat context may be the authoritative copy.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `task` | object | Fixed task brief: problem id, description, target quantity, safety constraints |
| `stage` | string | One of `node_1_spec`, `node_2a_routing`, `node_2b_modeling`, `node_3_report`, `node_4_render`, `done` |
| `quota` | object | Remaining retries per stage (see "Quota & Annealing" below) |
| `hypothesis_layer` | object | Current physical assumptions (CD values, boundary conditions, model form) — the layer annealing rolls back to |
| `dimensional_table` | object | `symbol -> dimension name` declarations, as consumed by `dimensional_gate.py --dims` |
| `knowledge_routing` | object | Which method template + which JSON param file was matched (Node 2a output) |
| `numerical_artifacts` | object | Keyed store of computed numbers / ODE solutions, each tagged with an `artifact_id` (from `audit_log.py`) |
| `audit_logs` | array | Append-only audit records (see `audit_log.py`); only `audit_log.append_record` may mutate this |
| `anomalies` | array | Log of failures / boundary violations / annealing triggers encountered this run |
| `verification` | object | Empirical benchmark comparison result (model vs. real data, e.g. Baumgartner) with quantified error |
| `report` | object | Node 3 output: conclusion text + `traceability` map (claim -> `artifact_id`) |

## Quota & Annealing (per consensus §2.3)

- `quota.downstream_retries_remaining`: integer, starts at 3 per Node 2b attempt batch.
- Decrement once per actual code-edit + re-run cycle inside Node 2b.
- If it hits 0 **and** the model has not converged: set
  `stage = "node_2b_modeling"`, push an entry into `anomalies` of
  type `"annealing_triggered"`, and reset `hypothesis_layer` to the last
  known-good version before the failed batch. Do NOT continue patching
  downstream code.

## Field ownership rules

| Field | Only writer(s) |
|---|---|
| `task` | Node 1 (once, at init) |
| `stage`, `quota` | Node 2b (during execution), Node 3 (final `done`) |
| `hypothesis_layer` | Node 2b (on annealing rollback only, never silently in-place) |
| `dimensional_table` | Node 2b (when the governing equations are written out) |
| `knowledge_routing` | Node 2a |
| `numerical_artifacts` | Node 2b |
| `audit_logs` | `audit_log.append_record()` only — no node may edit it directly |
| `anomalies` | Node 2b (append-only, never rewritten) |
| `verification` | Node 2b |
| `report` | Node 3 |

Nodes never rewrite fields owned by earlier nodes; they only append to
`audit_logs` / `anomalies` and update their own owned fields.
