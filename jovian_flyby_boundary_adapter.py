"""
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

    # Handle the mu_m -> 0 (no-gravity, no-op) limit explicitly instead of
    # letting M.v_out_closed_form raise ZeroDivisionError inside its own
    # hyperbolic_turning_angle call: the analytically-correct limit is
    # e -> infinity, delta -> 0, and
    #   head_on:      v_out -> |v_rel - v_moon|
    #   overtaking:   v_out -> v_moon + v_rel   (both velocities simply add,
    #                  no deflection at all - the "no encounter happened"
    #                  no-op limit, which is a genuinely different no-op
    #                  answer than the head-on case's, and both are the
    #                  correct, well-defined values to return at exactly
    #                  mu_m = 0, not a NaN or an exception.)
    if mu_m == 0.0:
        if head_on:
            v_out, delta = abs(v_rel - v_moon), 0.0
        else:
            v_out, delta = v_moon + v_rel, 0.0
        return {"v_out_m_s": v_out, "delta": delta}

    v_out, delta = M.v_out_closed_form(r_p, v_rel, v_moon, mu_m, head_on=head_on)
    return {"v_out_m_s": v_out, "delta": delta}
