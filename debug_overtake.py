"""Debug the overtaking control case against a hand-closed-form expectation.

Overtaking geometry (v_rel = |v_inf - v_moon|, spacecraft catching up to the
moon from behind, moon's orbital velocity parallel to spacecraft's incoming
velocity). The standard gravity-assist "fastest gain" configuration has the
spacecraft exit on the FAR side of the moon from its incoming direction, so
the exit velocity in the JUPITER frame is:
    v_out^2 = v_moon^2 + v_rel^2 + 2*v_moon*v_rel*cos(delta_from_anti)
where the angle between the incoming direction (parallel to v_moon) and the
outgoing direction (rotated by delta, the deflection angle) is (pi - delta),
giving the +2*v_moon*v_rel*cos(delta) form (cos of the deflection angle from
the PARALLEL incoming config, which is the standard published form - see e.g.
any textbook gravity-assist derivation: delta-v_vector = 2*v_moon*sin(delta/2)
for the "maximum gain" head-on-with-the-moon's-motion case, which is exactly
the +cos(delta) form's small-angle limit).

My model's `head_on=False` branch in v_out_closed_form currently uses the SAME
minus-sign formula as the head_on=True branch, which is WRONG for the
overtaking case - it silently computes the head-on-closing algebra under a
small v_rel, which is why it produced absurdly LOW v_out values.
"""
import math

cases = [
    # (v_inf, v_moon, r_p, mu_m, label)
    (20000.0, 17332.06, 1821600.0, 5.959e15, "io"),
    (20000.0, 13740.9, 1560800.0, 3.202e14, "europa"),
    (20000.0, 10880.2, 2634100.0, 9.892e15, "ganymede"),
    (20000.0, 8203.9, 2410400.0, 7.181e15, "callisto"),
]
for v_inf, vm, rp, mum, label in cases:
    v_rel = abs(v_inf - vm)
    e = 1.0 + rp * v_rel ** 2 / mum
    delta = 2.0 * math.asin(1.0 / e)
    # CORRECT overtaking-gain form (the "fast planet" slingshot, spacecraft
    # coming in from behind, exiting on the far side -> maximum Jupiter-frame
    # speed-up):
    v_out_gain = math.sqrt(vm ** 2 + v_rel ** 2 + 2.0 * vm * v_rel * math.cos(delta))
    # WRONG (current model's) minus-sign form, for comparison:
    v_out_minus = math.sqrt(vm ** 2 + v_rel ** 2 - 2.0 * vm * v_rel * math.cos(delta))
    print(f"{label:9s}  v_rel={v_rel/1e3:7.4f} km/s  delta={delta*180/math.pi:8.4f} deg  "
          f"v_out(CORRECT gain form)={v_out_gain/1e3:8.4f} km/s  "
          f"v_out(current minus form)={v_out_minus/1e3:8.4f} km/s")
