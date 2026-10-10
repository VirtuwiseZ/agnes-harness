"""Definitive check of which sign convention is physically correct for the
overtaking ("catching up to a fast moon, exiting on the far side") case,
against the well-known Voyager-class result: a gravity assist OFF THE FRONT
OF A FAST BODY GIVES A LARGE SPEED GAIN relative to the central body's frame,
of order ~2*v_moon for the most favorable geometry. The correct magnitude for
"Ganymede-class" (v_moon ~ 10.88 km/s, v_rel ~ 9 km/s, delta ~ 156 deg) in the
gain form should land somewhere in the 15-30 km/s range, definitely NOT ~4 km/s
(a speed DROP), which would make no physical sense for a "gains speed" case.
"""
import math

# Recompute with the CORRECTLY-paired (v_rel, delta, sign) - the deflection
# angle delta is defined from the COMING-IN direction; for the overtaking
# "fastest gain" geometry the exit vector sits delta AWAY from the coming-in
# direction, on the side toward the moon's own velocity direction (the far
# side of the moon), so in the central-body frame:
#   v_out = v_moon + (v_rel rotated by delta, AWAY from anti-parallel-to-moon
#   ... actually the standard result is:
#       dv (the velocity change in the central-body frame) magnitude = 2*v_rel*sin(delta/2)
#   and for the favorable "gain" case this dv vector points roughly ALONG
#   v_moon, so v_out ~ v_moon + 2*v_rel*sin(delta/2) for the best alignment.
# Let's check THAT formula (independent of the two-vector-cosine-form sign
# confusion entirely):
cases = [
    ("io", 17332.06, 2.6679e3, 172.4475),
    ("europa", 13740.9, 6.2591e3, 114.2077),
    ("ganymede", 10880.2, 9.1198e3, 156.1022),
    ("callisto", 8203.9, 11.7961e3, 145.6384),
]
for label, vm, v_rel, delta_deg in cases:
    delta = math.radians(delta_deg)
    dv_mag = 2 * v_rel * math.sin(delta / 2)
    v_out_best = vm + dv_mag  # most favorable alignment: dv fully along v_moon
    print(f"{label:9s}  v_moon={vm/1e3:.4f} km/s  v_rel={v_rel/1e3:.4f} km/s  delta={delta_deg:.2f} deg  "
          f"dv_mag={dv_mag/1e3:.4f} km/s  v_out(max-aligned gain)={v_out_best/1e3:.4f} km/s")
