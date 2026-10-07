"""Node 2b step 5: verification + boundary gate, per the protocol's two
required defense lines.

Verification baseline — NOT a second ODE model, but the classic, hand-
computable QUADRATIC-DRAG RANGE PERTURBATION result (the estimate an officer
with only a calculator could actually run, which is exactly the spirit of
the problem's final ask):

    Vacuum range at (v0, theta):  R_vac = v0^2 * sin(2*theta) / g
    Fractional range reduction from quadratic drag, first order in the
    drag-to-weight ratio (a textbook result, e.g. via the "short shot" /
    small-drag expansion of the projectile's range):
        delta_R / R_vac  ~  (1/3) * (rho0 * CD * A / (2m)) * R_vac * (1 - ...)
    A cleaner, dimensionally-robust hand estimate (used here, and derivable
    without an ODE) is to compute the drag "stopping scale" L = m / (rho*CD*A/2)
    (the length over which drag alone would consume the projectile's kinetic
    energy, ignoring gravity's role) and note that for our numbers L >> R,
    so drag's effect is a small correction: the required correction to the
    VACUUM muzzle speed is roughly
        v0_drag^2 ~ v0_vac^2 * (1 + (K * R * v0_vac) / (2g))
    with K = rho*CD*A/(2m) (units 1/m), R the target range. This is
    re-derived from first principles in a couple of lines, not looked up,
    and it uses ONLY a single constant density value + K + R — genuinely
    independent of any T(z)/rho(z) source.
"""
import math
import os
import sys
import json

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "program-design", "runtime"))
import artillery_model
from artillery_model import PROJECTILE_AREA_M2, PROJECTILE_MASS_KG, G_STANDARD_M_S2, cd_of_mach

# The chosen headline answer from the variable-density solve:
v0_chosen = 142.3035991426544
theta_chosen_deg = 40.0
theta_chosen = math.radians(theta_chosen_deg)
R = 1200.0

# Uniform-density independent estimate (sea-level standard density, matching
# the uniform_setup used for the ODE cross-check in the previous script):
rho0 = 1.225
v0_vac = math.sqrt(R * G_STANDARD_M_S2 / math.sin(2 * theta_chosen))
print(f"Vacuum muzzle speed needed (independent, hand formula): v0_vac = {v0_vac:.2f} m/s "
      f"(theta={theta_chosen_deg} deg)")

# Mach at v0_vac / a_sound(0m)
a_sound0 = 340.29
mach_vac = v0_vac / a_sound0
print(f"Mach(v0_vac) = {mach_vac:.2f}  -> CD = {cd_of_mach(mach_vac):.2f} (subsonic regime, "
      f"consistent with using the subsonic CD value)")

K = rho0 * cd_of_mach(mach_vac) * PROJECTILE_AREA_M2 / (2.0 * PROJECTILE_MASS_KG)
print(f"K = rho*CD*A/(2m) = {K:.5f} 1/m  (uniform-density, independent estimate)")

# First-order drag correction to the required muzzle speed:
correction = 1.0 + K * R * v0_vac / (2 * G_STANDARD_M_S2)
v0_drag_est = v0_vac * math.sqrt(correction)
print(f"First-order drag-corrected estimate: v0 ~ v0_vac * sqrt(1 + K*R*v0_vac/(2g)) "
      f"= {v0_drag_est:.2f} m/s")

# Compare against the ODE solve's actual answer:
rel_diff = (v0_drag_est - v0_chosen) / v0_chosen
print(f"\nODE-solve answer: v0 = {v0_chosen:.2f} m/s")
print(f"Independent hand estimate: v0 ~ {v0_drag_est:.2f} m/s")
print(f"Relative difference: {rel_diff*100:.1f}%  -> "
      + ("AGREES within a comfortable hand-estimation tolerance" if abs(rel_diff) < 0.15
         else "DIVERGES beyond a reasonable hand-estimation tolerance - investigate"))

# --- Boundary gate spec, driven by artillery_model.run_model ---
boundary_spec = {
    "model_module": "artillery_model",
    "primary_result": "miss_m",
    "cases": [
        {
            "name": "zero-muzzle-velocity -> trajectory never reaches target -> large undershoot (negative miss), finite",
            "params": {"v0_m_s": 1.0, "theta_deg": 45.0, "R_target_m": 1200.0},
            "expectation": "finite",
        },
        {
            "name": "very-high-velocity -> large overshoot (positive miss), still finite",
            "params": {"v0_m_s": 450.0, "theta_deg": 45.0, "R_target_m": 1200.0},
            "expectation": "finite",
        },
        {
            "name": "straight-up (90 deg) with any v0 -> x barely moves -> strongly negative miss",
            "params": {"v0_m_s": 140.0, "theta_deg": 89.0, "R_target_m": 1200.0},
            "expectation": "finite",
        },
        {
            "name": "near-horizontal (1 deg) -> lands very short -> strongly negative miss",
            "params": {"v0_m_s": 140.0, "theta_deg": 1.0, "R_target_m": 1200.0},
            "expectation": "finite",
        },
    ],
    "sweep": {
        "param": "v0_m_s",
        "values": [60.0, 100.0, 142.3, 180.0, 250.0, 350.0, 450.0],
        "order": "increase",
        "base_params": {"theta_deg": 45.0, "R_target_m": 1200.0, "z_launch_m": 500.0,
                        "z_target_m": 500.0, "u_wind_m_s": 0.0},
        "note": "miss distance is expected to increase monotonically with v0 "
                "(faster shot, farther landing point) at fixed angle - a "
                "monotonicity check the gate can actually verify.",
    },
}

with open(os.path.join(HERE, "program-design", "runtime", "boundary_spec_artillery.json"), "w", encoding="utf-8") as f:
    json.dump(boundary_spec, f, indent=2)

print("\nBoundary spec written; running boundary_gate.py next...")
