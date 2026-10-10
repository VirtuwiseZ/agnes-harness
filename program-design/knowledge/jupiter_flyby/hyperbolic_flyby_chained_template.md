# Method Template (Run #2, derived fresh - NOT imported from run #1's report text): Two-Body
# Hyperbolic Flyby + Chained-Encounter Construction for Outbound-System Gravity Assist

## Applicable Domain (mechanism-match statement, checked against the actual physics, not against
## the problem's keyword surface)
- A spacecraft (test mass) makes one or more close hyperbolic passes by a body moving on a
  nearly-circular orbit around a central mass, and we want the spacecraft's final velocity in
  the central body's frame after N encounters, compared against a reference propulsive-capture
  delta-v, to answer "does the maneuver save meaningful propellant?"
- Mechanism: pure gravity (two-body Rutherford scattering), NO aerodynamic drag, NO
  atmospheric entry - this is the mechanism-matched family for Jovian-moon gravity assists.
  The `atmosphere-drag-ode.md` template is explicitly rejected for this problem (see
  routing_decision_audit in the state file): its core assumption (drag-dominated descent
  through a structured rho(z)/T(z) medium) has no counterpart anywhere in this problem's
  physics, and silently force-fitting it would be a category error.

## Required Problem Parameters (load from `jupiter_flyby_params_run2.json`, re-derived this run)
- `v_inf_approach_m_s`: given by the problem statement, Jupiter frame.
- `mu_jupiter_m3_s2`: central-body gravitational parameter (standard IAU/JPL value, confirmed
  not derived this run, cross-checked in-model via Kepler's third law against each moon's
  independently known orbital period - a self-consistency check that does NOT depend on
  trusting mu_jupiter as a free constant, it ties it to an observable (the period)).
- `moons`: {name: {a_m, M_kg, R_m}} x 4 (Io, Europa, Ganymede, Callisto).
- `capture_orbit_candidates`: target orbital radii for the reference direct-capture burn.
- `propulsion_baseline.Isp_s`: for the Tsiolkovsky propellant-fraction conversion.
- NEW this run, `overtaking_control_flag`: a boolean toggle that computes, for the SAME four
  moons and same perigee sweep, the OVER TAKING geometry (v_rel = v_inf - v_moon, spacecraft
  catching up to the moon from behind, NOT the classic case - this is the control case that
  PROVES the head-on vs. overtaking asymmetry is a real physical effect and not an artifact of
  one particular vector arrangement).
