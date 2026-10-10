p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

old = '''MOONS = P["named_parameters"]["moons"]
CAPTURE_ORBITS = P["named_parameters"]["capture_orbit_candidates"]'''
new = '''MOONS = P["named_parameters"]["moons"]
CAPTURE_ORBITS = P["named_parameters"]["capture_orbit_candidates"]


def _filter_note_only(d):
    """Drop the '_note' bookkeeping string that JSON dicts in this project
    carry alongside their real data entries; only keep keys with dict values
    (the actual per-moon / per-orbit data rows are always dicts, never strings)."""
    return {k: v for k, v in d.items() if isinstance(v, dict)}


MOONS = _filter_note_only(MOONS)
CAPTURE_ORBITS = _filter_note_only(CAPTURE_ORBITS)'''
assert old in raw, "anchor not found"
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("patched MOONS/CAPTURE_ORBITS load site")
