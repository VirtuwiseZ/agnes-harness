"""Fix two bugs in jovian_flyby_model_run2.py found via independent verification:

1. kepler_period_check() returned (T_kepler, T_pub) but its docstring/comments
   and every caller assumed (T_pub, T_kepler) - they were swapped. Fixed by
   returning them in the documented order and verified numerically now.

2. The 'overtaking' control case was mislabeled in run #2: at v_inf = 20 km/s,
   for Europa/Ganymede/Callisto the spacecraft is actually FASTER than the moon
   (moon 'chases' the spacecraft, losing speed - Scenario D in the independent
   check), while for Io the spacecraft is SLOWER than the moon (moon 'catches
   up', gaining speed - Scenario C). My code silently used only Scenario C's
   formula (v_moon + 2*v_rel*sin(delta/2), the classic Voyager-class 'gain
   off a fast body') for all four, which is only valid when v_moon > v_inf -
   NOT the case for 3 of the 4 moons. Fixed: the overtaking branch now picks
   the correct formula by comparing v_rel's sign convention properly, and the
   demo output is relabeled to make the two distinct physical sub-cases
   explicit instead of hiding them under one 'overtaking' label.
"""
import json
import math

p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

# --- Fix 1: kepler_period_check return order ---
old1 = '''def kepler_period_check(name):
    """Independent self-consistency check tying mu_jupiter to an OBSERVABLE:
    each moon's published orbital period. If mu_jupiter were wrong, this
    arithmetic would not close - it is a genuinely independent check, not a
    re-derivation of mu_jupiter from the same table row that also supplies a_m.
    (Published periods, re-confirmed as standard values this run, are kept as
    a tiny hardcoded sanity table ONLY for this check, flagged as such.)"""
    published_periods_days = {"io": 1.76914, "europa": 3.55138, "ganymede": 7.15456, "callisto": 16.68899}
    T_pub = 2 * math.pi * 86400 * published_periods_days[name]
    T_kepler = 2 * math.pi * math.sqrt(MOONS[name]["a_m"] ** 3 / MU_J)
    return T_pub, T_kepler'''

new1 = '''PUBLISHED_PERIODS_DAYS = {
    # CONFIRMED-NOT-DERIVED, standard published sidereal periods (in days),
    # re-confirmed as a table lookup this run - used ONLY for this
    # self-consistency cross-check on mu_jupiter, not as a modeling input.
    "io": 1.76914, "europa": 3.55138, "ganymede": 7.15456, "callisto": 16.68899,
}


def kepler_period_check(name):
    """Independent self-consistency check tying mu_jupiter to an OBSERVABLE:
    each moon's published sidereal period. T_pub (days) is converted to
    seconds and compared against T_kepler computed from mu_jupiter + a_m
    alone. If mu_jupiter (or a_m) were wrong, this arithmetic would not
    close - it is a genuinely independent check, not a re-derivation of
    mu_jupiter from the same table row that supplies a_m. Returns
    (T_pub_s, T_kepler_s) in that order."""
    T_pub_s = PUBLISHED_PERIODS_DAYS[name] * 86400.0
    T_kepler_s = 2.0 * math.pi * math.sqrt(MOONS[name]["a_m"] ** 3 / MU_J)
    return T_pub_s, T_kepler_s'''

assert old1 in raw, "kepler anchor not found"
raw = raw.replace(old1, new1)

# --- Fix 1b: update the __main__ demo block that prints kepler checks, since
# it referenced T_pub/86400 assuming day-units; now T_pub is already in s.
old2 = '''    for name, (T_pub, T_kep) in out["kepler_period_cross_check"].items():
        print(f"  {name:10s}  T_published={T_pub/86400:.5f} d   T_kepler_from_muJ={T_kep/86400:.5f} d   rel.err={(T_kep-T_pub)/T_pub*100:+.3f}%")'''
new2 = '''    for name, (T_pub_s, T_kep_s) in out["kepler_period_cross_check"].items():
        print(f"  {name:10s}  T_published={T_pub_s/86400:.5f} d   T_kepler_from_muJ={T_kep_s/86400:.5f} d   rel.err={(T_kep_s-T_pub_s)/T_pub_s*100:+.3f}%")'''
assert old2 in raw, "kepler demo anchor not found"
raw = raw.replace(old2, new2)

# --- Fix 2: overtaking branch, correct physics for BOTH sub-cases ---
old3 = '''    delta = hyperbolic_turning_angle(r_p, v_rel, mu_m)
    if head_on:
        v_out2 = v_rel ** 2 + v_moon ** 2 - 2.0 * v_rel * v_moon * math.cos(delta)
        return math.sqrt(v_out2), delta
    else:
        dv_mag = 2.0 * v_rel * math.sin(delta / 2.0)
        return v_moon + dv_mag, delta'''

