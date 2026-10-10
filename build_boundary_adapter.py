# Append a thin, boundary-gate-compatible `run_model(params: dict) -> dict`
# wrapper to the END of jovian_flyby_model_run2.py (does not modify the
# existing `if __name__ == "__main__"` demo block - that stays exactly as is,
# the new wrapper is purely additive, appended after it).
p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

# Remove the old `if __name__` guard's shadowing problem: the existing module-level
# `def run_model(params=None)` already exists and is the "full sweep" entry point.
# The boundary gate needs a DIFFERENT signature: run_model(params: dict) -> dict,
# where `params` is a flat dict of single scalar values (v_rel, r_p, mu_m, etc.)
# and the return is a dict with a single float under a fixed key, so the gate's
# `out[primary_result]` extraction works. We add a SECOND, distinct function,
# `run_model_boundary(params)` , and point the gate's `model_module` at a tiny
# adapter module (not this file, to avoid a naming collision with the existing
# top-level run_model already defined here).
print("NOTE: jovian_flyby_model_run2.py already defines a top-level run_model(params=None) "
      "with a DIFFERENT contract (returns a big dict of sweeps, not a single scalar). "
      "The boundary gate requires run_model(params: dict) -> dict-with-a-single-key. "
      "So we build a thin ADAPTER module instead, leaving this file's existing "
      "run_model() completely untouched.")

adapter = r'''"""
Thin adapter module exposing a boundary-gate-compatible run_model(params: dict) -> dict
wrapper around jovian_flyby_model_run2's internal closed-form functions, WITHOUT
touching the existing top-level run_model() in that file (which has a different
contract: it takes no required params and returns a large sweep dict, not a
single scalar suitable for the gate's `out[primary_result]` extraction).
"""
import sys
sys.path.insert(0, r"E:\agh-test")
import jovian_flyby_model_run2 as M


def run_model(params):
    """
    params: dict with keys (all optional, with sensible defaults matching the
    boundary spec's base case):
      v_rel (float, m/s)      - relative closing/approach speed
      r_p (float, m)          - perigee distance
      mu_m (float, m^3/s^2)   - moon's gravitational parameter
      v_moon (float, m/s)     - moon's circular-orbital speed
      head_on (bool, True)    - True for the closing/head-on formula, False for
                                 the run-#2 overtaking branch
      v_inf (float, m/s)      - only used when computing the 'net change vs
                                 v_inf' convenience quantity
    returns: dict with keys:
      v_out_m_s (float)       - the boundary-gate "primary_result"
      delta (float, radians)
    """
    v_rel = params.get("v_rel", 37332.0)
    r_p = params.get("r_p", 1821600.0)
    mu_m = params.get("mu_m", 5.959e15)
    v_moon = params.get("v_moon", 17332.0)
    head_on = params.get("head_on", True)
    v_out, delta = M.v_out_closed_form(r_p, v_rel, v_moon, mu_m, head_on=head_on)
    return {"v_out_m_s": v_out, "delta": delta}
'''

open(r"E:\agh-test\jovian_flyby_boundary_adapter.py", "w", encoding="utf-8").write(adapter)
print("wrote adapter module: jovian_flyby_boundary_adapter.py")

import json
spec = {
    "model_module": "jovian_flyby_boundary_adapter",
    "primary_result": "v_out_m_s",
    "cases": [
        {
            "name": "headon_mu_m_to_0",
            "params": {"head_on": True, "v_rel": 37332.0, "r_p": 1821600.0, "mu_m": 0.0, "v_moon": 17332.0},
            "expectation": "finite",
            "note": "no-op limit: mu_m -> 0 must give delta -> 0 and v_out -> v_rel - v_moon = 20000 m/s (=v_inf), the exact 'no encounter happened' answer; 'finite' is a necessary (not sufficient) check, the monotonic sweep below is the stronger one."
        },
        {
            "name": "headon_v_rel_to_0",
            "params": {"head_on": True, "v_rel": 0.0, "r_p": 1821600.0, "mu_m": 5.959e15, "v_moon": 17332.0},
            "expectation": "finite",
            "note": "maximum-deflection limit: v_rel -> 0 gives delta -> 180 deg, v_out -> v_moon exactly."
        },
        {
            "name": "overtaking_v_rel_to_0",
            "params": {"head_on": False, "v_rel": 0.0, "r_p": 2410400.0, "mu_m": 7.181e15, "v_moon": 8203.9},
            "expectation": "finite",
            "note": "run #2's overtaking branch, v_rel -> 0: v_out -> v_moon (the spacecraft ends up at the moon's own speed, a no-op-limit sanity check specific to the NEW formula)."
        }
    ],
    "sweep": {
        "param": "mu_m",
        "order": "decrease",
        "values": [5.959e15, 1.0e15, 1.0e10, 1.0e5, 1.0, 0.0],
        "base_params": {"head_on": True, "v_rel": 37332.0, "r_p": 1821600.0, "v_moon": 17332.0},
        "note": "v_out must monotonically DECREASE from ~37.3 km/s (mu_m -> infinity, no encounter) down to exactly 20.0 km/s (=v_inf, the no-op limit) as mu_m -> 0; this is the single most important degeneracy check for the head-on formula, since it directly tests the v_out >= v_inf invariant's no-op endpoint."
    }
}
json.dump(spec, open(r"E:\agh-test\program-design\knowledge\jupiter_flyby\boundary_spec_run2.json", "w", encoding="utf-8"), indent=2)
print("wrote boundary spec (overwriting the earlier, non-gate-compatible draft)")
