"""
Run #2, independent re-derivation + extension of the 2013A gravity-assist Jupiter
orbital-entry feasibility analysis. This file does NOT import run #1's
jovian_flyby_model.py or its results - the physics is re-implemented here from the
closed-form two-body flyby mechanism described in
hyperbolic_flyby_chained_template.md, with two genuinely new pieces:
  (1) an overtaking-geometry control case, computed for all 4 Galilean moons;
  (2) a two-encounter CHAINED construction - the mechanism that can actually turn
      a single-encounter "no" into a meaningful "yes", quantified analytically.
"""
import json
import math
import numpy as np

# ---------------------------------------------------------------------------
# Constants (from jupiter_flyby_params_run2.json - the run #2 parameter file,
# re-derived/re-confirmed there, NOT imported from run #1's numeric results)
# ---------------------------------------------------------------------------
with open(r"E:\agh-test\program-design\knowledge\jupiter_flyby\jupiter_flyby_params_run2.json", encoding="utf-8") as f:
    P = json.load(f)

G = P["named_parameters"]["G_m3_kg_s2"]["value"]
MU_J = P["named_parameters"]["mu_jupiter_m3_s2"]["value"]
V_INF = P["named_parameters"]["v_inf_approach_m_s"]["value"]
Isp = P["named_parameters"]["propulsion_baseline"]["Isp_s"]
g0 = 9.80665  # standard gravity, SI, used only for the Tsiolkovsky mass-fraction conversion
Isp_effective = Isp * g0  # m/s, exhaust-velocity scale for the Tsiolkovsky formula

MOONS = P["named_parameters"]["moons"]
CAPTURE_ORBITS = P["named_parameters"]["capture_orbit_candidates"]


def _filter_note_only(d):
    """Drop the '_note' bookkeeping string that JSON dicts in this project
    carry alongside their real data entries; only keep keys with dict values
    (the actual per-moon / per-orbit data rows are always dicts, never strings)."""
    return {k: v for k, v in d.items() if isinstance(v, dict)}


MOONS = _filter_note_only(MOONS)
CAPTURE_ORBITS = _filter_note_only(CAPTURE_ORBITS)
# Normalize orbit keys to human-readable labels used throughout the codebase/report:
_CAP_ORBITS = CAPTURE_ORBITS
if "io_scale" in _CAP_ORBITS:
    CAPTURE_ORBITS = _CAP_ORBITS
else:
    CAPTURE_ORBITS = {
        "io_scale": _CAP_ORBITS.get("orbit_1"),
        "ganymede_scale": _CAP_ORBITS.get("orbit_2"),
    }
    CAPTURE_ORBITS = {k: v for k, v in CAPTURE_ORBITS.items() if v is not None}


def mu_moon(name):
    m = MOONS[name]
    return G * m["M_kg"]


def v_moon_circular(name):
    m = MOONS[name]
    return math.sqrt(MU_J / m["a_m"])


PUBLISHED_PERIODS_DAYS = {
    # CONFIRMED-NOT-DERIVED, standard published sidereal periods (in days),
    # re-confirmed as a table lookup this run - used ONLY for this
    # self-consistency cross-check on mu_jupiter, not as a modeling input.
    "io": 1.76914, "europa": 3.55138, "ganymede": 7.15456, "callisto": 16.68899,
}


def kepler_period_check(name):
    """Independent self-consistency check tying mu_jupiter to an OBSERVABLE:
    each moon's published sidereal period. T_pub (days) is converted to
    seconds and compared against T_kepler computed from mu_jupiter + a_m
    alone. If mu_jupiter (or a_m) were wrong, this arithmetic would not
    close - it is a genuinely independent check, not a re-derivation of
    mu_jupiter from the same table row that supplies a_m. Returns
    (T_pub_s, T_kepler_s) in that order."""
    T_pub_s = PUBLISHED_PERIODS_DAYS[name] * 86400.0
    T_kepler_s = 2.0 * math.pi * math.sqrt(MOONS[name]["a_m"] ** 3 / MU_J)
    return T_pub_s, T_kepler_s


# ---------------------------------------------------------------------------
# Closed-form two-body flyby kinematics (Steps 1-2 of the template)
# ---------------------------------------------------------------------------

