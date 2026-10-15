"""
descent_model.py — Node 2b model runner for Problem A (Space Diving).

Source-agnostic per architecture: this module receives a plain
{z_m: [...], rho_kg_m3: [...], T_K: [...]} structured array (loaded from
the JSON file produced upstream by the Data-Source Routing step, here
`atmosphere_data_0_150km.json` — the ODE has no idea which named source
produced it, per ode_model.py's design constraint).

Implements:
  * Piecewise-regime drag coefficient / area switching (subsonic /
    transonic / supersonic) based on local Mach number.
  * 1D vertical descent ODE for u = v^2/2 vs. fallen distance x,
    du/dx = g_eff(z) - (rho(z)*CD*A/(2m))*u, solved with
    scipy.integrate.solve_ivp (no hand-rolled Taylor method).
  * A single-descent solver given a release altitude z0.
  * A sweep over z0 that reports, per release altitude, the peak
    |acceleration| and peak velocity of the whole descent, so the
    "max safe altitude" (headline constraint: peak |a| <= 5 g) can be
    read off as the largest z0 where this holds.
  * A `run_model(params)` callable compatible with boundary_gate.py's
    protocol (takes a dict, returns a dict with a named primary result
    key) — used by the boundary-gate spec, not by the main sweep.
"""
import json
import os

import numpy as np
from scipy.integrate import solve_ivp

# --- physical constants
G_EARTH_M_S2 = 9.80665
GM_EARTH = 3.986004418e14      # m^3/s^2
R_EARTH_M = 6.371e6            # m
GAMMA = 1.4
R_SPECIFIC = 287.05           # J/(kg K)

# Default hypothesis values (from hypothesis_layer in problem_state.json,
# mirrored here so the module is importable standalone; the authoritative
# copy is problem_state.json's hypothesis_layer, and run_model() accepts
# overrides via params).
DEFAULTS = {
    "m_kg": 190.0,
    "CD_subsonic": 1.0,
    "CD_transonic": 5.0,
    "CD_final_subsonic": 1.2,
    "A_subsonic_m2": 0.18,
    "A_supersonic_m2": 0.2,
    "mach_subsonic_max": 0.8,
    "mach_supersonic_min": 1.25,
    "G_PEAK_LIMIT_SUSTAINED": 5.0,   # headline safety bound, in g
}

DATA_FILE = os.path.join(os.path.dirname(__file__), "atmosphere_data_0_150km.json")


