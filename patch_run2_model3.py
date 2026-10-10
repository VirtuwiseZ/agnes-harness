p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

old = '''    overtake_shown = {name: single_encounter_all_moons("overtaking", r_p_factor=1.0)[name] for name in MOONS}'''
new = '''    overtake_shown = {name: single_encounter_all_moons("overtaking", r_p_factor=1.0)[name] for name in _moon_names()}'''
assert old in raw, "anchor not found"
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("patched overtake_shown")
