# problem_state.json — Schema Reference

Single source of truth for a physics-agent run. Every pipeline node reads
this file at the start of its turn and writes its deltas back before
handing off. No other file or chat context may be the authoritative copy.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `task` | object | Fixed task brief: problem id, description, target quantity, safety constraints |
| `session_key` | string \| null | This run's AGH session key (the stable, unique identifier AGH assigns to the conversation it is running in), written once at Node 0/1 state-file creation, so Node 4 can automatically pull this session's own trace back without a human-supplied export. See §0's "Record this run's own session key" bullet in the governance SKILL for the exact write rule, including what to do if the key is not available in the current client surface (leave null + log an audit note, do NOT guess). |
| `stage` | string | One of `node_1_spec`, `node_1_5_data_source`, `node_2a_routing`, `node_2b_modeling`, `node_3_report`, `node_4_render`, `done` |
| `quota` | object | Remaining retries per stage (see "Quota & Annealing" below) |
| `hypothesis_layer` | object | Current physical assumptions (CD values, boundary conditions, model form) — the layer annealing rolls back to |
| `dimensional_table` | object | `symbol -> dimension name` declarations, as consumed by `dimensional_gate.py --dims` |
| `knowledge_routing` | object | Which method template + which JSON param file was matched (Node 2a output) |
| `data_source_decision` | object | Node 1.5 output: chosen external data source + access method + verification baseline + rationale + availability check |
| `internal_prior` | object \| null | Node 1a's private, free-form "what do I think the answer is and why" sketch — written ONCE at Node 1a, never shown to the user, never cited in the report; its only permitted later use is a conscious divergence-check against Node 2b's verified result (see SKILL.md §2 Node 1a for the two hard rules). Exists so the sketch can never be silently read back as a settled, gate-verified number. |
| `numerical_artifacts` | object | Keyed store of computed numbers / ODE solutions, each tagged with an `artifact_id` (from `audit_log.py`). Sub-key `figures` (optional, see `problem_state_schema.md` §Figures below): problem-agnostic data blocks for the optional charting node (SKILL Node 2.7), consumed by `make_report_figures.py` (spec in `dev-notes/self-tests/03/charting_generic_architecture.md` §3, implemented in `program-design/hooks/make_report_figures.py`) to produce the image files Node 4 inlines via `--figures-dir`. |
| `audit_logs` | array | Append-only audit records (see `audit_log.py`); only `audit_log.append_record` may mutate this |
| `anomalies` | array | Log of failures / boundary violations / annealing triggers encountered this run |
| `verification` | object | Empirical benchmark comparison result (model vs. real data, e.g. Baumgartner) with quantified error |
| `report` | object | Node 3 output: conclusion text + `traceability` map (claim -> `artifact_id`). The full incremental markdown research report is a separate file on disk: `program-design/runtime/report_<task-slug>.md` — the schema's `report` field holds only the conclusion + traceability index; the narrative itself lives in that file, which Node 4 consumes directly. |

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
| `session_key` | Node 0/1 state-file creation (once, at the same moment `task` is written); Node 4 only ever reads it, never writes it |
| `stage`, `quota` | Node 2b (during execution), Node 3 (final `done`) |
| `hypothesis_layer` | Node 2b (on annealing rollback only, never silently in-place) |
| `dimensional_table` | Node 2b (when the governing equations are written out) |
| `knowledge_routing` | Node 2a |
| `data_source_decision` | Node 1.5 only — no later node may edit or "re-decide" it silently; if a downstream data-source fallback is needed it must surface as an `anomaly` (type `data_source_unavailable`), not by rewriting this field in place |
| `internal_prior` | Node 1a (written once, immediately after Node 1's spec is recorded); read-only for every later node — the only permitted "write" to it after Node 1a is appending a divergence-check note into `audit_logs` (type `internal_prior_divergence`), never rewriting `internal_prior` itself |
| `numerical_artifacts` | Node 2b |
| `audit_logs` | `audit_log.append_record()` only — no node may edit it directly |
| `anomalies` | Node 2b (append-only, never rewritten) |
| `verification` | Node 2b |
| `report` | Node 3 |
| `report_<task-slug>.md` (separate file, not a field in this JSON) | Node 3 (append incrementally at every node boundary; Node 4 reads it read-only) |
| `numerical_artifacts.figures` | Node 2.7 (optional node — only writes this sub-field if this problem's numerical results warrant charting; empty/absent is valid, not an omission) |

Nodes never rewrite fields owned by earlier nodes; they only append to
`audit_logs` / `anomalies` and update their own owned fields.

## Figures sub-schema (`numerical_artifacts.figures`, optional)

Domain-neutral, problem-agnostic data blocks. The full schema (6 kinds:
`curve`/`scatter`/`error_bar`/`interval_highlight`/`heatmap`/`boxplot`; `role`
tag for theory/experiment/simulation/residual/fit; `highlights`/`markers`
lists; `axes.x.scale`/`axes.y.scale` = `"linear"` (default) or `"log"`; a
boxplot series is `{name: category, values: [y values]}` rather than the
x/y-paired `points` shape used by the other kinds) and the
"zero-judgment rendering layer" design (the figure script never decides
whether a number is physically correct — that remains the job of the
dimensional/boundary gates upstream) is specified in
`dev-notes/self-tests/03/charting_generic_architecture.md` §2. `figures`
may be empty or absent entirely — charting is an optional node (SKILL
Node 2.7), not a required one.

## Figures sub-schema, extension: `interactive` and `interactive_live` kinds (v2.2/v2.3, optional)

In addition to the six static kinds above, two optional, on-demand Plotly-backed
kinds are supported (see `dev-notes/interactive_figure_design.md` §2, §6 and
`dev-notes/self-tests/03/charting_generic_architecture.md` §9, §10 for the full
field specs — this section is just the schema-level summary, not a duplicate):

- **`interactive`** — renders a self-contained HTML fragment (rotatable/zoomable,
  can switch between several **pre-computed** series via Updatemenu buttons). Only
  valid for switching between data that was already computed upstream; it does
  **not** re-solve anything. Fields: `backend` (currently only `"plotly"`),
  `layout_3d` (optional bool), `series` (reuses the existing name/points shape,
  plus an optional `z` when `layout_3d=true`), and an optional `switcher` object
  that declares the series are meant to be toggled between (adds the button UI).
- **`interactive_live`** — renders a 2D curve y = f(x; p) where the user drags
  1..N parameter sliders and y is **re-computed live in the browser** on every
  slider `input` event (GeoGebra-style "drag a parameter, watch the curve
  re-draw in real time"), still fully static / no server / no external CDN —
  the closed-form expression is mirrored as inline JavaScript and pushed into
  the existing Plotly trace via `Plotly.restyle()`. **Only valid for cheap
  closed-form re-evaluation, not for re-solving a heavy numerical ODE/PDE**; if
  a parameter genuinely requires re-simulation to get a new y, use `interactive`
  (pre-computed parameter sweep + switcher) instead and say so in the title.
  Fields: `x_data` ({values: [x grid], label}), `y_label`, `params`
  (list of {name, label, min, max, step, initial} — one slider each),
  `constants` (optional, extra fixed values the JS body can read, e.g. mode
  frequencies/amplitudes shared across the curve), `js_function_body` (the
  inline JS expression — body only, not the full `function(P){...}` wrapper, which
  the renderer adds — that returns the new y-array given the current parameter
  object `P`; kept deliberately narrow / arithmetic-only, see the security note
  in `make_report_figures.py`'s `_render_interactive_live()` docstring), and
  `live_model_note` (a one-sentence statement that this slider re-computes a
  cheap closed-form expression client-side, not a live re-solve of the underlying
  numerical model — strongly encouraged; its absence triggers a WARNING at
  render time, matching this project's "never silently paper over a missing
  piece of output" rule).

  Optional enhancement fields (all default-absent, fully backward-compatible —
  a spec that omits them renders exactly the same widget as before these were
  added; added 2026-10-09, learning general UX patterns from a third-party
  self-contained realtime-FEM reference file, see
  `dev-notes/self-tests/03/figures_interactive_test/
  reference_fem_realtime_simulation_notes.md`):
  - `y_range_pin` ([lo, hi], optional): pins the y-axis range so it does not
    thrash/re-auto-range on every slider drag (previously `Plotly.restyle()`
    could recompute auto-range each time, causing visible axis jitter — the
    same UX problem the reference file solves with temporal smoothing of its
    colorbar range, generalized here to a fixed range instead of a moving
    average, since our curve is 1-D not a scrolling frame).
  - `verify_reference_js` (JS expression in `P`, returning a single number,
    optional) OR `verify_reference_value` (a fixed number, optional), plus an
    optional `verify_reference_label` (string): when present, the widget
    shows a live readout next to the curve comparing the current
    closed-form result's grid-mean against this independently-derived
    reference value (deviation, absolute + %), turning the numeric
    sanity check from a build-time-only diff into something a report
    reader can see on-screen — the reference file's "cheap analytic model
    as order-of-magnitude cross-check" pattern, generalized to our
    closed-form case. `verify_reference_js`, when given, is subject to the
    same narrow sandbox as `js_function_body` (no DOM/fetch/eval/network).

Both kinds write a self-contained `<figure_id>.html` fragment (not a PNG/SVG);
Node 4's `trace_visualizer.py` inlines it directly (not via base64 `<img>`),
reusing the same `{{figure: <id>}}` placeholder mechanism and `--figures-dir`
argument as the static kinds — no new flags or code paths needed on the
visualizer side. Neither kind changes any of the six static kinds' behavior or
requirement; both are optional Node 2.7 choices, not new mandatory steps.

