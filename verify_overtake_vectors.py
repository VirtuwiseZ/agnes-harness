"""Independent, from-scratch vector-geometry re-derivation of the overtaking
('parallel incoming vectors') flyby case, to verify the model's
'v_moon - 2*v_rel*sin(delta/2)' (Sub-case D) formula is actually correct.

Setup (moon's frame):
- Moon M at origin, orbital velocity Vm (Jupiter frame).
- Spacecraft approaches with velocity Vm - V_rel (i.e. it's slower than the
  moon by V_rel in the Jupiter frame -> in the MOON's frame the spacecraft's
  incoming speed is V_rel, coming from 'behind' relative to the moon's motion,
  i.e. the spacecraft's moon-frame velocity points OPPOSITE to the moon's
  own Jupiter-frame velocity Vm... wait, that's exactly the head-on/closing
  geometry in disguise. Let me redo this carefully, in TWO distinct setups,
  and just compute all of them numerically with actual vector arithmetic
  (no closed-form shortcuts), so I can compare against the closed-form
  model's output and see which one (if any) is actually right.
"""
import math
import numpy as np


def turning_angle(r_p, v_rel, mu_m):
    e = 1.0 + r_p * v_rel ** 2 / mu_m
    return 2.0 * math.asin(1.0 / e)


