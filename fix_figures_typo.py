p = r"E:\agh-test\run2_figures.py"
raw = open(p, encoding="utf-8").read()
old = "f\"(a={M.CAP_ORBITS[orbit]['a_m']/1e6:.0f}e6 m). Green=helps, red=costs propellant.\\n\""
new = "f\"(a={M.CAPTURE_ORBITS[orbit]['a_m']/1e6:.0f}e6 m). Green=helps, red=costs propellant.\\n\""
assert old in raw, "anchor not found"
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("fixed CAP_ORBITS -> CAPTURE_ORBITS typo")
