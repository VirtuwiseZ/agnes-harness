# Method Template: Boundary / Degenerate-Limit Verification

## Purpose
Before a modeling result is trusted, this template forces a check that the governing
equations behave sanely under physically degenerate limits. A model that passes the
normal case but produces a nonsense limit (e.g. infinite velocity as mass→0, or a
negative "optimum" length) is **rejected** regardless of how clean the main-case
numbers look.

## Required Inputs
- The governing equation(s) or numerical model being tested (e.g. an ODE solver function,
  a symbolic expression, or a parameterized formula).
- A named "primary result" that the model is trying to optimize or predict
  (e.g. `max_safe_altitude`, `v_max` at release, optimal arm lengths).

## Template Steps

1. **Enumerate the boundary cases** relevant to this physical system:
   - Each independent mass parameter → 0 and → ∞
   - Each length / altitude parameter → 0 and → its physical ceiling
   - Each rate / coupling parameter (e.g. CD, friction coefficient) → 0 and → ∞
   - Gravity → 0 (free-floating limit)
   - Initial condition → its extreme endpoints (rest vs. maximum stored energy)

2. **For each boundary case, assert a physical expectation**, stated as a plain check:
   - Result must stay finite (no NaN / ±∞).
   - Result must have the correct sign / monotonicity (e.g. longer sling ⇒ never less
     launch speed; higher CD ⇒ never faster fall).
   - Result must reduce correctly to a known simpler problem where one exists
     (e.g. CD=0 ⇒ pure gravitational free-fall formula, r_slip→0 ⇒ simple pendulum).

3. **Execute the checks** via the `boundary_gate.py` hook (deterministic, not LLM-judged):
   - The hook takes the model's callable + the enumerated limits and reports PASS/FAIL
     per case, with the actual numeric value vs. the asserted expectation.

4. **Only if all cases PASS** may the pipeline advance to the conclusion node.
   Any single FAIL is logged to `problem_state.json.anomalies` and forces a roll-back
   to the hypothesis layer to re-examine the assumption that produced the broken limit.

## Examples (2010 Trebuchet boundary cases — the designated "boundary demo" problem)
| Boundary | Physical expectation |
|---|---|
| counterweight height `h → 0` | stored PE → 0 ⇒ launch speed → 0 |
| sling length `r3 → 0` | projectile effectively pinned to arm ⇒ speed bounded, no amplification |
| counterweight mass `m1 → ∞` | beam/counterweight dominates ⇒ projectile speed → finite cap, not ∞ |
| beam mass `m2 → 0` | energy transfers more fully to projectile ⇒ speed increases monotonically |
| gravity `g → 0` | no stored gravitational energy ⇒ launch speed → 0 even if `h` fixed |

## Failure / Annealing Triggers
- If a limit produces an unphysical sign, blow-up, or monotonicity violation: do NOT
  patch the numerical solver — roll back to the governing-equation / hypothesis layer
  and re-derive that limit by hand before re-running.
