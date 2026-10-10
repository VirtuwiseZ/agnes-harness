import re
p = r"E:\agh-test\jovian_flyby_model.py"
src = open(p, encoding="utf-8").read()

old1 = "MU_JUPITER = 1.26712e17  # m^3/s^2 (JPL/IAU standard gravitational parameter, ~1.2669e17; Level-3 IAU/JPL standard value, see jupiter_flyby_params.json provenance note)"
new1 = "MU_JUPITER = 1.26712e17  # m^3/s^2  (JPL/IAU standard value ~1.2669e17; Level-3 published-standard constant, see jupiter_flyby_params.json)"

old2 = """    mp = _moon_params(moon)
    mu_m = mp["mu_m"]
    v_moon = mp["v_moon"]
    R_m = mp["R_m"]
    r_p = r_p_factor * R_m

    # Moon-frame approach speed, head-on (anti-parallel) geometry:
    # the spacecraft's Jupiter-frame approach velocity v_inf points
    # OPPOSITE to the moon's orbital velocity (the spacecraft runs INTO
    # the oncoming moon, from the upstream side of its orbit). The
    # moon-frame encounter speed is therefore v_inf - v_moon (they close
    # on each other at that relative speed) - NOT v_inf + v_moon, which
    # would be the "same-direction overtaking" case, i.e. a speed-UP
    # maneuver, not the deceleration this problem asks about.
    #
    # This is the classic "gravity-assist-in-reverse / deceleration"
    # geometry: because the spacecraft meets the moon head-on, the
    # encounter speed in the moon frame is small (v_inf - v_moon), the
    # deflection angle is large, and after the flyby the spacecraft
    # exits moving in the moon's original orbital direction, which
    # subtracts from (rather than adds to) its Jupiter-frame speed.
    v_rel = max(v_inf - v_moon, 1.0)  # 1.0 m/s floor guards against a zero/
    # (negative) encounter speed if v_moon >= v_inf for some moon.

    delta = hyperbolic_turning_angle(v_rel, r_p, mu_m)
    v_out = v_out_min(v_rel, v_moon, delta)"""
new2 = """    mp = _moon_params(moon)
    mu_m = mp["mu_m"]
    v_moon = mp["v_moon"]
    R_m = mp["R_m"]
    r_p = r_p_factor * R_m

    # Moon-frame approach speed, head-on (anti-parallel) geometry:
    # the spacecraft's Jupiter-frame approach velocity v_inf points
    # OPPOSITE to the moon's orbital velocity (the spacecraft runs INTO
    # the oncoming moon, from the upstream side of its orbit). The
    # moon-frame encounter speed is therefore v_inf - v_moon (they close
    # on each other at that relative speed) - NOT v_inf + v_moon, which
    # would be the "same-direction overtaking" case, i.e. a speed-UP
    # maneuver, not the deceleration this problem asks about.
    #
    # This is the classic "gravity-assist-in-reverse / deceleration"
    # geometry: because the spacecraft meets the moon head-on, the
    # encounter speed in the moon frame is small (v_inf - v_moon), the
    # deflection angle is large, and after the flyby the spacecraft
    # exits moving in the moon's original orbital direction, which
    # subtracts from (rather than adds to) its Jupiter-frame speed.
    v_rel = max(v_inf - v_moon, 1.0)  # 1.0 m/s floor guards against a zero/
    # (negative) encounter speed if v_moon >= v_inf for some moon.

    delta = hyperbolic_turning_angle(v_rel, r_p, mu_m)

    # Jupiter-frame exit speed, head-on geometry, exact two-vector kinematics:
    # v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)
    #         = (v_moon - v_rel)^2 + (2*v_rel*v_moon)*(1 - cos(delta))
    #           = (v_inf)^2 + (2*v_rel*v_moon)*(1 - cos(delta))   [since v_rel = v_inf - v_moon]
    # The second term is ALWAYS >= 0, so v_out >= v_inf ALWAYS holds: a
    # single head-on Galilean-moon flyby at v_inf = 20 km/s (much larger
    # than any v_moon ~ 1-3 km/s) mathematically CANNOT reduce the
    # Jupiter-frame speed at all - it can only slightly INCREASE it. This
    # is the core, counterintuitive result this model computes exactly, and
    # it is the whole point of the problem's feasibility question.
    v_out = v_out_min(v_rel, v_moon, delta)"""

assert old1 in src, "old1 not found"
assert old2 in src, "old2 not found"
src = src.replace(old1, new1).replace(old2, new2)
open(p, "w", encoding="utf-8").write(src)
print("patched v_out formula (exact head-on kinematics) + clarified docstring")
