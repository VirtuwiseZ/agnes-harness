p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

old = '''def perigee_sweep_all_moons_all_geometries(r_p_factors):
    out = {"head_on": {}, "overtaking": {}}
    for geom in ("head_on", "overtaking"):
        for name in MOONS:'''
new = '''def perigee_sweep_all_moons_all_geometries(r_p_factors):
    out = {"head_on": {}, "overtaking": {}}
    for geom in ("head_on", "overtaking"):
        for name in _moon_names():'''
assert old in raw, "anchor not found"
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("patched perigee_sweep_all_moons_all_geometries")
