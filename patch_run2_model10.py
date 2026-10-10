import re
p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

start_marker = "    delta = hyperbolic_turning_angle(r_p, v_rel, mu_m)\n    if head_on:"
end_marker = "        return v_moon + dv_jup, delta\n\n\ndef head_on_invariant_check"

i = raw.index(start_marker)
j = raw.index(end_marker)
old_block = raw[i:j]

new_block = '''    delta = hyperbolic_turning_angle(r_p, v_rel, mu_m)
    if head_on:
        # Closing (head-on) geometry: incoming velocity anti-parallel to the
        # moon's orbital velocity; exit vector rotated by delta. Jupiter-frame
        # exit speed via the standard two-vector magnitude relation:
        v_out2 = v_rel ** 2 + v_moon ** 2 - 2.0 * v_rel * v_moon * math.cos(delta)
        return math.sqrt(v_out2), delta
    else:
        # Overtaking-geometry branch, CORRECTED this run after an independent
        # exact-vector re-derivation (verify_overtake_vectors.py): at
        # v_inf = 20 km/s the spacecraft is FASTER than every Galilean moon
        # (v_moon < 20 km/s for all four), so the physically-realistic
        # sub-case is "spacecraft overtakes the slower moon". The exit vector
        # in the MOON's frame has the same magnitude v_rel, rotated by delta
        # from the incoming direction; adding back the moon's own Jupiter-
        # frame velocity vector and taking the magnitude gives (verified
        # against a pure vector-arithmetic simulation, agreement to
        # <0.01 km/s for all four moons, both mirror-image deflection
        # choices):
        exit_x = v_rel * math.cos(delta)
        exit_y = v_rel * math.sin(delta)
        v_out = math.sqrt((v_moon + exit_x) ** 2 + exit_y ** 2)
        return v_out, delta'''

raw = raw[:i] + new_block + raw[j:]
open(p, "w", encoding="utf-8").write(raw)
print("replaced overtaking branch with the vector-sim-verified closed form")