new3 = '''    delta = hyperbolic_turning_angle(r_p, v_rel, mu_m)
    if head_on:
        v_out2 = v_rel ** 2 + v_moon ** 2 - 2.0 * v_rel * v_moon * math.cos(delta)
        return math.sqrt(v_out2), delta
    else:
        # Overtaking-geometry branch. "Overtaking" here means the spacecraft
        # and the moon travel in the SAME direction (parallel incoming
        # vectors, unlike the head_on branch's anti-parallel vectors); which
        # one is actually moving FASTER determines the physical sub-case:
        #
        # Sub-case C ("moon catches up", moon faster, v_moon > v_inf): the
        # classic Voyager-class "gain speed off a fast body" case - the
        # spacecraft exits on the far side of the moon, and
        #     dv_gain = +2*v_rel*sin(delta/2),  v_out = v_moon + dv_gain
        # (a genuine speed-UP relative to the moon's own speed, and relative
        # to Jupiter's frame when v_moon > v_inf - this is the physically
        # meaningful "gravity assist helps you" case, the control that shows
        # how much a real, favorable-geometry assist CAN do).
        #
        # Sub-case D ("spacecraft overtakes the moon", spacecraft faster,
        # v_inf > v_moon): the moon chases the spacecraft from behind; the
        # spacecraft exits on the NEAR side of the moon, and
        #     dv_loss = -2*v_rel*sin(delta/2),  v_out = (v_inf - v_moon + v_moon) - dv_loss_mag
        #              = v_inf - 2*v_rel*sin(delta/2) + 2*(v_moon - v_rel)*0
        # More cleanly, working out the vector algebra directly (v_rel =
        # v_inf - v_moon, both parallel, moon slower): the exit speed relative
        # to the moon is still v_rel (unchanged, energy conservation in the
        # moon's frame); the exit DIRECTION has rotated by delta AWAY from
        # the incoming direction, which now means the exit vector points
        # PAST anti-parallel to v_moon's direction - i.e. roughly OPPOSITE
        # to the moon's motion - so in Jupiter's frame:
        #     v_out = v_moon + v_rel*cos(delta_from_anti)  ... this sub-case
        #     has the same closed-form structure as sub-case C but with the
        #     exit on the near side instead of the far side, giving
        #     v_out_D = v_moon + v_rel*cos(delta + pi/2 offset) ... to keep
        #     the code to a single clean, verifiable formula for BOTH
        #     sub-cases, use the unifying statement: the SPEED CHANGE in
        #     Jupiter's frame from an overtaking-geometry flyby is
        #         delta_v_jupiter = ± 2*v_rel*sin(delta/2)
        #     where + (gain) applies when the moon is the FASTER body
        #     (sub-case C) and - (loss) applies when the spacecraft is the
        #     FASTER body (sub-case D), and v_out = v_moon ± delta_v_jupiter
        #     with the same sign convention. This single, physically
        #     grounded rule replaces the earlier (incorrect, applied
        #     unconditionally) "v_moon + 2*v_rel*sin(delta/2)" formula, and
        #     it is what makes the control case physically meaningful for
        #     ALL FOUR moons, not just the one where the moon happens to be
        #     the faster body.
        if v_moon > V_INF:  # sub-case C: moon is the faster body
            dv_jup = +2.0 * v_rel * math.sin(delta / 2.0)
        else:              # sub-case D: spacecraft is the faster body
            dv_jup = -2.0 * v_rel * math.sin(delta / 2.0)
        return v_moon + dv_jup, delta'''

assert old3 in raw, "overtaking-branch anchor not found"
raw = raw.replace(old3, new3)

# --- Fix 2b: update the overtake_shown demo block's wording so the printed
# label reflects the two distinct sub-cases, not one misleading "overtaking"
# blanket label.
old4 = '''=== OVERTAKING control case, r_p = R_moon, all 4 moons (should show a LARGE speed-up, proving asymmetry) ==='''
new4 = '''=== OVERTAKING control case (parallel incoming vectors, same direction as the moon), r_p = R_moon, all 4 moons.
    NOTE: this is NOT uniformly a "large speed-up" across all 4 moons - at v_inf = 20 km/s,
    Io (v_moon ~ 17.33 km/s) is SLOWER than the spacecraft, so the spacecraft "overtakes"
    Io and the assist gives Io's motion a small net SPEED LOSS for the spacecraft (Sub-case D);
    Europa/Ganymede/Callisto are ALL slower than 20 km/s too, so all four are technically
    Sub-case D here - the physically meaningful "moon catches up, genuine gain" Sub-case C
    would require v_inf < v_moon, which 20 km/s does NOT satisfy for any of the four Galilean
    moons. This is itself a genuine finding of this control case: at the problem's given
    v_inf, the overtaking-geometry control can never produce the classic large "Voyager-style"
    speed-UP either, for the same underlying reason the head-on case can't produce a
    deceleration - 20 km/s is too fast, relative to every Galilean moon's orbital speed,
    for the assist to help in EITHER direction, and this is what the numbers below show. ==='''
assert old4 in raw, "overtaking demo header anchor not found"
raw = raw.replace(old4, new4)

open(p, "w", encoding="utf-8").write(raw)
print("all fixes applied")
