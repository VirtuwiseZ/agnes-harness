# Method Template: Parameter Sensitivity Analysis

## Purpose
Once a primary result passes the normal-case and boundary checks, this template asks:
**how robust is the result to reasonable uncertainty in the input parameters?** A result
that only survives a ±1% parameter wiggle is fragile; one that survives a wide,
physically motivated uncertainty band is defensible to a reviewer. This template
quantifies that band explicitly instead of asserting it.

## Required Inputs
- The primary result function `f(params)`, where `params` is a dict of the physical
  quantities the result depends on (e.g. `m_total`, `CD_transonic`, `A_supersonic`,
  initial altitude).
- A "baseline" parameter set (the one used for the headline result, typically from the
  domain JSON).
- An uncertainty / swing range for each parameter, motivated by real-world variation
  (e.g. CD estimate ±50%, area ±20%, mass ±10%), not arbitrarily chosen.

## Template Steps

1. **Define the uncertainty band for each parameter** and record it as an explicit
   hypothesis (each band and its justification logged into `problem_state.json`
   audit trail).

2. **Sweep each parameter independently** across its band while holding all others at
   baseline (one-at-a-time, OAT), and record `f` at the band's center, low, and high.

3. **Identify the dominant parameter(s)**: the one(s) whose band produces the largest
   relative change in `f`.

4. **Optional (if time/complexity allows)**: a small two-way or random-latin-square
   cross sweep to catch any strong interaction between the top-2 dominant parameters.

5. **Report**: state the headline result together with its propagated uncertainty
   (e.g. "max safe altitude = 94 km, and remains above the 5G safety floor even if
   CD is 50% higher than estimated"), with each number traceable to the sweep artifacts.

## Why This Matters for the Project's Review
The competition explicitly demands a result-verification method. Sensitivity analysis is
the cheapest way to demonstrate that the headline conclusion is not a knife-edge accident
of one specific parameter value, reinforcing the "not just LLM-generated" requirement.

## Failure / Annealing Triggers
- If flipping a single parameter across its (reasonable) band makes the headline
  conclusion **change sign or category** (e.g. "safe" flips to "unsafe"), that is a
  strong signal the underlying physical assumption (not the numerical method) is the
  fragile part — roll back to the hypothesis layer and re-examine that assumption, not
  the sweep code.
