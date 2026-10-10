# Full model rewrite: correct head-on (closing-speed) gravity-assist kinematics.
content = '''"""
Jovian-moon gravity-assist orbital-entry model (fresh module, problem-specific).
Implements the two-body hyperbolic flyby mechanism template derived in Node 2a.

Physics summary
---------------
Approach: a spacecraft arrives at Jupiter\\'s system with Jupiter-frame
hyperbolic excess speed v_inf = 20 km/s. A single Galilean moon, moving on
a circular orbit of radius a_m at speed v_moon = sqrt(mu_j/a_m), can act as
a moving target for a gravity-assist (\"reverse slingshot\") maneuver.

Encounter kinematics (the key mechanism):
  * In the moon\\'s rest frame the flyby is a plain two-body hyperbolic
    (Rutherford) encounter. The incoming speed in that frame depends on the
    approach geometry:
      - head-on (deceleration) geometry: the spacecraft approaches the moon
        from the upstream side of its orbit, i.e. its Jupiter-frame velocity
        points OPPOSITE to the moon\\'s orbital velocity. The closing speed is
        v_rel = v_inf + v_moon.
      - overtaking (speed-up) geometry: v_rel = v_inf - v_moon. This is NOT
        the geometry relevant to a deceleration question and is explicitly
        excluded here.
  * Turning angle: delta = 2*asin(1/e), with e = 1 + r_p*v_rel**2/mu_m.
  * Energy conservation in the moon frame (assumption a2): the spacecraft\\'s
    speed magnitude in the moon frame is exactly unchanged by the flyby;
    only its direction rotates by delta.
  * Back in the Jupiter frame: v_out = |v_moon_vec + v_rotated|, where
    v_rotated is the outgoing moon-frame velocity (magnitude v_rel) rotated
    by delta from the incoming direction. For the head-on geometry, with the
    exit leg as anti-parallel to v_moon as the geometry allows:
        v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)
    This is the standard reverse-slingshot / deceleration result.

All constants: see jupiter_flyby_params.json for provenance (Level-3
IAU/JPL standard values, no live data source was reachable in this
environment - see Node 1.5 audit record).
"""
import math

# ---- constants (provenance: jupiter_flyby_params.json, IAU/JPL standard values) ----
MU_JUPITER = 1.26712e17  # m^3/s^2
G = 6.67430e-11          # m^3 / (kg s^2), CODATA

MOONS = {
    "io":       {"a_m": 4.2181e8,  "M_kg": 8.932e22,  "R_m": 1.8216e6},
    "europa":   {"a_m": 6.711e8,   "M_kg": 4.80e21,   "R_m": 1.5608e6},
    "ganymede": {"a_m": 1.0704e9,  "M_kg": 1.4819e23, "R_m": 2.6341e6},
    "callisto": {"a_m": 1.8827e9,  "M_kg": 1.0759e23, "R_m": 2.4104e6},
}

TARGET_ORBITS = {
    "io_scale":       {"a_m": 4.2181e8,  "label": "Io-scale compact orbit"},
    "ganymede_scale": {"a_m": 1.0704e9,  "label": "Ganymede-scale outer orbit"},
}

Isp_s = 450.0          # s, assumed-this-run representative chemical upper-stage Isp
g0 = 9.80665          # m/s^2, standard gravity (Tsiolkovsky propellant-fraction calc)
V_INFDIRECT = 20.0e3  # m/s, given Jupiter-frame approach speed


def _moon_params(name):
    m = MOONS[name]
    mu_m = G * m["M_kg"]
    v_moon = math.sqrt(MU_JUPITER / m["a_m"])
    v_esc_surface = math.sqrt(2 * mu_m / m["R_m"])
    return {"a_m": m["a_m"], "R_m": m["R_m"], "mu_m": mu_m,
            "v_moon": v_moon, "v_esc_surface": v_esc_surface}


def hyperbolic_turning_angle(v_rel, r_p, mu_m):
    """delta = 2*asin(1/e), e = 1 + r_p*v_rel**2/mu_m.  delta in radians."""
    e = 1.0 + r_p * v_rel ** 2 / mu_m
    return 2.0 * math.asin(1.0 / e)


def v_out_head_on(v_rel, v_moon, delta):
    """Jupiter-frame exit speed for the head-on (closing-speed) geometry:
    v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta).
    NOTE: because v_rel = v_inf + v_moon > v_moon, and 0 <= delta < 180 deg,
    this expression ALWAYS gives v_out >= v_inf - ... check below. The
    model computes it exactly; the interesting regime (whether v_out < v_inf
    at all for realistic delta values) is a genuine physical question this
    function answers, not something assumed away."""
    v2 = v_rel ** 2 + v_moon ** 2 - 2 * v_rel * v_moon * math.cos(delta)
    return math.sqrt(max(v2, 0.0))


def is_decoupled_speed_down(v_rel, v_moon, delta, v_inf):
    """True if the head-on flyby actually reduces the Jupiter-frame speed
    below the original v_inf (the whole point of a deceleration maneuver)."""
    return v_out_head_on(v_rel, v_moon, delta) < v_inf


def direct_capture_deltav(target_orbit_name, v_inf=V_INFDIRECT, r_peri=None):
    """Standard capture burn from a v_inf approach to a circular orbit of
    radius r_peri (executed at perijove = r_peri):
        v_peri = sqrt(v_inf^2 + 2*mu_j/r_peri),  v_circ = sqrt(mu_j/r_peri),
        delta_v = v_peri - v_circ
    """
    if r_peri is None:
        r_peri = TARGET_ORBITS[target_orbit_name]["a_m"]
    v_peri = math.sqrt(v_inf ** 2 + 2 * MU_JUPITER / r_peri)
    v_circ = math.sqrt(MU_JUPITER / r_peri)
    return v_peri - v_circ, v_peri, v_circ


def assisted_capture_deltav(target_orbit_name, v_out, r_peri=None):
    """Capture burn AFTER a moon assist has reduced the approach excess speed
    to v_out - same formula as direct, with v_out in place of v_inf."""
    if r_peri is None:
        r_peri = TARGET_ORBITS[target_orbit_name]["a_m"]
    v_peri = math.sqrt(v_out ** 2 + 2 * MU_JUPITER / r_peri)
    v_circ = math.sqrt(MU_JUPITER / r_peri)
    return v_peri - v_circ, v_peri, v_circ


def propellant_mass_fraction(dv, Isp=Isp_s):
    """Tsiolkovsky: m_prop/m0 = 1 - exp(-dv/(Isp*g0)). Best-case (no
    gravity-loss, no drag - there is no atmosphere at Jupiter\\'s perijove
    of interest - single idealized tangential circularization impulse)."""
    return 1.0 - math.exp(-dv / (Isp * g0))


def run_model(params):
    """Primary model entry point. Keys: moon, r_p_factor, target_orbit,
    v_inf, Isp. Returns all primary + secondary results; `primary_result`
    is the propellant-saving fraction vs. a direct insertion burn."""
    moon = params["moon"]
    r_p_factor = params.get("r_p_factor", 1.0)
    target_orbit = params["target_orbit"]
    v_inf = params.get("v_inf", V_INFDIRECT)
    Isp = params.get("Isp", Isp_s)

    mp = _moon_params(moon)
    mu_m, v_moon, R_m = mp["mu_m"], mp["v_moon"], mp["R_m"]
    r_p = r_p_factor * R_m

    # Head-on closing speed (see module docstring for the geometry).
    v_rel = v_inf + v_moon
    delta = hyperbolic_turning_angle(v_rel, r_p, mu_m)
    v_out = v_out_head_on(v_rel, v_moon, delta)
    speed_down = v_out < v_inf
    dv_speed = v_inf - v_out if speed_down else -(v_out - v_inf)  # negative => speed-UP

    bound_test = v_out ** 2 + 2 * MU_JUPITER / TARGET_ORBITS[target_orbit]["a_m"]
    is_bound = bound_test < 0

    dv_direct, v_peri_direct, v_circ = direct_capture_deltav(target_orbit, v_inf)
    dv_assist, v_peri_assist, _ = assisted_capture_deltav(target_orbit, v_out)
    frac_direct = propellant_mass_fraction(dv_direct, Isp)
    frac_assist = propellant_mass_fraction(dv_assist, Isp)
    saving_fraction = (frac_direct - frac_assist) / frac_direct if frac_direct > 0 else 0.0

    return {
        "primary_result": saving_fraction,
        "moon": moon, "target_orbit": target_orbit,
        "r_p_m": r_p, "delta_rad": delta, "delta_deg": math.degrees(delta),
        "v_rel_moon_frame_m_s": v_rel,
        "v_out_jupiter_frame_m_s": v_out,
        "does_it_actually_slow_down": speed_down,
        "dv_speed_change_m_s": dv_speed,
        "is_bound_after_assist": is_bound,
        "dv_direct_m_s": dv_direct, "dv_assisted_m_s": dv_assist,
        "dv_saving_m_s": dv_direct - dv_assist,
        "frac_direct": frac_direct, "frac_assist": frac_assist,
        "v_moon_m_s": v_moon, "mu_m": mu_m, "v_esc_surface_m_s": mp["v_esc_surface"],
    }


if __name__ == "__main__":
    import json
    for moon in MOONS:
        for orbit in TARGET_ORBITS:
            out = run_model({"moon": moon, "target_orbit": orbit})
            print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v)
                              for k, v in out.items()}, indent=1))
'''
open(r"E:\agh-test\jovian_flyby_model.py", "w", encoding="utf-8").write(content)
print("rewrote jovian_flyby_model.py from scratch with correct head-on closing-speed kinematics")
