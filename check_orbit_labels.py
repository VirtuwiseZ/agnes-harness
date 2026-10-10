import json
p = json.load(open(r"E:\agh-test\program-design\knowledge\jupiter_flyby\jupiter_flyby_params_run2.json", encoding="utf-8"))
co = p["named_parameters"]["capture_orbit_candidates"]
print({k: v for k, v in co.items() if not k.startswith("_")})
