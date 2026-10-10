import json, re

p = r"E:\agh-test\jovian_flyby_model_run2.py"
raw = open(p, encoding="utf-8").read()

# 1. Fix __main__ demo block to use real orbit labels
raw = raw.replace(
    '    base = out["capture_baseline"]["io_scale"]',
    '    io_keys = [k for k in out["capture_baseline"] if "io" in k or k == "orbit_1"]\n'
    '    base_key = [k for k in out["capture_baseline"] if "io" in k][0] if any("io" in k for k in out["capture_baseline"]) else list(out["capture_baseline"].keys())[0]\n'
    '    base = out["capture_baseline"][base_key]'
)

# 2. Rename orbit_1 -> io_scale, orbit_2 -> ganymede_scale at the CAPTURE_ORBITS load site
raw = raw.replace(
    '''CAPTURE_ORBITS = _filter_note_only(CAPTURE_ORBITS)''',
    '''CAPTURE_ORBITS = _filter_note_only(CAPTURE_ORBITS)
# Normalize orbit keys to human-readable labels used throughout the codebase/report:
CAPTURE_ORBITS = {
    "io_scale": CAPTURE_ORBITS.get("orbit_1", CAPTURE_ORBITS.get("io_scale")),
    "ganymede_scale": CAPTURE_ORBITS.get("orbit_2", CAPTURE_ORBITS.get("ganymede_scale")),
}''')
# If orbit_1/io_scale weren't found (keys already normalized), guard:
raw = raw.replace(
    '''CAPTURE_ORBITS = _filter_note_only(CAPTURE_ORBITS)
# Normalize orbit keys to human-readable labels used throughout the codebase/report:
CAPTURE_ORBITS = {
    "io_scale": CAPTURE_ORBITS.get("orbit_1", CAPTURE_ORBITS.get("io_scale")),
    "ganymede_scale": CAPTURE_ORBITS.get("orbit_2", CAPTURE_ORBITS.get("ganymede_scale")),
}''',
    '''CAPTURE_ORBITS = _filter_note_only(CAPTURE_ORBITS)
# Normalize orbit keys to human-readable labels used throughout the codebase/report:
_CAP_ORBITS = CAPTURE_ORBITS
if "io_scale" in _CAP_ORBITS:
    CAPTURE_ORBITS = _CAP_ORBITS
else:
    CAPTURE_ORBITS = {
        "io_scale": _CAP_ORBITS.get("orbit_1"),
        "ganymede_scale": _CAP_ORBITS.get("orbit_2"),
    }
    CAPTURE_ORBITS = {k: v for k, v in CAPTURE_ORBITS.items() if v is not None}''')

open(p, "w", encoding="utf-8").write(raw)
print("patched orbit labels + demo block")
