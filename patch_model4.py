# Fix remaining physics error: head-on (anti-parallel) geometry gives v_rel = v_inf + v_moon
# (closing speed), not v_inf - v_moon. The previous "v_inf - v_moon" was actually the
# overtaking/speed-up case, which is not what a deceleration maneuver needs.
import re
p = r"E:\agh-test\jovian_flyby_model.py"
src = open(p, encoding="utf-8").read()

old = """    # This is the classic "gravity-assist-in-reverse / deceleration"
    # geometry: because the spacecraft meets the moon head-on, the
    # encounter speed in the moon frame is small (v_inf - v_moon), the
    # deflection angle is large, and after the flyby the spacecraft
    # exits moving in the moon's original orbital direction, which
    # subtracts from (rather than adds to) its Jupiter-frame speed.
    v_rel = max(v_inf - v_moon, 1.0)  # 1.0 m/s floor guards against a zero/
    # (negative) encounter speed if v_moon >= v_inf for some moon."""
new = """    # This is the classic "gravity-assist-in-reverse / deceleration"
    # geometry: the spacecraft approaches the moon head-on, i.e. from the
    # upstream side of the moon's orbit, so its Jupiter-frame velocity
    # points OPPOSITE to the moon's orbital velocity. The two bodies
    # close on each other at the CLOSING SPEED v_inf + v_moon (not the
    # difference - that would be the same-direction overtaking case, a
    # speed-UP maneuver, not the deceleration this problem asks about).
    # After the flyby the spacecraft exits moving (roughly) in the
    # moon's orbital direction, which subtracts from its Jupiter-frame
    # speed - that is the physical mechanism by which a "reverse
    # slingshot" can slow the spacecraft down in the Jupiter frame.
    v_rel = v_inf + v_moon  # closing speed, head-on (anti-parallel) approach"""

assert old in src, "old block not found"
src = src.replace(old, new)

old2 = """    # Jupiter-frame exit speed, head-on geometry, exact two-vector kinematics:
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
new2 = """    # Jupiter-frame exit speed, head-on geometry, exact two-vector kinematics:
    # v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta),  where now
    # v_rel = v_inf + v_moon (closing speed). Unlike the overtaking case,
    # this can legitimately give v_out < v_inf for sufficiently large
    # delta - that is the whole point of a deceleration maneuver.
    v_out = v_out_min(v_rel, v_moon, delta)"""
assert old2 in src, "old2 block not found"
src = src.replace(old2, new2)

open(p, "w", encoding="utf-8").write(src)
print("patched: v_rel is now v_inf + v_moon (true closing speed for head-on approach)")
