p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

old = '''def v_out_closed_form(r_p, v_rel, v_moon, mu_m, head_on=True):
    """
    head_on=True  : closing geometry, v_rel already = v_inf + v_moon; the exit
                    velocity vector is rotated by delta in the direction that
                    opposes the moon's orbital motion (the only arrangement that
                    could ever decelerate - and as Step 2's invariant proves,
                    it actually cannot, for v_rel > v_moon, which is exactly
                    the v_inf + v_moon case).
    head_on=False : overtaking geometry, v_rel = v_inf - v_moon (control case).
    """
    delta = hyperbolic_turning_angle(r_p, v_rel, mu_m)
    if head_on:
        # incoming vector is anti-parallel to v_moon; exit is rotated by delta
        # away from the incoming direction, toward (not fully past) parallel
        # with -v_moon... in the closing geometry the relevant vector relation
        # is v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta), with
        # delta measured from the anti-parallel (head-on) configuration.
        v_out2 = v_rel ** 2 + v_moon ** 2 - 2.0 * v_rel * v_moon * math.cos(delta)
    else:
        # overtaking: incoming vector is PARALLEL to v_moon (moon catches up
        # from behind); the same algebraic structure applies with the cosine
        # term now favoring a LARGE deflection because v_rel is small, giving
        # v_out^2 = v_rel^2 + v_moon^2 + 2*v_rel*v_moon*cos(delta_from_parallel)
        # which for the standard "gains speed" slingshot case is written, to
        # keep the SAME single closed form, as:
        v_out2 = v_rel ** 2 + v_moon ** 2 - 2.0 * v_rel * v_moon * math.cos(delta)
        # Note: for the overtaking case the relevant geometric angle is
        # (pi - delta) relative to the parallel incoming configuration, but
        # since cos(pi - delta) = -cos(delta), and the standard published
        # gravity-assist result for the "fastest" gain case is
        # v_out^2 = v_rel^2 + v_moon^2 + 2*v_rel*v_moon*cos(delta) - we use
        # the plain minus-sign form above for BOTH cases with the SAME delta
        # formula, which is exactly right for head-on and gives the correct
        # (LARGER) deflection-driven gain for overtaking, since a SMALL v_rel
        # makes delta LARGE, and cos(delta) can be well below 0, making the
        # -2*v_rel*v_moon*cos(delta) term LARGE and POSITIVE, boosting v_out.
    return math.sqrt(v_out2), delta'''

new = '''def v_out_closed_form(r_p, v_rel, v_moon, mu_m, head_on=True):
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
        v_out2 = v_rel ** 2 + v_moon ** 2 - 2.0 * v_rel * v_moon * math.cos(delta)
        return math.sqrt(v_out2), delta
    else:
        dv_mag = 2.0 * v_rel * math.sin(delta / 2.0)
        return v_moon + dv_mag, delta'''

assert old in raw, "v_out_closed_form anchor not found"
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("patched v_out_closed_form with the physically-correct overtaking-gain formula")
