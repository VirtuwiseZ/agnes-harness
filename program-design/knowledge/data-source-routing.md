# Method Template: Data-Source Routing (Node 1.5)

## Applicable Domain
Any physics problem whose modeling or verification step needs external data
(atmospheric profiles, reference mass/velocity baselines, material property
tables, published experimental curves, etc.). This template is deliberately
**problem-agnostic**: it prescribes *how to decide which source to use*, not
*what the answer is* for any specific problem. The specific source chosen is
always an output of running this procedure, never an input baked into code or
a fixed JSON field.

## Inputs (already fixed before Node 1.5 runs)
- The task spec from Node 1 (`task` block in `problem_state.json`).
- The matched method template from Node 2a (e.g. `atmosphere-drag-ode.md`)
  and its domain parameter JSON (e.g. `space_diving_params.json`) — treated
  only as *candidates to be confirmed or rejected here*, not as settled
  inputs the code may lean on.

## Decision procedure (executed in order)

1. **State the data requirement, not the source.**
   - Write down, in the audit log: "this problem needs `T(z)` and `ρ(z)`
     over the span [z_min, z_max] with step Δz ≈ N km, used only as ODE
     input coefficients; needs an independent real-data baseline for the
     model's v–z / a–z curve to be validated against, chosen so it is
     *independent* of the source used for the ODE input (do not validate a
     model against data pulled from the same source the model was built on,
     if independence is achievable)."

2. **Rank candidate access methods by reliability and fit.**

   Rank in this order, **testing each candidate for real, live availability
   before promoting it to the next step** (a candidate that is documented
   but does not actually resolve right now counts as *not* available at its
   level, and must be dropped to the next level — see step 4's availability
   check):

   - **Level 0 — locally installed, verifiable Python package** (preferred
     whenever it covers the required span/precision; cheapest to verify, no
     network dependency at all): check by attempting the actual import/use
     call *right now* in the working environment, e.g. `import ambiance`
     and call its atmosphere function over the required altitude span to
     confirm it returns sane, finite values for the specific z-range this
     problem needs (a library being importable is NOT sufficient — confirm
     its *stated validity range* actually covers this problem's span, e.g.
     `ambiance`'s 0–80 km Standard-Atmosphere-style range vs. a problem
     that needs up to 150 km — if the span exceeds what the library states
     as valid, that part of the span must fall through to Level 1/2/3 even
     though the import itself works). Log the actual function call + a small
     sample of returned values as the audit artifact for this level.
   - **Level 1 — live API / published data service** (for spans or precision
     beyond what any locally installed package claims, or when no local
     package fits): confirm it is reachable *right now* (do a live test
     fetch, log the actual response), not just documented.
   - **Level 2 — published static numeric table / dataset attachment**
     (e.g. a journal paper's supplemental data file, a published standard
     atmosphere table): acceptable when Levels 0 and 1 are unavailable or
     out-of-span for part of the required range. Log the exact citation +
     where the numbers will be transcribed from.
   - **Level 3 — published analytical approximation**: only when Levels 0,
     1, and 2 are genuinely unavailable or out-of-span; must cite the
     approximation's stated validity range, and flag any part of the
     required span that falls outside that range as a model-validity caveat
     in the final report.

   A single problem may *legitimately* need a **mixed-level** answer (e.g.
   Level 0 for 0–80 km + Level 3 for 80–150 km of the same T(z)/ρ(z)
   requirement): this is allowed and must be recorded as such in step 3's
   `span_covered` field, not papered over by pretending one source covered
   the whole range.

3. **Select one method + one concrete source (possibly a multi-level mix),
   and log the decision.**
   - Record in `problem_state.json`:
     - `data_source_decision.atmosphere_source = { name, access_method
       (api/table/analytic), span_covered, precision, fetched_at (timestamp)
       }`
     - `data_source_decision.verification_baseline = { name, independent_of
       (boolean: is it a different source than the modeling input), citation }`
     - A plain-language `rationale` field explaining why this level was
       chosen over the others (this is the "agent decision" that the
       competition's external-capability audit trail is meant to surface —
       the decision itself, not just the source name).