def exact_vector_sim(name, vm, v_rel, delta_rad, geometry):
    """Do the ACTUAL vector bookkeeping in the moon's frame and Jupiter's
    frame, no shortcuts, for both geometries. geometry in ('head_on',
    'overtake_slow_sc', 'overtake_fast_sc') - the last two are the two
    distinct 'same-direction' sub-cases (spacecraft slower vs. faster than
    the moon), which are genuinely different physics, not just a sign flip
    of one formula, and this check exists to find out exactly which closed-
    form expression (if any) each one actually maps to."""
    if geometry == "head_on":
        # Spacecraft comes IN anti-parallel to Vm (closing): incoming moon-
        # frame velocity = -(v_rel) * xhat where xhat is the moon's orbital
        # velocity direction; after deflection by delta (outgoing velocity
        # rotated delta AWAY from incoming, toward the +xhat side, since
        # that's the 'grazing the far side' favorable-deflection choice -
        # but for a HEAD-ON case the outgoing direction rotated delta from
        # -xhat can go to EITHER side; the standard 'maximum deflection
        # effect on the Jupiter-frame speed' choice is the one that rotates
        # TOWARD +xhat, i.e. outgoing moon-frame velocity = v_rel * (sin(delta)*yhat - cos(delta)*xhat)... let's just
        # parameterize it cleanly: incoming = v_rel * (-1, 0); outgoing =
        # v_rel * (-cos(delta), -sin(delta)) is the 'rotate by delta
        # counterclockwise' convention - the MAGNITUDE is unchanged (good,
        # energy conserved in the moon's frame), and we'll just compute the
        # resulting Jupiter-frame speed for that specific choice, and ALSO
        # for the mirror-image clockwise choice, to see if the model's
        # single-formula 'minus-sign' expression matches either one.
        v_in_moon = np.array([-v_rel, 0.0])
        v_out_moon_ccw = np.array([-v_rel * math.cos(delta_rad), -v_rel * math.sin(delta_rad)])
        v_out_moon_cw = np.array([-v_rel * math.cos(delta_rad), +v_rel * math.sin(delta_rad)])
        Vm_vec = np.array([vm, 0.0])
        jup_ccw = np.linalg.norm(v_out_moon_ccw + Vm_vec)
        jup_cw = np.linalg.norm(v_out_moon_cw + Vm_vec)
        return {"v_out_moon_ccw_jupiter": jup_ccw, "v_out_moon_cw_jupiter": jup_cw}

    elif geometry == "overtake_slow_sc":
        # Spacecraft SLOWER than the moon (v_inf < vm), same direction as
        # the moon's orbit: in the moon's frame the spacecraft's incoming
        # velocity = (v_inf - vm) * xhat = -v_rel * xhat (since v_rel =
        # vm - v_inf > 0 here) - this is EXACTLY the same moon-frame
        # incoming vector as the head_on case above! So the entire
        # 'overtaking' case, when the spacecraft is the SLOWER body, is
        # mathematically identical to the head-on/closing case in the
        # moon's frame, differing only in what the incoming Jupiter-frame
        # velocity's DIRECTION is relative to the moon's own motion
        # (anti-parallel vs. parallel-but-slower). The OUTCOMING Jupiter-
        # frame speed, however, depends ONLY on the moon-frame outgoing
        # vector + Vm, so it is IDENTICAL to the head_on case's result,
        # for the same (v_rel, delta). This is the key structural
        # identity this whole check is meant to confirm - if true, the
        # model's 'Sub-case D' formula (vm - 2*v_rel*sin(delta/2)) is
        # WRONG, because it's not a distinct case at all, it's just the
        # head-on formula wearing different clothes.
        v_in_moon = np.array([-(vm - v_rel), 0.0])  # = -v_rel * xhat, since v_rel = vm - v_inf... wait, v_rel here IS vm - v_inf by definition of this sub-case
        # Actually let's just recompute cleanly: incoming Jupiter-frame
        # velocity = (v_inf) * xhat = (vm - v_rel) * xhat (since v_rel = vm - v_inf in this sub-case)
        v_in_jup = np.array([(vm - v_rel), 0.0])
        v_in_moon = v_in_jup - np.array([vm, 0.0])  # = -v_rel * xhat, confirmed, same as head_on
        v_out_moon_ccw = np.array([-v_rel * math.cos(delta_rad), -v_rel * math.sin(delta_rad)])
        jup_ccw = np.linalg.norm(v_out_moon_ccw + np.array([vm, 0.0]))
        v_out_moon_cw = np.array([-v_rel * math.cos(delta_rad), +v_rel * math.sin(delta_rad)])
        jup_cw = np.linalg.norm(v_out_moon_cw + np.array([vm, 0.0]))
        return {"v_out_moon_ccw_jupiter": jup_ccw, "v_out_moon_cw_jupiter": jup_cw,
                "note": "structurally identical to head_on in the moon's frame"}

    elif geometry == "overtake_fast_sc":
        # Spacecraft FASTER than the moon (v_inf > vm), same direction as
        # the moon's orbit: v_rel = v_inf - vm. Incoming Jupiter-frame
        # velocity = v_inf * xhat = (vm + v_rel) * xhat. In the moon's
        # frame: incoming = v_rel * xhat (a POSITIVE multiple of xhat,
        # unlike the head_on/slow_sc case's NEGATIVE multiple). This is a
        # GENUINELY DIFFERENT incoming configuration in the moon's frame -
        # the spacecraft approaches the moon from BEHIND (overtaking it),
        # not from in front. After deflection by delta (outgoing velocity
        # rotated delta from the incoming direction, 'grazing the far
        # side' = rotating TOWARD -xhat, the direction opposite the moon's
        # own motion, which is the favorable-deflection choice for making
        # the spacecraft FASTER in the Jupiter frame - this is the classic
        # 'Voyager gains speed off Jupiter' geometry, EXCEPT here it's a
        # Galilean moon, not Jupiter, and the 'gain' magnitude is bounded
        # by the same 2*v_rel*sin(delta/2) structure):
        v_in_moon = np.array([v_rel, 0.0])
        v_out_moon_ccw = np.array([v_rel * math.cos(delta_rad), v_rel * math.sin(delta_rad)])
        jup_ccw = np.linalg.norm(v_out_moon_ccw + np.array([vm, 0.0]))
        v_out_moon_cw = np.array([v_rel * math.cos(delta_rad), -v_rel * math.sin(delta_rad)])
        jup_cw = np.linalg.norm(v_out_moon_cw + np.array([vm, 0.0]))
        return {"v_out_moon_ccw_jupiter": jup_ccw, "v_out_moon_cw_jupiter": jup_cw,
                "note": "genuinely distinct from head_on in the moon's frame (incoming +xhat vs -xhat); the closed-form expression for this case is v_out_jup = vm + v_rel*cos(delta) +/- v_rel*sin(delta) (the two mirror choices)"}


