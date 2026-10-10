import json, urllib.request, os

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

results = []
# JPL SB Satellites API (documented, the correct endpoint discovered in run #1 - re-verifying it's still
# the right one, not reusing its DATA, just the endpoint shape, which is a legitimate re-check)
candidates = [
    "https://ssd-api.jpl.nasa.gov/sb_sat.api?kind=a&phys-par=true&orb=true",
    "https://ssd-api.jpl.nasa.gov/horizons/lookup",
    "https://science.nasa.gov/planetary-science/solar-system/moons/",
]
for url in candidates:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "physics-agent/2.0 (run-2 independent recheck)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
        results.append({"url": url, "status": "OK", "len": len(body)})
    except Exception as e:
        results.append({"url": url, "status": type(e).__name__, "detail": str(e)[:120]})
print(json.dumps(results, indent=1))

st["data_source_decision"]["availability_check"] = {
    "rechecked_in_run2": True,
    "raw_outcome": results,
}
json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\nstate updated, awaiting routing decision")