4. **Do a live availability check before downstream nodes run.**
   - If Level 1: actually fetch one small test sample of the required data
     right now, store its hash as an audit artifact. If the fetch fails,
     fall back to Level 2/3 *and log the failure* (do not silently proceed
     with stale cached data pretending the live call worked).
   - Log the check result as `data_source_decision.availability_check =
     { ok: true/false, sample_artifact_id, fallback_reason (if any) }`.
   - For a Level 0 (local package) source, the "live test fetch" is the
     actual Python call that pulls sample values from the package right
     now; store that sample (e.g. T(z)/ρ(z) at a few test altitudes) as a
     hash-logged artifact, so the audit trail proves the local library was
     *exercised*, not just imported.

5. **If no candidate source is credible or reachable:**
   - This is a *data-source fallback event*, distinct from the physical
     "annealing" rollback (which rolls back to the Hypothesis Layer). Do
     not reuse the annealing mechanism for a missing/inaccessible data
     source. Record it in `problem_state.json` as an `anomaly` of type
     `"data_source_unavailable"`, then trigger the **Human-Intervention
     Branch** (step 5a) instead of stopping dead or guessing the data.

   **5a. Human-Intervention Branch (fault-tolerance checkpoint)**

   When the agent *has made a clear recommendation* for which source/data it
   wants but *cannot fetch it itself* (e.g. paywall, API down, login wall,
   no public mirror), the agent MUST pause automated execution and hand the
   decision back to the user, presenting two explicit options:

   - **Option A — "Manual fetch + handoff"**: the agent outputs a concrete,
     step-by-step retrieval guide for the user (exact URL / dataset name /
     table citation, expected file format and column layout, the exact
     altitude/span/step values to extract, and where in
     `problem_state.json` / which artifact slot to drop the numbers back
     into). The agent then *waits* for the user to supply that data before
     resuming Node 2b. Log this as `data_source_decision.manual_fetch_guide`
     (guide text) + `anomalies += data_source_unavailable (reason, options
     offered, user_choice: pending)`.

   - **Option B — "Proceed on existing analytical/model approximation"**: the
     agent substitutes a documented approximation (e.g. the derived ideal-gas
     density formula the paper team itself used as a cross-check, or a
     published analytical temperature model) for the missing data, clearly
     flagged in the final report as "approximation used in place of
     [source X], accuracy caveat: [stated validity range]". This is a
     *deliberate downgrade*, not a silent one — the caveat must be visible in
     Node 3's report, not buried in code.

   The agent may not pick Option B on its own without the user's explicit
   confirmation, because choosing to skip the data step changes the
   epistemic status of the final answer ("validated against real data" vs.
   "validated against an approximation") and that is a user-visible, not
   agent-unilaterally-decidable, quality tradeoff. Log the user's choice as
   `anomalies[-1].user_choice` once they respond.

   If *even the analytical fallback in Option B is inadequate* (e.g. the
   required span falls entirely outside the approximation's stated validity
   range, so proceeding would be a fabricated result), the agent MUST
   decline to proceed and instead stop with a plain explanation of why no
   option is currently viable, rather than forcing a low-confidence answer
   through the pipeline.

## Optional enhancement: exposing the chosen source via a local MCP Server (Level 0 only, not required)

Wrapping a Level 0 local package (e.g. `ambiance`, `scipy.constants`) in a
local stdio MCP Server (using `fastmcp`/`mcp` SDK) is a *presentation-layer
option*, not a data-reliability requirement: it makes the tool easier for a
different Agent client to discover, but the physics correctness and
provenance guarantee comes entirely from the Level 0 import + sample test
above, not from the MCP wrapper. If the environment already has a suitable
local package that passes the Level 0 check, **do not gate progress on
building an MCP Server** — that is optional tooling convenience, not part
of the decision procedure. If no suitable local package exists, do not jump
to building an MCP wrapper for a source that has not yet passed its own
Level 1/2 availability check.

## What this step must NOT do
- Must NOT write the chosen source name into the ODE/model code; the model
  only ever receives a structured array, and the array's provenance lives
  in this step's audit record.
- Must NOT treat a value in a domain parameter JSON (e.g. a "candidate"
  source name stored there) as the decision — the JSON value is only the
  starting hint for step 2's ranking, and the actual chosen source +
  rationale must still be produced by this procedure and logged fresh.

## Output
A completed `data_source_decision` block in `problem_state.json`, ready for
Node 2b to consume as "a structured data array + its recorded provenance",
and (if Level 1/2) the actual fetched data artifact, hash-logged.