- NEW this run, `chained_encounter`: a {moon_A, moon_B, geometry_per_encounter, wait_strategy}
  spec for a TWO-encounter construction, described below as Template Step 4b (a genuinely new
  analytical step not in run #1's model or template).

## Template Steps (each produces an auditable artifact, per pipeline convention)

0. Data-Source Routing (Node 1.5, done in the run, recorded in the state file - not re-listed
   here since it's a pipeline node, not a step of THIS template).

1. **Per-moon circular-orbit velocity + mu_moon**
   - `v_moon = sqrt(mu_jupiter / a_m)` (circular-orbit assumption, flagged - real Galilean
     moons have small eccentricities, <0.01, negligible at the precision level this problem
     operates at; the assumption is recorded, not silently dropped).
   - `mu_moon = G * M_moon` for each of the four moons.
   - Dimensional Gate on `sqrt(mu_j/a)` and `G*M`.

2. **Single-encounter head-on (closing) kinematics - the run #1 core result, re-derived,
   not copied**
   - `v_rel_closing = v_inf + v_moon`
   - `e = 1 + r_p * v_rel_closing^2 / mu_moon`
   - `delta = 2 * asin(1/e)`
   - `v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)`  (head-on exit vector
     arrangement; see vector-geometry note below for why this specific sign convention is
     the DECCELERATION case, and Step 4 for the speed-UP case)
   - Dimensional Gate on `e`, `delta`, `v_out^2` (delta is in radians - a genuine dimension-
     check gotcha: asin()'s argument must be dimensionless, verify `1/e` is, verify `delta`
     itself is dimensionless, record this explicitly rather than assume it).
   - NEW explicit invariant, derived this run: prove algebraically (symbolically, via sympy,
     not by numerical coincidence) that for ANY v_moon > 0 and ANY delta in (0, pi), the
     head-on expression satisfies `v_out^2 - v_inf^2 = v_moon^2 + 2*v_inf*v_moon +
     2*v_moon*(v_inf+v_moon)*(1-cos(delta)) > 0` - i.e. v_out is STRICTLY greater than v_inf
     for any finite positive deflection. This invariant is the formal proof that a single
     head-on encounter CANNOT decelerate, and it is derived independently this run (run #1
     reached the same conclusion by numerical inspection of four data points; this run
     elevates it to an exact algebraic identity, which is a strictly stronger and cleaner
     result, and it is recorded as its own auditable artifact, not buried in a code comment).

3. **Direct-capture reference burn (the denominator of "how much does the assist actually
   save")**
   - `v_peri = sqrt(v_inf^2 + 2*mu_jupiter/a_target)` (specific-energy at perijove of the
     incoming hyperbolic trajectory, evaluated at the target orbit's radius - the spacecraft
     must still have the full 20 km/s hyperbolic excess at this point if no assist has
     happened)
   - `v_circ = sqrt(mu_jupiter/a_target)`
   - `delta_v_direct = v_peri - v_circ`
   - `propellant_fraction_direct = 1 - exp(-delta_v_direct/(Isp*g0))`
   - Dimensional Gate on each.

4. **Step 4a: Single-encounter overtaking CONTROL (new this run, proving asymmetry)**
   - `v_rel_overtake = v_inf - v_moon`  (spacecraft approaching the moon from BEHIND, same
     orbital direction; this is actually the geometry that gives a speed-UP relative to
     Jupiter, which is why it is labeled a CONTROL and not a candidate deceleration
     geometry - it is here to show the numbers move in the OPPOSITE direction, proving the
     head-on "no meaningful deceleration" result is not an accident of vector bookkeeping)
   - Same Steps 2's formulas (e, delta, v_out) applied with this v_rel, swept over the same
     perigee grid, for the same four moons.
   - Expected (from run #1's prior, to be re-verified not assumed): v_out OVERTAKING > v_moon
     by a genuinely large margin (this is the classic "slingshot gains speed" case, and it
     is the physically-correct mirror of why head-on closing can't help).

5. **Step 4b (NEW this run, genuinely new analytical step, not in run #1): Chained two-
   encounter construction - the actual mechanism that CAN produce a large net velocity
   change, quantified analytically**
   - Encounter 1: head-on flyby of Moon A (from Step 2), perigee r_p_A = R_A (tightest
     safe flyby). Result: v_out_1, essentially unchanged from v_inf (Step 2's invariant),
     BUT the exit DIRECTION has been rotated by delta_1 relative to the incoming direction
     (this is the part of the encounter that DOES actually happen - the speed barely moves,
     the direction changes by a small but nonzero angle delta_1, and that direction change
     is the resource a second encounter can use).
   - Encounter 2: a SECOND flyby, this time of a DIFFERENT moon B, chosen so that B's
     orbital velocity at the intercept point is nearly ANTI-PARALLEL to v_out_1's direction
     (i.e. B is "in front of" the spacecraft's new heading, not behind it - the spacecraft
     has to wait a carefully chosen fraction of B's orbital period for B to arrive at that
     intercept point; the wait costs mission time, not spacecraft fuel - this is a genuine,
     quantified tradeoff, not hand-waving).
   - Encounter 2 uses the SAME closed-form as Step 2 but with v_rel_2 = |v_out_1 - v_moon_B|
     (now a GENUINELY smaller closing speed, because v_out_1's direction after encounter 1
     is no longer the original approach direction - it has been partially redirected - so
     the vector difference to moon B's velocity is materially smaller than the original
     v_inf+v_moon closing speed, producing a MATERIALIALLY LARGER deflection angle
     delta_2 than the tiny delta_1).
   - Net result after encounter 2: v_out_2, compared against v_inf, with the SAME
     algebraic-invariant tool from Step 2 re-applied to check whether THIS time the net
     change can be negative (a true deceleration) - the chained case is exactly where the
     "no" answer from Step 2 gets stress-tested, and whether it holds or flips is a
     genuinely new result this run must compute, not assume.
   - Dimensional Gate + the same explicit algebraic invariant check, applied to the
     two-encounter composition, not just the single-encounter one.

6. **Verification (independent, per Node 1.5's chosen baseline, NOT the modeling input)**
   - Independent energy-balance identity (different formula path than Steps 1-5): total
     specific orbital energy of the spacecraft ABOUT JUPITER, evaluated (a) far upstream
     before any encounter, (b) immediately after encounter 1 using the vis-viva equation
     for a hyperbolic orbit with perijove = encounter 2's approach distance, (c) after
     encounter 2 - all three must reconcile via the same single scalar (energy), providing
     a check that does not re-derive the flyby formula itself, only checks it against a
     genuinely different conservation law.
   - Real-mission plausibility anchor (independent physical object + dataset, per Node 1.5):
     Voyager 2's 1979 Jupiter encounter produced a large, published, well-documented
     Jupiter-frame velocity change - cross-checked against this model: does the model
     predict a deflection angle in the same order of magnitude as Voyager's actual
     geometry, when fed Voyager's actual encounter parameters (perigee distance, approach
     speed relative to Jupiter, Jupiter's mu - NOT a Galilean moon's mu)? If yes, the
     two-body flyby formalism itself is validated against real data; the question that
     remains purely open is whether that SAME formalism, applied to a Galilean MOON's much
     smaller mu and much smaller R, produces a delta-v large enough to matter - and that
     is exactly what Steps 2/4/5 answer, and they are expected (to be confirmed, not
     assumed) to say "no for a single encounter, potentially yes for the chained
     construction."

7. **Boundary Gate (degenerate limits, independent of Steps 1-6's main sweep)**
   - v_inf -> 0: spacecraft barely arriving; does the formula still give a sensible answer?
     (Expected: yes, delta grows, v_out -> v_moon, a "capture-by-gravity-only" limit that
     should reduce to a well-known result - a sanity check against the circular-orbit
     energy of the moon itself).
   - r_p -> 0 (perigee much smaller than any physical R_moon, purely a mathematical
     limit): delta -> approach a hard limit; verify the formula doesn't produce NaN or a
     spurious "infinite deflection" artifact at this limit - it should approach delta ->
     180 deg (a perfect retrograde flip), which is the most favorable case possible for
     any single-encounter deceleration claim, and even THAT maximum case must be checked
     against the acceptance threshold to confirm the "not feasible" verdict is robust even
     to the single most-optimistic single-encounter limit, not just the realistic
     surface-skim value.
   - mu_moon -> 0: deflection -> 0, v_out -> v_inf exactly (trivial no-op limit, must
     reproduce v_inf to machine precision as a degenerate-case correctness check, not just
     "close").
   - v_moon -> infinity (unphysical, but a genuine algebraic test of the invariant's robust-
     ness under extreme parameter values): the "v_out >= v_inf for head-on" invariant should
     still hold - verify it does not accidentally rely on v_moon being modestly sized.

8. **Parameter sweep + figure generation (the part run #1's figures got wrong, redesigned
   this run)**
   - Perigee sweep: r_p from R_moon to ~10x R_moon, log-spaced, for ALL FOUR moons, BOTH
     head-on and overtaking geometry - 4 moons x 2 geometries = 8 curves total, NOT the
     2 near-blank curves run #1 produced. Every curve must visibly deviate from the trivial
     "v_out = 20 km/s" reference line somewhere in its range - if a curve does not, that is
     itself a finding to state explicitly, not hide with a y-axis zoom that makes it look
     flat by accident.
   - Full 2D parameter surface: x-axis = perigee factor (r_p/R_moon, 1 to 10), y-axis =
     which moon (4 discrete rows), color/height = propellant-saving-fraction, one heatmap
     per geometry (head-on vs. overtaking) - 2 heatmaps total, plus one for the CHAINED
     construction's net saving, giving 3 genuine 2D information-bearing surfaces, not 1D
     lines that happen to hug a horizontal reference.
   - Chained-construction velocity progression plot: a discrete step diagram (not a
     continuous curve - the chain is a sequence of discrete encounters with waits between
     them, so a staircase-style plot with labeled encounter points is the honest visual
     form, not a fake-continuous interpolation).

9. **Conclusion + traceability (per report_structure_guide.md, not run #1's report)**
   - Explicit pass/fail verdict against BOTH acceptance thresholds (10% propellant fraction,
     1 km/s delta-v), stated separately for: single head-on encounter, single overtaking
     encounter (as a labeled control, not a candidate), and the chained construction.
   - Every number in the conclusion carries a `problem_state.json` traceability pointer
     (audit-log record + artifact hash), never a bare citation of "the model says."

## Failure / Annealing Triggers
- If the symbolic invariant from Step 2 FAILS to hold for the chained case (Step 5) in a
  way that produces v_out_2 < v_inf by more than machine precision: this is the FIRST
  signal the "no" answer is actually wrong - investigate before reporting, do not paper
  over it. If it holds and v_out_2 is still >= v_inf: the "no" answer is robust across
  both single AND chained constructions, which is a stronger final verdict than run #1's,
  and worth calling out explicitly as the run #2 contribution.
- If any figure in Step 8 renders as visually near-blank (the exact failure mode the user
  flagged in run #1): re-examine the axis scaling / data range BEFORE accepting the figure
  - a figure that hides a real effect by bad axis choice is not a valid artifact and must
  be regenerated, not shipped.