def load_atmosphere(data_path: str = DATA_FILE):
    with open(data_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return (np.asarray(d["z_m"], dtype=float),
            np.asarray(d["rho_kg_m3"], dtype=float),
            np.asarray(d["T_K"], dtype=float))


def _speed_of_sound(z_m, z_grid_m, T_grid):
    T = float(np.interp(z_m, z_grid_m, T_grid))
    return np.sqrt(GAMMA * R_SPECIFIC * T)


def g_eff(z_m):
    return GM_EARTH / (R_EARTH_M + z_m) ** 2


def solve_single(z0_m, z_grid_m, rho_grid, T_grid,
                 m_kg=190.0,
                 CD_subsonic=1.0, CD_transonic=5.0, CD_final_subsonic=1.2,
                 A_subsonic_m2=0.18, A_supersonic_m2=0.2,
                 mach_subsonic_max=0.8, mach_supersonic_min=1.25):
    """Integrate one full descent from rest at z0_m down to ~1 m above the
    surface. See _solve_single_real below for the full docstring; this is a
    thin public wrapper so external callers don't have to reference the
    private name."""
    return _solve_single_real(
        z0_m, z_grid_m, rho_grid, T_grid, m_kg,
        CD_subsonic, CD_transonic, CD_final_subsonic,
        A_subsonic_m2, A_supersonic_m2,
        mach_subsonic_max, mach_supersonic_min)


def _solve_single_real(z0_m, z_grid_m, rho_grid, T_grid, m_kg,
                       CD_subsonic, CD_transonic, CD_final_subsonic,
                       A_subsonic_m2, A_supersonic_m2,
                       mach_subsonic_max, mach_supersonic_min):
    if z0_m <= 1.0:
        # Degenerate: essentially no fall. Return zeros, not an error.
        return {"x": np.array([0.0]), "v": np.array([0.0]), "a": np.array([0.0]),
                "mach": np.array([0.0]), "regime": ["subsonic"],
                "max_v": 0.0, "max_abs_a": 0.0, "max_abs_a_in_g": 0.0,
                "z0_m": z0_m}

    rho_lookup = lambda alt: np.interp(alt, z_grid_m, rho_grid)
    T_lookup = lambda alt: float(np.interp(alt, z_grid_m, T_grid))
    a_sound = lambda alt: float(np.sqrt(GAMMA * R_SPECIFIC * T_lookup(alt)))

    regime = {"cur": "subsonic"}
    call_log = []  # (x, regime, CD, A) at every rhs evaluation, so the
    # post-hoc a[] uses exactly the regime the integrator actually used,
    # not a separately re-simulated regime sequence that can miss fast
    # transitions between t_eval sample points.

    def cd_a_of(v, alt):
        """Single authoritative regime state machine, shared by the ODE rhs and
        the post-hoc recompute pass (re-seeded once between them via
        regime['cur'] = 'subsonic').
        One-way transitions: subsonic -> transonic -> supersonic ->
        final_subsonic (parachute deployed; terminal state, no further
        regime changes). The only downward transition that ever fires is
        out of transonic/supersonic, into final_subsonic, the moment M
        drops back below mach_subsonic_max.
        Note: transonic and supersonic regimes use the body's streamlined
        cross section (A_subsonic_m2 ~ 0.18 m^2) — NOT the parachute's
        canopy area, which is only active once 'final_subsonic' (parachute
        deployed) is reached. This matches the physical picture of a
        skydiver who keeps a compact, streamlined body posture through the
        fast (near-supersonic) part of the fall, and only deploys the
        parachute canopy once slowed back down to subsonic speeds."""
        M = float(np.asarray(v).item()) / a_sound(alt)
        if regime["cur"] == "final_subsonic":
            return CD_final_subsonic, A_supersonic_m2
        if M >= mach_supersonic_min:
            if regime["cur"] not in ("transonic",):
                regime["cur"] = "supersonic"
        elif M >= mach_subsonic_max:
            if regime["cur"] not in ("supersonic", "final_subsonic"):
                regime["cur"] = "transonic"
        else:
            if regime["cur"] in ("transonic", "supersonic"):
                regime["cur"] = "final_subsonic"
        if regime["cur"] == "subsonic":
            return CD_subsonic, A_subsonic_m2
        if regime["cur"] == "transonic":
            return CD_transonic, A_subsonic_m2
        if regime["cur"] == "supersonic":
            return CD_transonic, A_subsonic_m2
        return CD_final_subsonic, A_supersonic_m2

    def rhs(x, u):
        alt = max(0.0, z0_m - x)
        u0 = float(np.asarray(u).item())
        v = float(np.sqrt(2.0 * max(u0, 0.0)))
        CD, A = cd_a_of(v, alt)
        call_log.append((x, regime["cur"], CD, A))
        g = g_eff(alt)
        du_dx = g - (float(rho_lookup(alt)) * CD * A / (2.0 * m_kg)) * u0
        return [du_dx]

    t_eval = np.linspace(0.0, z0_m - 1.0, 2000)
    sol = solve_ivp(rhs, [0.0, z0_m - 1.0], [0.0], t_eval=t_eval,
                    method="RK45", rtol=1e-8, atol=1e-10)
    if not sol.success:
        raise RuntimeError(f"solve_ivp failed: {sol.message}")

    u = sol.y[0]
    v = np.sqrt(2.0 * np.clip(u, 0, None))
    x = sol.t
    alt = np.maximum(0.0, z0_m - x)
    g_arr = g_eff(alt)

    # For each t_eval sample, use the LAST logged rhs call at x <= sample_x,
    # so the regime/CD/A attached to each sample is exactly what the
    # integrator was using right up to that point.
    log_x = np.array([c[0] for c in call_log])
    idx = np.searchsorted(log_x, x, side="right") - 1
    idx = np.clip(idx, 0, len(call_log) - 1)
    regime_names = [call_log[i][1] for i in idx]
    CD_arr = np.array([call_log[i][2] for i in idx])
    A_arr = np.array([call_log[i][3] for i in idx])
    a_arr = g_arr - (np.asarray(rho_lookup(alt), dtype=float) * CD_arr * A_arr / (2.0 * m_kg)) * (v ** 2)
    mach_arr = v / np.array([a_sound(alt_i) for alt_i in alt])

    return {
        "x": x, "v": v, "a": a_arr, "mach": mach_arr,
        "regime": regime_names,
        "max_v": float(np.max(v)),
        "max_abs_a": float(np.max(np.abs(a_arr))),
        "max_abs_a_in_g": float(np.max(np.abs(a_arr)) / G_EARTH_M_S2),
        "z0_m": z0_m,
    }


def run_model(params: dict) -> dict:
    """boundary_gate.py-compatible entry point. `params` overrides any
    subset of DEFAULTS plus a 'z0_m' release altitude. Returns peak
    statistics for one descent; 'max_abs_a_in_g' is the primary result
    used by the boundary gate's expectation checks."""
    p = {**DEFAULTS, **params}
    z_grid_m, rho_grid, T_grid = load_atmosphere()
    res = _solve_single_real(
        z0_m=p["z0_m"], z_grid_m=z_grid_m, rho_grid=rho_grid, T_grid=T_grid,
        m_kg=p["m_kg"],
        CD_subsonic=p["CD_subsonic"], CD_transonic=p["CD_transonic"],
        CD_final_subsonic=p["CD_final_subsonic"],
        A_subsonic_m2=p["A_subsonic_m2"], A_supersonic_m2=p["A_supersonic_m2"],
        mach_subsonic_max=p["mach_subsonic_max"],
        mach_supersonic_min=p["mach_supersonic_min"])
    out = {k: res[k] for k in ("max_v", "max_abs_a", "max_abs_a_in_g")}
    out["regime_seen_final_subsonic"] = "final_subsonic" in res["regime"]
    return out


def sweep_over_release_altitude(z0_list_m, z_grid_m, rho_grid, T_grid,
                                **overrides):
    """Run solve_single for each release altitude; return a list of the
    per-altitude result dicts, keyed by z0_m."""
    base = {**DEFAULTS, **overrides}
    results = []
    for z0 in z0_list_m:
        res = _solve_single_real(
            z0_m=z0, z_grid_m=z_grid_m, rho_grid=rho_grid, T_grid=T_grid,
            m_kg=base["m_kg"],
            CD_subsonic=base["CD_subsonic"], CD_transonic=base["CD_transonic"],
            CD_final_subsonic=base["CD_final_subsonic"],
            A_subsonic_m2=base["A_subsonic_m2"], A_supersonic_m2=base["A_supersonic_m2"],
            mach_subsonic_max=base["mach_subsonic_max"],
            mach_supersonic_min=base["mach_supersonic_min"])
        res["z0_m"] = z0
        results.append(res)
    return results


def max_safe_altitude(z0_list_m, z_grid_m, rho_grid, T_grid,
                      g_limit=5.0, **overrides):
    """Largest z0 (km) in the sweep whose peak |a| stays at or below
    g_limit * G_EARTH_M_S2. Returns (z0_km, full_sweep_results)."""
    sweep = sweep_over_release_altitude(z0_list_m, z_grid_m, rho_grid, T_grid, **overrides)
    ok = [r for r in sweep if r["max_abs_a"] <= g_limit * G_EARTH_M_S2 + 1e-9]
    if not ok:
        return None, sweep
    z0_km = max(r["z0_m"] for r in ok) / 1000.0
    return z0_km, sweep


if __name__ == "__main__":
    z_grid_m, rho_grid, T_grid = load_atmosphere()
    z0_list = np.arange(0, 151000 + 1, 1000.0)
    z0_km, sweep = max_safe_altitude(z0_list, z_grid_m, rho_grid, T_grid, g_limit=5.0)
    print(f"max safe altitude (5 g bound): {z0_km} km")
    for r in sweep:
        if r["z0_m"] % 5000 == 0:
            regimes_seen = sorted(set(r["regime"]))
            print(f"z0={r['z0_m']/1000:4.0f} km: v_max={r['max_v']:8.1f} m/s "
                  f"|a|max={r['max_abs_a_in_g']:6.3f} g  regimes_seen={regimes_seen}")