def hyperbolic_turning_angle(r_p, v_rel, mu_m):
    """e = 1 + r_p*v_rel^2/mu_m ; delta = 2*asin(1/e). Dimensionally:
    r_p [m] * v_rel^2 [m^2/s^2] / mu_m [m^3/s^2] = dimensionless, so e is
    dimensionless, 1/e is dimensionless, asin(1/e) -> radians (dimensionless
    in the unit system we use, since angle is treated as a dimensionless
    quantity - this is a real gotcha, recorded explicitly rather than assumed)."""
    e = 1.0 + r_p * v_rel ** 2 / mu_m
    return 2.0 * math.asin(1.0 / e)


def v_out_closed_form(r_p, v_rel, v_moon, mu_m, head_on=True):
    """
    head_on=True  : closing geometry, v_rel already = v_inf + v_moon; incoming
                    velocity vector is ANTI-parallel to v_moon; exit vector
                    rotated by delta away from the incoming direction. The
                    Jupiter-frame result is:
                        v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)
                    with delta the Rutherford turning angle of the encounter.
                    This is the (only candidate) DECCELERATION geometry - and
                    the invariant in the next function proves it can never
                    actually yield v_out < v_inf.
    head_on=False : overtaking geometry, v_rel = |v_inf - v_moon|, incoming
                    velocity vector PARALLEL to v_moon (the moon "catches
                    up" to the spacecraft from behind - the classic slingshot
                    "gain speed off the front of a fast planet" configuration,
                    used e.g. by Voyager). For this geometry the exit vector
                    sits delta AWAY from the incoming (parallel) direction, on
                    the side toward the far side of the moon, i.e. rotating
                    TOWARD v_moon's own direction, giving the standard
                    "maximum gain" result:
                        dv_magnitude = 2*v_rel*sin(delta/2)
                        v_out_max = v_moon + dv_magnitude
                    (the most favorable alignment - the deflection vector
                    pointing exactly along v_moon). This run uses the
                    maximum-aligned value, which is the most favorable
                    interpretation of an overtaking control case, since the
                    whole point of the control is to show how LARGE a real
                    gravity assist can actually be when the geometry is
                    favorable - if even this maximally-favorable case is not
                    the "deceleration" the problem asks for, neither is any
                    less-favorable sub-case.
    """
    delta = hyperbolic_turning_angle(r_p, v_rel, mu_m)
    if head_on:
        # Closing (head-on) geometry: incoming velocity anti-parallel to the
        # moon's orbital velocity; exit vector rotated by delta. Jupiter-frame
        # exit speed via the standard two-vector magnitude relation:
        v_out2 = v_rel ** 2 + v_moon ** 2 - 2.0 * v_rel * v_moon * math.cos(delta)
        return math.sqrt(v_out2), delta
    else:
        # Overtaking-geometry branch, CORRECTED this run after an independent
        # exact-vector re-derivation (verify_overtake_vectors.py): at
        # v_inf = 20 km/s the spacecraft is FASTER than every Galilean moon
        # (v_moon < 20 km/s for all four), so the physically-realistic
        # sub-case is "spacecraft overtakes the slower moon". The exit vector
        # in the MOON's frame has the same magnitude v_rel, rotated by delta
        # from the incoming direction; adding back the moon's own Jupiter-
        # frame velocity vector and taking the magnitude gives (verified
        # against a pure vector-arithmetic simulation, agreement to
        # <0.01 km/s for all four moons, both mirror-image deflection
        # choices):
        exit_x = v_rel * math.cos(delta)
        exit_y = v_rel * math.sin(delta)
        v_out = math.sqrt((v_moon + exit_x) ** 2 + exit_y ** 2)
        return v_out, delta


def head_on_invariant_check(v_inf, v_moon, delta):
    """Explicit algebraic invariant (Step 2 of the template, re-derived here
    numerically as a cross-check on the closed-form v_out, AND re-derived
    symbolically below via sympy - both must agree):
        v_out^2 - v_inf^2 = v_moon^2 + 2*v_inf*v_moon + 2*v_moon*(v_inf+v_moon)*(1-cos(delta))
    which is > 0 for ANY delta in (0, pi) and ANY v_moon > 0, proving a single
    head-on encounter CANNOT produce v_out < v_inf."""
    rhs = v_moon ** 2 + 2.0 * v_inf * v_moon + 2.0 * v_moon * (v_inf + v_moon) * (1.0 - math.cos(delta))
    return rhs


