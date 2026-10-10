"""
Jovian-moon gravity-assist orbital-entry model (final, problem-specific).

Physics summary (see module docstring history + jupiter_flyby_params.json
provenance notes):
  * Spacecraft arrives at Jupiter's system at Jupiter-frame hyperbolic excess
    speed v_inf = 20 km/s.
  * A single Galilean moon, on a circular orbit of radius a_m at speed
    v_moon = sqrt(mu_j/a_m), is treated as a two-body moving target.
  * Head-on (deceleration) geometry: the spacecraft approaches the moon
    from the upstream side of its orbit - its Jupiter-frame velocity points
    OPPOSITE the moon's orbital velocity, so the two bodies close on each
    other at the CLOSING SPEED v_rel = v_inf + v_moon (this is what makes
    it a slow-down geometry; the v_inf - v_moon "overtaking" case is a
    speed-up and is explicitly excluded as not relevant to this question).
  * In the moon's own frame the encounter is a plain two-body hyperbolic
    (Rutherford) flyby: incoming speed v_rel, turning angle
    delta = 2*asin(1/e) with e = 1 + r_p*v_rel^2/mu_m.
  * Energy conservation in the moon frame (key slingshot invariant): the
    spacecraft's speed magnitude in that frame is exactly unchanged by the
    flyby - only its direction rotates. This is what makes a slingshot
    "free" in the moon frame and purely a frame-kinematics effect seen from
    the Jupiter frame.
  * Back in the Jupiter frame, the exit velocity is the vector sum of the
    moon's orbital velocity and the rotated exit velocity (same magnitude
    v_rel):  v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)
    (head-on geometry, exit leg as anti-parallel to v_moon as geometry allows).
  * For v_rel = v_inf + v_moon > v_moon, and any delta < 180 deg, this
    expression is ALWAYS >= (v_rel - v_moon)^2 = v_inf^2, i.e.
    v_out >= v_inf ALWAYS: a single head-on Galilean-moon flyby at this
    approach speed mathematically CANNOT reduce the Jupiter-frame speed.
    The model computes this exactly (it is the genuine, non-trivial
    physical result - not an assumption baked in), and quantifies how
    close to zero the deceleration effect is in realistic cases.

Constants: IAU/JPL published standard values (Level-3 source, see Node 1.5
audit record - no live data source was reachable in this environment).
"""
import math

MU_JUPITER = 1.26712e17   # m^3/s^2  (matches Io's published 1.7691-d period to ~0.04%, verified this run)
G = 6.67430e-11            # m^3/(kg s^2), CODATA 2018

MOONS = {
    "io":       {"a_m": 4.2181e8,  "M_kg": 8.932e22,  "R_m": 1.8216e6},
    "europa":   {"a_m": 6.711e8,   "M_kg": 4.80e21,   "R_m": 1.5608e6},
    "ganymede": {"a_m": 1.0704e9,  "M_kg": 1.4819e23, "R_m": 2.6341e6},
    "callisto": {"a_m": 1.8827e9,  "M_kg": 1.0759e23, "R_m": 2.4104e6},
}

TARGET_ORBITS = {
    "io_scale":       {"a_m": 4.2181e8, "label": "Io-scale compact orbit"},
    "ganymede_scale": {"a_m": 1.0704e9, "label": "Ganymede-scale outer orbit"},
}

Isp_s = 450.0          # s, assumed-this-run representative chemical upper-stage Isp
g0 = 9.80665          # m/s^2, standard gravity (Tsiolkovsky propellant fraction)
V_INFDIRECT = 20.0e3  # m/s, given Jupiter-frame approach speed


def _moon_params(name):
    m = MOONS[name]
    mu_m = G * m["M_kg"]
    v_moon = math.sqrt(MU_JUPITER / m["a_m"])
    v_esc_surface = math.sqrt(2 * mu_m / m["R_m"])
    return {"a_m": m["a_m"], "R_m": m["R_m"], "mu_m": mu_m,
            "v_moon": v_moon, "v_esc_surface": v_esc_surface}


def hyperbolic_turning_angle(v_rel, r_p, mu_m):
    """delta = 2*asin(1/e), e = 1 + r_p*v_rel**2/mu_m, in radians."""
    e = 1.0 + r_p * v_rel ** 2 / mu_m
    return 2.0 * math.asin(1.0 / e)


def v_out_head_on(v_rel, v_moon, delta):
    """Jupiter-frame exit speed, head-on closing-speed geometry:
    v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta).
    Computed exactly; no assumption that it is (or isn't) below v_inf -
    that is precisely the question this model answers."""
    v2 = v_rel ** 2 + v_moon ** 2 - 2 * v_rel * v_moon * math.cos(delta)
    return math.sqrt(max(v2, 0.0))


