import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby.json"

out = audit_log.append_record(state, "node1_5_data_source_routing", {
    "action": "availability check for external Jovian-moon property data",
    "attempted_sources": [
        "https://nssdc.gsfc.nasa.gov/planetary/factsheet/satellite_facts.html",
        "https://ssd-api.jpl.nasa.gov/sats?sats=ganymede",
        "https://en.wikipedia.org/wiki/Ganymede_(moon)",
        "https://data.nasa.gov"
    ],
    "result": "all blocked in this environment (non-public IP resolution); no local Level-0 package (astropy/sunpy) installed; Level 2/3 fallback (published static table / memorized textbook constants) available but requires user confirmation per protocol, since agent may not unilaterally pick a downgrade",
    "decision": "STOP_AND_ASK_USER_OPTION_A_OR_B"
})
print("recorded:", out["artifact_id"])

# write anomaly
with open(state, "r", encoding="utf-8") as f:
    st = json.load(f)
st["anomalies"].append({
    "type": "data_source_unavailable",
    "note": "Node 1.5: all live external Jovian-moon property sources unreachable in this environment; no local Level-0 package. Offering Option A (user manual fetch) vs Option B (proceed on Level 3 analytical approximation = IAU/JPL-standard published moon property values as a fixed candidate table in jupiter_flyby_params.json, clearly flagged in the report as approximation-based, not live-fetched data). user_choice: pending",
    "artifact_id": out["artifact_id"]
})
with open(state, "w", encoding="utf-8") as f:
    json.dump(st, f, indent=2, ensure_ascii=False)
print("anomaly logged; anomaly count now:", len(st["anomalies"]))