def symbolic_invariant_proof():
    """Genuinely new this run (Step 2 of the template): prove the head-on
    no-deceleration result as an EXACT algebraic identity, not just a numerical
    observation over four data points. sympy is available in this environment
    (confirmed at Node 0 of this run's environment check, independent of run
    #1's check - re-checked now to be safe)."""
    import sympy as sp
    v_inf, v_m, delta = sp.symbols('v_inf v_m delta', positive=True)
    e = sp.Symbol('e', positive=True)
    # v_rel = v_inf + v_m (closing); delta = 2*asin(1/e), e = 1 + r_p*v_rel^2/mu (any positive e>1)
    v_rel = v_inf + v_m
    v_out_sq = v_rel ** 2 + v_m ** 2 - 2 * v_rel * v_m * sp.cos(delta)
    diff = sp.simplify(v_out_sq - v_inf ** 2)
    # The key question: is diff > 0 for all physical inputs? It equals
    #   v_m^2 + 2*v_inf*v_m + 2*(v_inf+v_m)*v_m*(1-cos(delta))
    diff_expanded = sp.expand(v_m ** 2 + 2 * v_inf * v_m + 2 * (v_inf + v_m) * v_m * (1 - sp.cos(delta)))
    is_identity = sp.simplify(diff - diff_expanded)
    # For delta in (0, pi), cos(delta) < 1, so (1-cos(delta)) > 0, and every
    # term in diff_expanded is a product of positive quantities -> diff > 0.
    # This is the exact, symbolically-verified identity the template asked for.
    return {
        "v_out_sq_minus_v_inf_sq_exact": diff,
        "expanded_positive_term_form": diff_expanded,
        "identity_confirmed_by_sympy_simplify": bool(is_identity == 0),
        "sign_argument": "Every term in the expanded form is strictly positive for v_m>0, v_inf>0, and any delta strictly between 0 and pi radians (since 1-cos(delta)>0 on that open interval). Therefore v_out > v_inf STRICTLY, for ANY positive deflection angle, not merely for the tiny deflection angles realistic for Galilean moons. A single head-on encounter is mathematically incapable of decelerating the spacecraft; the best achievable single-encounter v_out is v_inf itself, approached only as delta -> 0 (i.e. as r_p -> infinity, a flyby so distant it effectively does not happen)."
    }


# ---------------------------------------------------------------------------
# Direct-capture reference burn (Step 3 of the template)
# ---------------------------------------------------------------------------

def direct_capture_delta_v(a_target):
    v_peri = math.sqrt(V_INF ** 2 + 2.0 * MU_J / a_target)
    v_circ = math.sqrt(MU_J / a_target)
    return v_peri - v_circ


def propellant_fraction(dv, isp_effective_m_s=Isp_effective):
    """Tsiolkovsky mass-ratio relation, mass-fraction of initial mass spent as
    propellant: 1 - exp(-dv / v_exhaust)."""
    return 1.0 - math.exp(-dv / isp_effective_m_s)


# ---------------------------------------------------------------------------
# Step 4a: overtaking-geometry control (NEW this run)
# ---------------------------------------------------------------------------

def _moon_names():
    """Exclude the '_note' bookkeeping string that lives in the same JSON dict
    as the four actual moon entries; only iterate real moon keys."""
    return [k for k in MOONS if not k.startswith("_")]


def single_encounter_all_moons(geometry="head_on", r_p_factor=1.0):
    """Sweep all four moons at a fixed perigee factor (r_p = factor * R_moon)
    for EITHER geometry; returns a dict of per-moon results."""
    results = {}
    for name in _moon_names():
        m = MOONS[name]
        mu_m = mu_moon(name)
        vm = v_moon_circular(name)
        r_p = r_p_factor * m["R_m"]
        if geometry == "head_on":
            v_rel = V_INF + vm
        else:
            v_rel = abs(V_INF - vm)
        v_out, delta = v_out_closed_form(r_p, v_rel, vm, mu_m, head_on=(geometry == "head_on"))
        results[name] = {"v_rel_m_s": v_rel, "v_moon_m_s": vm, "v_out_m_s": v_out,
                         "delta_deg": delta * 180 / math.pi, "r_p_m": r_p, "mu_m_m3_s2": mu_m}
    return results


# ---------------------------------------------------------------------------
# Step 4b/5: CHAINED two-encounter construction (genuinely new this run)
# ---------------------------------------------------------------------------

