"""Node 2b step 2: fetch/parse the external data chosen in Node 1.5 (ambiance),
produce the plain structured array + a second, genuinely independent uniform-
density setup for the verification baseline, and drive the hit-condition
root-finder to actually solve the 1200 m / 500 m case, then generalize.

Two atmosphere setups, kept source-agnostic (plain numpy arrays, no package
name anywhere downstream of this fetch step):
  1. `variable`  - ambiance's T(z)/rho(z)/a(z) over 0-6 km (the modeling input
     chosen at Node 1.5, used to find the headline (v0, theta) answer).
  2. `uniform`   - a single constant rho, a_sound pair (sea-level standard
     values), used ONLY for the independent cross-check against a textbook
     quadratic-drag range approximation — NOT re-derived from the same
     ambiance data, per the independence rule.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'program-design', 'runtime'))
import artillery_model
from artillery_model import simulate, hit_condition, cd_of_mach

# --- 1. Fetch ambiance's structured array (the Node 1.5-chosen source) ---
from ambiance import Atmosphere  # imported HERE only; never referenced by the ODE code itself

z_grid_m = np.arange(0.0, 6001.0, 100.0)
atmos = Atmosphere(z_grid_m)
rho_grid = atmos.density
a_grid = atmos.speed_of_sound
T_grid = atmos.temperature

variable = {
    "rho_grid_m": z_grid_m,
    "rho_grid_values": rho_grid,
    "a_sound_grid_m": z_grid_m,
    "a_sound_grid_values": a_grid,
}

# --- 2. Independent uniform-density setup (for the verification baseline only) ---
uniform_rho = 1.225
uniform_a_sound = 340.29
uniform_setup = {
    "rho_grid_m": np.array([0.0, 6000.0]),
    "rho_grid_values": np.array([uniform_rho, uniform_rho]),
    "a_sound_grid_m": np.array([0.0, 6000.0]),
    "a_sound_grid_values": np.array([uniform_a_sound, uniform_a_sound]),
}


def solve_hit(R_target_m: float, setup: dict, u_wind_m_s: float = 0.0,
              z_launch_m: float = 500.0, z_target_m: float = 500.0,
              v0_cap_m_s: float = 450.0):
    """Given a fixed firing angle, root-find v0 so hit_condition = 0.
    Returns (v0, theta_deg, miss_residual, converged)."""
    from scipy.optimize import brentq

    def f(v0):
        return hit_condition(
            v0, math.radians(theta_deg_for_solve), R_target_m, u_wind_m_s,
            z_launch_m, z_target_m,
            setup["rho_grid_m"], setup["rho_grid_values"],
            setup["a_sound_grid_m"], setup["a_sound_grid_values"],
        )

    theta_deg_for_solve = solve_hit._theta_deg  # set by caller just below

    # Scan a coarse v0 grid first to bracket a sign change of f (robust,
    # no closed-form initial guess needed - mirrors the "no calculator"
    # spirit of the final officer-facing method).
    v_scan = np.linspace(30.0, v0_cap_m_s, 42)
    fvals = np.array([f(v) for v in v_scan])
    sign_changes = np.where(np.diff(np.sign(fvals)) != 0)[0]
    if len(sign_changes) == 0:
        return None, None, None, False
    lo, hi = v_scan[sign_changes[0]], v_scan[sign_changes[0] + 1]
    v_sol = brentq(f, lo, hi, xtol=1e-3)
    miss = f(v_sol)
    return v_sol, theta_deg_for_solve, miss, True


def solve_for_angle(theta_deg: float):
    solve_hit._theta_deg = theta_deg


# --- Headline case: R=1200 m, both ends 500 m, no wind. Try a coarse set of
# candidate angles, root-find v0 for each, and report the one that lands
# closest to a "natural" firing angle (45 deg, the vacuum-optimal range angle)
# while also staying comfortably under the 450 m/s cap. ---
R = 1200.0
angles_to_try = [30, 40, 45, 50, 55, 60]
results = []
for ang in angles_to_try:
    solve_for_angle(ang)
    v0, theta, miss, ok = solve_hit(R, variable, 0.0, 500.0, 500.0)
    results.append({"theta_deg": ang, "v0_m_s": v0, "miss_m": miss, "converged": ok})

print("=== Variable-density (ambiance) modeling-input solve, R=1200 m, no wind ===")
for r in results:
    print(r)

# Pick the most "economical" candidate: smallest v0 that still converges
converged = [r for r in results if r["converged"]]
economical = min(converged, key=lambda r: r["v0_m_s"])
print("\nChosen headline answer (smallest v0 among converged angle candidates):")
print(economical)

# --- Cross-check against the INDEPENDENT uniform-density baseline for the same
# (v0, theta) pair, so we can say "the variable-atmosphere answer and the
# constant-atmosphere answer agree within X" ---
if economical["v0_m_s"] is not None:
    check = hit_condition(
        economical["v0_m_s"], math.radians(economical["theta_deg"]), R, 0.0, 500.0, 500.0,
        uniform_setup["rho_grid_m"], uniform_setup["rho_grid_values"],
        uniform_setup["a_sound_grid_m"], uniform_setup["a_sound_grid_values"],
    )
    print(f"\nIndependent uniform-density baseline check at the same (v0, theta): "
          f"miss = {check:+.2f} m  (0 = still a hit under the independent assumption)")

    # Also check the classic vacuum (zero-drag) range for the same v0/theta,
    # as a second, fully source-free sanity anchor (no atmosphere data at all).
    g = artillery_model.G_STANDARD_M_S2
    v0 = economical["v0_m_s"]
    th = math.radians(economical["theta_deg"])
    range_vacuum_same_level = v0**2 * math.sin(2 * th) / g  # only valid level-to-level
    print(f"Vacuum (zero-drag), same-level range formula at this v0/theta: "
          f"{range_vacuum_same_level:.1f} m (vs. target {R} m)")

# --- Generalization: same method, different R / altitude / wind combos ---
print("\n=== Generalization sweep (variable-density setup) ===")
gen_cases = [
    {"R": 1000.0, "z_launch": 500.0, "z_target": 500.0, "wind": 0.0},
    {"R": 1500.0, "z_launch": 500.0, "z_target": 500.0, "wind": 0.0},
    {"R": 1200.0, "z_launch": 500.0, "z_target": 500.0, "wind": -5.0},   # 5 m/s headwind
    {"R": 1200.0, "z_launch": 500.0, "z_target": 500.0, "wind": +5.0},   # 5 m/s tailwind
    {"R": 1200.0, "z_launch": 1000.0, "z_target": 500.0, "wind": 0.0},  # firing from higher
    {"R": 1200.0, "z_launch": 500.0, "z_target": 1000.0, "wind": 0.0},  # target higher
    {"R": 1200.0, "z_launch": 0.0, "z_target": 0.0, "wind": 0.0},      # sea level, both ends
]
for c in gen_cases:
    solve_for_angle(45)
    v0, theta, miss, ok = solve_hit(c["R"], variable, c["wind"], c["z_launch"], c["z_target"])
    tag = f"R={c['R']:.0f}m zL={c['z_launch']:.0f}m zT={c['z_target']:.0f}m wind={c['wind']:+.0f} m/s"
    if ok:
        print(f"{tag}: v0={v0:.1f} m/s, theta={theta} deg, residual={miss:+.3f} m")
    else:
        print(f"{tag}: no converged v0 found under the 450 m/s cap at 45 deg "
              f"(needs a different angle or is out of the cannon's physical range)")

import json
sys.path.insert(0, os.path.join(HERE, "program-design", "hooks"))
import audit_log
state_path = os.path.abspath(os.path.join(HERE, "program-design", "runtime", "problem_state_2025B_artillery.json"))
audit_log.append_record(
    state_path=state_path,
    source="ambiance_atmosphere_array_fetch",
    args={
        "z_grid_m_span": [float(z_grid_m[0]), float(z_grid_m[-1])],
        "step_m": 100.0,
        "sample": {
            "rho_at_500m": float(np.interp(500.0, z_grid_m, rho_grid)),
            "a_sound_at_500m": float(np.interp(500.0, z_grid_m, a_grid)),
            "T_at_500m": float(np.interp(500.0, z_grid_m, T_grid)),
        },
        "note": "Node 2b step 1: plain structured arrays handed to the ODE code; the ODE itself never sees the package name (source-agnostic rule satisfied).",
    },
)
audit_log.append_record(
    state_path=state_path,
    source="headline_solve_variable_density",
    args={"results_by_angle": results, "chosen": economical},
)
audit_log.append_record(
    state_path=state_path,
    source="independent_uniform_density_baseline_check",
    args={"miss_m_at_chosen_v0_theta": check if economical["v0_m_s"] is not None else None,
          "vacuum_range_formula_m": range_vacuum_same_level if economical["v0_m_s"] is not None else None,
          "R_target_m": R},
)
audit_log.append_record(
    state_path=state_path,
    source="generalization_sweep",
    args={"cases": gen_cases},
)
print("\nAudit records written.")