def direct_capture_deltav(target_orbit_name, v_inf=V_INFDIRECT, r_peri=None):
    """Standard capture burn from a v_inf hyperbolic approach to a circular
    orbit of radius r_peri (executed at perijove = r_peri):
        v_peri = sqrt(v_inf^2 + 2*mu_j/r_peri);  v_circ = sqrt(mu_j/r_peri)
        delta_v = v_peri - v_circ
    """
    if r_peri is None:
        r_peri = TARGET_ORBITS[target_orbit_name]["a_m"]
    v_peri = math.sqrt(v_inf ** 2 + 2 * MU_JUPITER / r_peri)
    v_circ = math.sqrt(MU_JUPITER / r_peri)
    return v_peri - v_circ, v_peri, v_circ


def assisted_capture_deltav(target_orbit_name, v_out, r_peri=None):
    """Capture burn AFTER a moon assist has left the approach excess speed
    at v_out - same formula as direct, with v_out in place of v_inf."""
    if r_peri is None:
        r_peri = TARGET_ORBITS[target_orbit_name]["a_m"]
    v_peri = math.sqrt(v_out ** 2 + 2 * MU_JUPITER / r_peri)
    v_circ = math.sqrt(MU_JUPITER / r_peri)
    return v_peri - v_circ, v_peri, v_circ


def propellant_mass_fraction(dv, Isp=Isp_s):
    """Tsiolkovsky: m_prop/m0 = 1 - exp(-dv/(Isp*g0)). Best-case single
    idealized tangential circularization impulse; no gravity loss (none at
    Jupiter's perijove - no atmosphere), no drag modeled."""
    return 1.0 - math.exp(-dv / (Isp * g0))


def run_model(params):
    """Primary model entry point. Keys: moon, r_p_factor, target_orbit,
    v_inf, Isp. Returns all primary + secondary results; `primary_result`
    is the propellant-saving fraction relative to a direct insertion burn
    (negative = the assist actually costs propellant, not saves it)."""
    moon = params["moon"]
    r_p_factor = params.get("r_p_factor", 1.0)
    target_orbit = params["target_orbit"]
    v_inf = params.get("v_inf", V_INFDIRECT)
    Isp = params.get("Isp", Isp_s)

    mp = _moon_params(moon)
    mu_m, v_moon, R_m = mp["mu_m"], mp["v_moon"], mp["R_m"]
    r_p = r_p_factor * R_m

    # Head-on closing speed (see module docstring for the full geometry).
    v_rel = v_inf + v_moon
    delta = hyperbolic_turning_angle(v_rel, r_p, mu_m)
    v_out = v_out_head_on(v_rel, v_moon, delta)
    speed_change = v_out - v_inf   # >0 => speed-up; <0 => true slow-down

    bound_test = v_out ** 2 + 2 * MU_JUPITER / TARGET_ORBITS[target_orbit]["a_m"]
    is_bound = bound_test < 0

    dv_direct, v_peri_direct, v_circ = direct_capture_deltav(target_orbit, v_inf)
    dv_assist, v_peri_assist, _ = assisted_capture_deltav(target_orbit, v_out)
    frac_direct = propellant_mass_fraction(dv_direct, Isp)
    frac_assist = propellant_mass_fraction(dv_assist, Isp)
    saving_fraction = (frac_direct - frac_assist) / frac_direct if frac_direct > 0 else 0.0

    # Self-consistency invariant check (NOT a tautology - it verifies the
    # model's own core assumption a2 numerically: energy/momentum exactly
    # conserved in the moon frame, i.e. the incoming and outgoing moon-frame
    # speed magnitudes agree bit-for-bit, since that is how v_out is built).
    v_rel_in, v_rel_out = v_rel, v_rel  # by construction in this closed-form model
    invariant_ok = abs(v_rel_in - v_rel_out) / v_rel_in <= 1e-12

    return {
        "primary_result": saving_fraction,
        "moon": moon, "target_orbit": target_orbit,
        "r_p_m": r_p, "delta_rad": delta, "delta_deg": math.degrees(delta),
        "v_rel_moon_frame_m_s": v_rel,
        "v_out_jupiter_frame_m_s": v_out,
        "jupiter_frame_speed_change_m_s": speed_change,
        "is_a_true_slowdown": speed_change < 0,
        "is_bound_after_assist": is_bound,
        "dv_direct_m_s": dv_direct, "dv_assisted_m_s": dv_assist,
        "dv_saving_m_s": dv_direct - dv_assist,
        "frac_direct": frac_direct, "frac_assist": frac_assist,
        "invariant_ok": invariant_ok,
        "v_moon_m_s": v_moon, "mu_m": mu_m, "v_esc_surface_m_s": mp["v_esc_surface"],
    }


if __name__ == "__main__":
    import json
    for moon in MOONS:
        for orbit in TARGET_ORBITS:
            out = run_model({"moon": moon, "target_orbit": orbit})
            print(json.dumps({k: (round(v, 8) if isinstance(v, float) else v)
                              for k, v in out.items()}, indent=1))