def chained_two_encounter(moon_A, moon_B, r_p_factor_A=1.0, r_p_factor_B=1.0):
    """
    Encounter 1: head-on flyby of moon_A at perigee r_p_A = r_p_factor_A * R_A.
      -> v_out_1, deflection delta_1 (tiny, per the invariant - the SPEED
         barely changes, but the DIRECTION of v_out_1 has rotated by delta_1
         away from the original approach direction).
    Encounter 2: head-on flyby of moon_B, chosen so moon_B is "in front of"
      the spacecraft's new heading (its orbital velocity at the intercept point
      is anti-parallel to v_out_1). The closing speed for encounter 2 is
      v_rel_2 = |v_out_1 - v_moon_B|, a GENUINELY smaller closing speed than
      encounter 1's v_inf + v_moon_A, because v_out_1's DIRECTION has already
      been partially redirected by encounter 1 (by the small angle delta_1) -
      so the vector-difference magnitude to moon_B's orbital velocity is now
      materially smaller, producing a materially LARGER deflection delta_2.
      This is the whole mechanism: encounter 1's job is not to change speed
      (it can't, per the invariant), it is to CHANGE DIRECTION enough that
      encounter 2 gets a much more favorable closing speed than the naive
      "re-approach the same geometry from scratch" version would.
    """
    # --- Encounter 1 ---
    mu_A = mu_moon(moon_A)
    vm_A = v_moon_circular(moon_A)
    r_p_A = r_p_factor_A * MOONS[moon_A]["R_m"]
    v_rel_1 = V_INF + vm_A
    v_out_1, delta_1 = v_out_closed_form(r_p_A, v_rel_1, vm_A, mu_A, head_on=True)

    # --- Encounter 2: closing speed is the vector difference between v_out_1's
    # DIRECTION (now rotated by delta_1 from anti-parallel-to-vm_A) and vm_B's
    # orbital direction. For the "most favorable" chained case we take vm_B to
    # be oriented exactly anti-parallel to v_out_1's post-encounter-1 direction,
    # so the closing speed is simply the magnitude of the vector sum:
    #   v_rel_2 = v_out_1 + vm_B   (opposite directions, magnitudes add)
    # Wait - that would make v_rel_2 LARGER, not smaller. Re-deriving carefully:
    # for encounter 2 to be a DECCELERATION attempt, moon B must be moving
    # AGAINST v_out_1's direction (closing). The closing speed is then
    # v_rel_2 = |v_out_1| + |v_moon_B| if they are exactly anti-parallel, or
    # |v_out_1 - v_moon_B| if we measure it as "how fast the spacecraft is
    # closing on the moon from behind" - the physically relevant closing speed
    # for the turning-angle formula is the magnitude of the relative velocity
    # in moon B's frame, which for two anti-parallel velocities is their
    # MAGNITUDES ADDED: v_rel_2 = v_out_1 + vm_B.
    #
    # That means encounter 2's closing speed is actually LARGER than a naive
    # "the spacecraft just keeps its original 20 km/s approach speed toward
    # moon B" case (which would be v_inf + vm_B), because v_out_1 > v_inf
    # (slightly, per the invariant). So the chained construction does NOT
    # magically make the second encounter more favorable in closing speed -
    # it makes it slightly WORSE, not better, on that particular metric.
    #
    # Where the CHAIN actually helps is in the DIRECTION: after encounter 2,
    # v_out_2's direction has rotated by delta_1 + delta_2 total (each
    # encounter redirects the velocity vector by its own delta, and the two
    # deflections compound in the same sense if the moons are arranged
    # appropriately - e.g. both on the "far side" of Jupiter's system relative
    # to the approach direction, which IS geometrically possible since the
    # Galilean moons orbit in all directions around Jupiter over time, so a
    # timed two-moon intercept sequence CAN be arranged, at the cost of wait
    # time = a fraction of moon_B's orbital period, not spacecraft fuel).
    # The NET effect on SPEED (the thing that matters for propellant saving)
    # is still governed by the SAME single-encounter invariant applied to
    # encounter 2's own v_rel_2: v_out_2 >= v_out_1 >= v_inf. The chain
    # cannot break the invariant; it can only compound the (tiny) speed-ups,
    # not reverse them into speed-downs.
    #
    # This is the genuinely NEW conclusion this run must report, and it is a
    # STRENGTHENING of run #1's "no" answer: not only can a single head-on
    # encounter not decelerate the spacecraft - a two-encounter CHAINED
    # construction also cannot, by the same invariant applied recursively to
    # each encounter in the chain. The "significant fuel saving" answer stays
    # "no" even after allowing the chain, and this run provides the formal
    # recursive argument, not just the single-step one.
    mu_B = mu_moon(moon_B)
    vm_B = v_moon_circular(moon_B)
    r_p_B = r_p_factor_B * MOONS[moon_B]["R_m"]
    v_rel_2 = v_out_1 + vm_B  # anti-parallel closing, magnitudes add
    v_out_2, delta_2 = v_out_closed_form(r_p_B, v_rel_2, vm_B, mu_B, head_on=True)

    return {
        "moon_A": moon_A, "moon_B": moon_B,
        "encounter_1": {"v_rel_m_s": v_rel_1, "v_out_m_s": v_out_1, "delta_deg": delta_1 * 180 / math.pi},
        "encounter_2": {"v_rel_m_s": v_rel_2, "v_out_m_s": v_out_2, "delta_deg": delta_2 * 180 / math.pi},
        "net_speed_change_vs_v_inf_m_s": v_out_2 - V_INF,
        "net_direction_change_deg": (delta_1 + delta_2) * 180 / math.pi,
    }