# Use real numbers from the model's parameter set, one example per sub-case
# to see which closed-form (if any) reproduces the exact vector-sim answer.
V_INF = 20000.0
moons = [
    ("io", 17332.06, 4.2181e8, 8.932e22, 1.8216e6),
    ("europa", 13740.9, 6.711e8, 4.80e21, 1.5608e6),
    ("ganymede", 10880.2, 1.0704e9, 1.4819e23, 2.6341e6),
    ("callisto", 8203.9, 1.8827e9, 1.0759e23, 2.4104e6),
]
G = 6.67430e-11

print("=== Sub-case: spacecraft SLOWER than moon (never true for any of the 4 at v_inf=20km/s, "
      "but checked for completeness to confirm the structural-identity claim) ===")
for name, vm, a, M, R in moons:
    mu_m = G * M
    if V_INF < vm:
        v_rel = vm - V_INF
        delta = turning_angle(R, v_rel, mu_m)
        sim = exact_vector_sim(name, vm, v_rel, delta, "overtake_slow_sc")
        # Model's Sub-case D closed form (the one currently in the code, WRONG-sign-for-this-sub-case suspect):
        model_D = vm - 2.0 * v_rel * math.sin(delta / 2.0)
        print(f"{name:9s}  v_rel={v_rel/1e3:.4f} km/s  delta={delta*180/math.pi:.4f} deg  "
              f"sim(ccw)={sim['v_out_moon_ccw_jupiter']/1e3:.4f}  sim(cw)={sim['v_out_moon_cw_jupiter']/1e3:.4f}  "
              f"model_D_closed_form={model_D/1e3:.4f}")

print("\n=== Sub-case: spacecraft FASTER than moon (the ACTUAL case for all 4 Galilean moons at v_inf=20 km/s) ===")
for name, vm, a, M, R in moons:
    mu_m = G * M
    v_rel = V_INF - vm
    delta = turning_angle(R, v_rel, mu_m)
    sim = exact_vector_sim(name, vm, v_rel, delta, "overtake_fast_sc")
    # The model's CURRENT formula for Sub-case D (spacecraft faster), applied blindly:
    model_current = vm - 2.0 * v_rel * math.sin(delta / 2.0)
    # The physically-correct 'gains speed off a slower body' closed form
    # (the classic gravity-assist 'maximum gain' result, dv = 2*v_rel*sin(delta/2),
    # APPLIED IN THE FAVORABLE DIRECTION - but note: here the spacecraft is
    # the faster body, so the 'gain' interpretation only applies to the
    # moon catching up scenario, NOT this one - for THIS one (spacecraft
    # overtaking the moon), the favorable-deflection choice actually makes
    # the spacecraft SLOWER in the Jupiter frame, which is the mirror image
    # of the classic result, and the closed form is:
    model_correct_fast = vm + v_rel * math.cos(delta) - v_rel * math.sin(delta)  # one mirror choice
    model_correct_fast_alt = vm + v_rel * math.cos(delta) + v_rel * math.sin(delta)  # the other
    print(f"{name:9s}  v_rel={v_rel/1e3:.4f} km/s  delta={delta*180/math.pi:.4f} deg")
    print(f"          sim(ccw)={sim['v_out_moon_ccw_jupiter']/1e3:.4f}  sim(cw)={sim['v_out_moon_cw_jupiter']/1e3:.4f}")
    print(f"          model_current_formula={model_current/1e3:.4f}   closed_form_choice_A={model_correct_fast/1e3:.4f}   choice_B={model_correct_fast_alt/1e3:.4f}")
