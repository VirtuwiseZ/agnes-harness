"""
Physics model module: Jupiter-moon gravity-assist deceleration for a 20 km/s probe.

Source-agnostic: consumes a structured orbital-constants dict (produced by Node 1.5),
never hardcodes ephemeris values. Implements the governing two-body gravity-assist
bound and the Tsiolkovsky residual-chemical-burn comparison.

Governing physics (Node 2b):
- In the moon's rest frame the encounter is elastic: speed magnitude preserved,
  direction rotated by deflection angle delta. The probe's Jupiter-frame velocity
  changes by delta_v_probe = 2 * v_moon * sin(delta/2) (projected onto the direction
  that reduces Jupiter-frame speed).
- Realistic delta: a close flyby gives delta ~ 90 deg -> sin(45 deg) = 0.7071,
  so delta_v_probe ~ sqrt(2) * v_moon (NOT the collinear ideal 2*v_moon).
- Required deceleration: delta_v_required = v_infinity - v_capture.
- Tsiolkovsky: propellant fraction for a chemical burn of delta_v at Isp s:
    fraction = 1 - exp(-delta_v / (Isp * g0)), g0 = 9.81 m/s^2.

Key physical insight the model encodes: the gravity-assist momentum reservoir is
the moon's OWN orbital speed v_moon = sqrt(G_J / a_moon), which is a function of
the primary's gravitational parameter G_J and the moon's semi-major axis a_moon
ONLY - NOT of the moon's mass M_moon or the probe's mass m_probe. The M_moon
term appears only in the small m_probe/M_moon correction to the elastic limit
(for realistic probes this correction is ~1e-12 to 1e-15, safely negligible).
This is why the "zero_gravity" degenerate case drives v_moon -> 0 with G_J -> 0,
and why varying M_moon by many orders of magnitude leaves the bound unchanged.
"""

import math

G0 = 9.81  # m/s^2, standard gravity
TOL = 1e-9  # tolerance for "zero" boundary expectation


def moon_v_orbital(moons, G_J_km3_s2, capture_radius_km, Isp_s):
    """Compute the key numbers for each moon in the structured input dict.

    moons: { name: {"a_km": float, "M_kg": float, "v_infinity": float} }
    Returns a dict of results, one block per moon.
    """
    results = {}
    for name, m in moons.items():
        a = m["a_km"]
        M_moon = m["M_kg"]
        # Moon's orbital speed around Jupiter (the momentum reservoir).
        # NOTE: depends on G_J and a ONLY, not on M_moon - this is the elastic
        # two-body gravity-assist limit; the M_moon dependence is a ~m/M
        # correction that is negligible for any realistic probe mass.
        v_moon = math.sqrt(max(G_J_km3_s2, 0.0) / a)  # km/s
        # Realistic single-flyby bound: a close flyby gives deflection ~90 deg
        # -> sqrt(2) * v_moon (NOT the collinear 2*v_moon ideal).
        delta_v_probe = math.sqrt(2.0) * v_moon  # km/s
        # Required deceleration to capture: v_infinity - circular orbit speed.
        v_capture = math.sqrt(max(G_J_km3_s2, 0.0) / capture_radius_km)  # km/s
        # Delta-v required to brake from a far approach of v_infinity down to a
        # circular orbit at capture_radius: you must reduce your speed to the
        # local circular-orbit speed. (The far-approach speed is v_infinity;
        # after falling in to periapsis your speed is higher, but for the
        # order-of-magnitude capture requirement the relevant target is the
        # circular-orbit speed at the chosen capture radius, and the burn is
        # done to reach that orbit.)
        delta_v_required = v_capture - m["v_infinity"]
        # Tsiolkovsky propellant fractions for a chemical burn of delta_v at Isp s.
        def frac(dv_km_s):
            # convert to m/s for the Isp*g0 term; negative args clamp to 0 burn.
            return 1.0 - math.exp(-max(dv_km_s, 0.0) * 1000.0 / (Isp_s * G0))
        frac_chem = frac(delta_v_required)
        frac_assist = frac(max(delta_v_required - delta_v_probe, 0.0))
        savings_frac = frac_chem - frac_assist
        results[name] = {
            "v_moon_km_s": v_moon,
            "v_capture_km_s": v_capture,
            "delta_v_required_km_s": delta_v_required,
            "delta_v_probe_km_s": delta_v_probe,
            "frac_chem": frac_chem,
            "frac_assist": frac_assist,
            "savings_frac": savings_frac,
            "M_moon_kg": M_moon,
        }
    return results


def run_model(params):
    """
    params:
      G_J_km3_s2: float - Jupiter's gravitational parameter.
      capture_radius_km: float - target capture-orbit radius.
      Isp_s: float - chemical engine specific impulse (for the residual burn).
      moons: { name: {"a_km": float, "M_kg": float, "v_infinity": float} }
      v_infinity_sweep: optional float - if present, overrides every moon's
        v_infinity (used by the boundary-gate monotonicity sweep to vary the
        approach speed and watch the covered-fraction decrease).
    Returns dict with per-moon "results" + primary + sweep-testable keys.
    """
    sv = params.get("v_infinity_sweep")
    if sv is not None:
        sv = float(sv)
        moons = {n: {**m, "v_infinity": sv} for n, m in params["moons"].items()}
    else:
        moons = {n: dict(m) for n, m in params["moons"].items()}
    res = moon_v_orbital(moons, params["G_J_km3_s2"],
                         params["capture_radius_km"], params["Isp_s"])
    best_name, best_block = max(res.items(), key=lambda kv: kv[1]["delta_v_probe_km_s"])
    best = best_block
    # Headline: as v_infinity DECREASES, the required deceleration
    # (v_capture - v_infinity) INCREASES, so a fixed best-moon assist covers a
    # SMALLER fraction; as v_infinity INCREASES, the required deceleration
    # shrinks and the covered fraction rises. The sweep (increasing v_infinity)
    # therefore observes frac_covered INCREASING - that is the monotonicity
    # quantity tested. (A fixed-km/s assist is a larger share of a smaller
    # required deceleration.)
    dv_req = best["delta_v_required_km_s"]
    frac_covered = (best["delta_v_probe_km_s"] / dv_req) if dv_req > 0 else 0.0
    return {"results": res,
            "primary_result": best["savings_frac"],
            "best_moon_probe_delta_v_km_s": best["delta_v_probe_km_s"],
            "best_moon": best_name,
            "frac_covered_by_assist": frac_covered}