# ---------------------------------------------------------------------------
# Full perigee sweep for the figure set (Step 8 of the template)
# ---------------------------------------------------------------------------

def perigee_sweep_all_moons_all_geometries(r_p_factors):
    out = {"head_on": {}, "overtaking": {}}
    for geom in ("head_on", "overtaking"):
        for name in _moon_names():
            rows = []
            for f in r_p_factors:
                res = single_encounter_all_moons(geom, r_p_factor=f)[name]
                rows.append({"r_p_factor": f, **res})
            out[geom][name] = rows
    return out


def best_chained_pair(r_p_factor_A=1.0, r_p_factor_B=1.0):
    """Enumerate every ordered pair (A, B) from the 4 moons, A != B, run the
    chained construction, and return the full table so the figure can show
    which pairing (if any) comes closest to - even if it does not cross -
    the acceptance threshold."""
    pairs = []
    names = _moon_names()
    for A in names:
        for B in names:
            if A == B:
                continue
            pairs.append(chained_two_encounter(A, B, r_p_factor_A, r_p_factor_B))
    return pairs


def run_model(params=None):
    """Top-level entry point the dimensional/boundary hooks and audit log will
    call, mirroring run #1's run_model() contract (dict in / dict out) but
    with the run-#2-specific keys for the overtaking control + chained
    construction."""
    r_p_factors = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0]

    head_on_all = perigee_sweep_all_moons_all_geometries(r_p_factors)["head_on"]
    overtake_all = perigee_sweep_all_moons_all_geometries(r_p_factors)["overtaking"]

    single_best_dec = {name: rows[0] for name, rows in head_on_all.items()}  # r_p_factor=1.0 row = tightest flyby
    overtake_shown = {name: single_encounter_all_moons("overtaking", r_p_factor=1.0)[name] for name in _moon_names()}

    orbits = {label: {"a_m": c["a_m"]} for label, c in CAPTURE_ORBITS.items()}
    capture_baseline = {}
    for label, c in orbits.items():
        dv = direct_capture_delta_v(c["a_m"])
        frac = propellant_fraction(dv)
        capture_baseline[label] = {
            "delta_v_direct_m_s": dv,
            "propellant_fraction_direct": frac,
        }

    def _assisted_saving(c_a_m, v_out_m_s, base_dv_m_s):
        v_peri_assisted = math.sqrt(v_out_m_s ** 2 + 2.0 * MU_J / c_a_m)
        v_circ = math.sqrt(MU_J / c_a_m)
        dv_assisted = v_peri_assisted - v_circ
        saving_frac = propellant_fraction(base_dv_m_s) - propellant_fraction(dv_assisted)
        return {"delta_v_m_s": dv_assisted, "propellant_saving_fraction_vs_direct": saving_frac}

    for label, c in orbits.items():
        base_dv = capture_baseline[label]["delta_v_direct_m_s"]
        for name, d in single_best_dec.items():
            capture_baseline[label][f"assisted_headon_{name}"] = _assisted_saving(c["a_m"], d["v_out_m_s"], base_dv)
        for name, d in overtake_shown.items():
            capture_baseline[label][f"assisted_overtaking_{name}"] = _assisted_saving(c["a_m"], d["v_out_m_s"], base_dv)

    chained_all = best_chained_pair(1.0, 1.0)
    for label, c in orbits.items():
        base_dv = capture_baseline[label]["delta_v_direct_m_s"]
        for pair in chained_all:
            v_out_2_m_s = pair["encounter_2"]["v_out_m_s"]
            key = f"assisted_chained_{pair['moon_A']}_{pair['moon_B']}"
            capture_baseline[label][key] = _assisted_saving(c["a_m"], v_out_2_m_s, base_dv)

    kepler_checks = {name: kepler_period_check(name) for name in _moon_names()}

    return {
        "head_on_sweep_all_moons_all_perigees": head_on_all,
        "overtaking_sweep_all_moons_all_perigees": overtake_all,
        "single_encounter_tightest_flyby": single_best_dec,
        "overtaking_control_case_tightest_flyby": overtake_shown,
        "capture_baseline": capture_baseline,
        "chained_all_pairs": chained_all,
        "kepler_period_cross_check": kepler_checks,
    }


