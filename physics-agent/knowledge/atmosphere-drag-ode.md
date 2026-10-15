# Method Template: Atmosphere-Drag ODE Descent Solver

## Applicable Domain
- Vertical free-fall / descent problems where aerodynamic drag dominates,
  and the atmosphere's temperature / density vary significantly with altitude
  (space dive, high-altitude parachute, re-entry, meteoroid deceleration).

## Required Problem Parameters (to load from a domain JSON, e.g. `space_diving_params.json`)
- `mass_total_kg`: total descending mass (incl. suit/parachute).
- `safety_constraints`: G-force limits and durations that cap the safe result.
- `baumgartner_benchmark` (or equivalent real-data set): for independent verification.
- `aerodynamic_coefficients`: `CD` per flight regime (subsonic / transonic / supersonic)
  and cross-sectional area per regime.
- `atmosphere_data_source`: **not named in the template** — this is decided at
  runtime by the Data-Source Routing step (Node 1.5) based on the problem's
  conditions, not fixed here. The template only requires that a `T(z)` / `ρ(z)`
  structured array be available as a modeling input, however it was obtained.
- `verification_baseline`: likewise decided at runtime (Node 1.5), not fixed in
  the template; for a space-diving problem this will typically be a documented
  real jump record, but that is an *output of analysis*, not an assumption the
  template bakes in.

## Template Steps (executed in order, each producing an auditable artifact)

0. **Data-Source Routing (Node 1.5 — done before this template's steps 1–6
   begin, per the pipeline)**
   - Assess, for *this specific problem*: what atmospheric T(z)/ρ(z) source is
     actually obtainable/appropriate (API, published table, or a published
     analytical approximation), and what public dataset is the right
     independent verification baseline.
   - Log the decision + rationale into `problem_state.json` audit logs.
   - Steps 1–6 below must treat the chosen source purely as "a structured data
     array handed in", never by name.

1. **Atmosphere characterization**
   - Obtain T(z) and ρ(z) over the full altitude span of interest (0–150 km in
     1 km steps for space diving), **from whatever source Node 1.5 selected**.
   - Log: `tool_call`, `source=<the Node 1.5-chosen source, recorded at runtime,
     not fixed here>`, `artifact_id=<hash>`.
   - Store T(z), ρ(z) arrays as a numerical artifact; do NOT embed them as
     literals in any later ODE code.

2. **Define piecewise drag regime**
   - Define Mach-number thresholds (e.g. 0.8 entry, 1.2 exit of transonic band).
   - Assign `CD` and cross-section `A` to each regime per the domain JSON.
   - Record this as an explicit hypothesis table (not implicit in code).

3. **Build the ODE**
   - `dv/dx = g_eff(z) − (ρ(z)·CD·A/(2m))·v²` integrated over falling distance `x`
     (or time `t`), with `g_eff` accounting for altitude if required.
   - **Dimensional Gate**: verify every term carries consistent SI dimensions before
     any numerical integration begins (call the `dimensional_gate.py` hook).

4. **Numerical integration**
   - Use a standard ODE solver (e.g. `scipy.integrate.solve_ivp`); do not hand-roll a
     first-order Taylor method unless the problem specifically calls for it.
   - Sweep the input of interest (e.g. initial altitude) over a defined range and record
     the extremum of the acceleration profile vs. initial altitude.

5. **Verification**
   - **Boundary Gate**: check degenerate limits (e.g. CD→0 pure gravity, CD→∞
     instantaneous stop, mass→0 or ∞) before trusting the swept result.
   - **Empirical check**: compare the model's v(x)/a(x) curve against the
     independent baseline chosen in Node 1.5 (for a space dive, typically a
     documented real jump record such as the 2012 39 km jump — but which
     specific record is the Node 1.5 decision, not this template's assumption),
     and quantify the mismatch.

6. **Conclusion**
   - State the maximum safe altitude with its traceability badge pointing at the
     specific integration artifact + verification artifact that produced it.

## Failure / Annealing Triggers (handled by the Quota & Rollback hook)
- If the ODE integrator diverges, returns NaN, or the swept extremum lands at the
  edge of the sweep range: roll back to step 2 (re-examine the CD/regime hypothesis),
  not to the integrator code.
