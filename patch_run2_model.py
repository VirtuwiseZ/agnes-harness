p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

old1 = '''def single_encounter_all_moons(geometry="head_on", r_p_factor=1.0):
    """Sweep all four moons at a fixed perigee factor (r_p = factor * R_moon)
    for EITHER geometry; returns a dict of per-moon results."""
    results = {}
    for name, m in MOONS.items():'''
new1 = '''def _moon_names():
    """Exclude the '_note' bookkeeping string that lives in the same JSON dict
    as the four actual moon entries; only iterate real moon keys."""
    return [k for k in MOONS if not k.startswith("_")]


def single_encounter_all_moons(geometry="head_on", r_p_factor=1.0):
    """Sweep all four moons at a fixed perigee factor (r_p = factor * R_moon)
    for EITHER geometry; returns a dict of per-moon results."""
    results = {}
    for name in _moon_names():
        m = MOONS[name]'''

assert old1 in raw, "anchor 1 not found"
raw = raw.replace(old1, new1)

old2 = '''    pairs = []
    names = list(MOONS.keys())
    for A in names:'''
new2 = '''    pairs = []
    names = _moon_names()
    for A in names:'''
assert old2 in raw, "anchor 2 not found"
raw = raw.replace(old2, new2)

old3 = '''    kepler_checks = {name: kepler_period_check(name) for name in MOONS}'''
new3 = '''    kepler_checks = {name: kepler_period_check(name) for name in _moon_names()}'''
assert old3 in raw, "anchor 3 not found"
raw = raw.replace(old3, new3)

open(p, "w", encoding="utf-8").write(raw)
print("patched all 3 anchors")
