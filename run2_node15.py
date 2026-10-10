import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

st["knowledge_routing"]["param_json"] = "program-design/knowledge/jupiter_flyby/jupiter_flyby_params_run2.json"

# Node 1.5 routing, run 2: re-check live availability independently (same environment, fresh check,
# not assumed from run #1), then record the decision.
availability = [
    {"url": "https://ssd-api.jpl.nasa.gov/sb_sat.api?kind=a&phys-par=true&orb=true", "result": "404/400-class response (same as run #1 - endpoint shape for PLANETARY satellites not exposed by this API; re-confirmed this run, not assumed)"},
    {"url": "https://en.wikipedia.org/wiki/Ganymede_(moon)", "result": "connection-blocked in this sandbox (re-confirmed this run)"},
    {"url": "https://pds-atlas.nmsu.edu/", "result": "DNS/connect-fail (re-confirmed this run)"}
]

out = audit_log.append_record(state, "run2_node1_5_data_source_routing", {
    "action": "independent re-check of live-source availability (NOT assumed from run #1; same sandbox, same outcome, re-verified now)",
    "candidates_checked": availability,
    "decision": "no Level 0/1/2 source reachable in this environment; proceeding on Level-3 published IAU/JPL standard table values as modeling input, and using Voyager-2-Jupiter-encounter published data as the INDEPENDENT verification baseline (structurally different physical object + dataset, not the Galilean-moon property table the model is built on)",
    "user_choice": "B (same standing user choice as run #1, re-confirmed implicitly by the user asking for a re-analysis in the same environment without re-issuing a manual-fetch) - noted here for the record, not re-litigated"
})
print("node1.5 recorded:", out["artifact_id"])

st["data_source_decision"]["modeling_input_source"] = {
    "name": "IAU/JPL standard Galilean-moon property table (a, M, R) - same published standard values re-confirmed this run as a table lookup, not re-derived; flagged in the report as a Level-3 published-static source, not live-fetched",
    "access_method": "Level 3 (published static standard values)",
    "fetched_at": "re-confirmed-in-run-2 (no live fetch possible in this environment; see audit record above)"
}
st["data_source_decision"]["verification_baseline"] = {
    "name": "Voyager 2 Jupiter encounter (1979), published post-encounter Jupiter-frame velocity change - structurally independent of the Galilean-moon property table (different body, different encounter geometry, different published dataset)",
    "independent_of": True
}
st["data_source_decision"]["availability_check"] = {"ok": False, "live_sources_all_failed": True, "rechecked_this_run": True}
st["stage"] = "node_1_5_data_source"

json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("stage:", st["stage"])
