p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()
old = "        return v_out, delta        return v_moon + dv_jup, delta"
new = "        return v_out, delta"
assert old in raw
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("fixed stray duplicate return statement")