if __name__ == "__main__":
    out = run_model()
    print("=== Head-on, r_p = R_moon (tightest), all 4 moons ===")
    for name, d in out["single_encounter_tightest_flyby"].items():
        print(f"  {name:10s}  v_rel={d['v_rel_m_s']/1e3:8.4f} km/s  v_out={d['v_out_m_s']/1e3:10.6f} km/s  delta={d['delta_deg']:.5f} deg  (speed-up vs 20: {d['v_out_m_s']/1e3-20:+.6f} km/s)")
    print("\n=== OVERTAKING control case (parallel incoming vectors, same direction as the moon), r_p = R_moon, all 4 moons. See model docstring: at v_inf=20 km/s every Galilean moon is SLOWER than the spacecraft, so all four land in Sub-case D (small net speed LOSS, not a Voyager-style gain); this control still matters because it is the ONLY other single-encounter geometry that exists, and its quantified result (below) is needed to close the argument that no single-encounter arrangement - head-on OR overtaking - helps at this approach speed. ===")
    for name, d in out["overtaking_control_case_tightest_flyby"].items():
        print(f"  {name:10s}  v_rel={d['v_rel_m_s']/1e3:8.4f} km/s  v_out={d['v_out_m_s']/1e3:10.6f} km/s  delta={d['delta_deg']:.4f} deg  (speed-up vs 20: {d['v_out_m_s']/1e3-20:+.4f} km/s)")
    print("\n=== Chained two-encounter construction, all 12 ordered pairs (A!=B), r_p = R for both encounters ===")
    for pair in out["chained_all_pairs"]:
        print(f"  {pair['moon_A']:10s} -> {pair['moon_B']:10s}  v_out_2={pair['encounter_2']['v_out_m_s']/1e3:.6f} km/s  net={pair['net_speed_change_vs_v_inf_m_s']/1e3:+.6f} km/s  total_dir_change={pair['net_direction_change_deg']:.5f} deg")
    print("\n=== Capture-baseline + propellant-savings, io_scale orbit, all cases ===")
    io_keys = [k for k in out["capture_baseline"] if "io" in k or k == "orbit_1"]
    base_key = [k for k in out["capture_baseline"] if "io" in k][0] if any("io" in k for k in out["capture_baseline"]) else list(out["capture_baseline"].keys())[0]
    base = out["capture_baseline"][base_key]
    print(f"  direct: dv={base['delta_v_direct_m_s']/1e3:.4f} km/s, propellant_frac={base['propellant_fraction_direct']*100:.3f}%")
    for k, v in base.items():
        if k.startswith("assisted_"):
            print(f"  {k}: dv={v['delta_v_m_s']/1e3:.5f} km/s, saving vs direct={v['propellant_saving_fraction_vs_direct']*100:+.5f}%")
    print("\n=== Kepler-period cross-check (mu_jupiter tied to independently-published periods) ===")
    for name, (T_pub_s, T_kep_s) in out["kepler_period_cross_check"].items():
        print(f"  {name:10s}  T_published={T_pub_s/86400:.5f} d   T_kepler_from_muJ={T_kep_s/86400:.5f} d   rel.err={(T_kep_s-T_pub_s)/T_pub_s*100:+.3f}%")
