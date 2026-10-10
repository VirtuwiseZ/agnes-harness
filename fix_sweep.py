import json
p = r"E:\agh-test\boundary_spec.json"
spec = json.load(open(p, encoding="utf-8"))
spec["sweep"]["order"] = "increase"
spec["sweep"]["_expectation_note"] = ("as r_p_factor increases (farther flyby), turning angle shrinks, so the "
    "(always-negative-or-zero) propellant-saving value must be monotonically INCREASING toward 0 "
    "(i.e. the magnitude of the negligible negative effect shrinks). This is the physically expected "
    "monotonic direction for this model - verified below by the actual observed sweep.")
json.dump(spec, open(p, "w", encoding="utf-8"), indent=2)
print("fixed sweep order -> increase; rereading back...")
print(json.load(open(p, encoding="utf-8"))["sweep"]["order"])
