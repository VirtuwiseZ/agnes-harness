p = r"E:\agh-test\jovian_flyby_model_run2.py"
lines = open(p, encoding="utf-8").read().splitlines(keepends=True)
# Replace lines 454-465 (0-indexed 453-464) with a clean single-line header.
new_block = ['    print("\\n=== OVERTAKING control case (parallel incoming vectors, same direction as the moon), r_p = R_moon, all 4 moons. See model docstring: at v_inf=20 km/s every Galilean moon is SLOWER than the spacecraft, so all four land in Sub-case D (small net speed LOSS, not a Voyager-style gain); this control still matters because it is the ONLY other single-encounter geometry that exists, and its quantified result (below) is needed to close the argument that no single-encounter arrangement - head-on OR overtaking - helps at this approach speed. ===")\n']
assert lines[453].startswith('    print("\\n=== OVERTAKING control case'), f"line 454 mismatch: {lines[453]!r}"
assert lines[464].rstrip().endswith('show. ===")'), f"line 465 mismatch: {lines[464]!r}"
lines[453:465] = new_block
open(p, "w", encoding="utf-8").writelines(lines)
print("fixed the unterminated-string demo header")
