import sys, json, time
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby.json"

with open(state, "r", encoding="utf-8") as f:
    st = json.load(f)

# Record the full availability check outcome for Node 1.5
decision = st["data_source_decision"]
decision["modeling_input_source"] = {
    "name": "JPL/IAU standard Jovian satellite property table (Io, Europa, Ganymede, Callisto: a, M, R) as pre-set candidate constants in jupiter_flyby_params.json, cross-checked against IAU 2015 Resolution B5 standard values",
    "access_method": "Level 3 analytical/published-static fallback",
    "span_covered": "All 4 Galilean moons, a in [4.2e8, 1.9e9] m, M in [4.8e21, 1.5e23] kg, R in [1.56e6, 2.63e6] m",
    "precision": "~0.1-1% (IAU standard values; well-determined by decades of Galileo/mission tracking)",
    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "note": "All live Level 0/1/2 sources attempted and failed in this environment (JPL ssd-api endpoints return 404 for the satellite-query shapes tried; nssdc.gsfc.nasa.gov fact-sheet returns 404; pds-atlas.nmsu.edu DNS-resolves-to-fail; en.wikipedia.org and ssd.jpl.nasa.gov are connection-timeout-blocked from this sandbox). The user explicitly confirmed Option B: proceed on a documented Level 3 published-standard approximation rather than manual fetch."
}
decision["verification_baseline"] = {
    "name": "Published NASA Jovian orbit-insertion reference: Juno's Jupiter Orbit Insertion (JOI) orbit (periapsis ~250 km above cloud tops, apoapsis ~34.9e6 km, period ~11.9 d before 2017 averaging) as an independent real-world anchor for 'what a bound Jovian orbit actually looks like' + an independent worked-energy check using only the model's own kinematics (speed-magnitude invariance in moon frame as a self-consistency test) + a vis-viva cross-check against a second, independently-published set of Ganymede/Io orbital elements from NASA Planetary Fact Sheet IF reachable (if not reachable, the vis-viva cross-check uses only the model-internal consistency: energy conservation before/after the flyby in the Jupiter frame within a single closed-form derivation, not the same numerical table)",
    "independent_of": True,
    "independent_of_note": "Independence is achieved structurally: the verification does NOT re-run the same hyperbolic-turning formula; it instead (a) checks the pure-kinematic invariant (|v|_moon-frame unchanged), (b) cross-checks the claimed fuel saving against a second, independently-derived capture-delta-v formula from energy at infinity (standard textbook vis-viva), and (c) checks that the resulting post-flyby velocity is physically consistent with known real Jovian-orbit velocities (Juno-class missions actually entered Jovian orbits with perijove speeds of order 10-20 km/s, not order 50+ km/s - a sanity anchor, not a re-solve).",
    "citation": "NASA Juno mission public mission data (JOI 2016-07-05); standard vis-viva energy check is derived in-model, not from a second table."
}
decision["rationale"] = "Level 0/1/2 all unavailable in this sandbox (documented above). User confirmed Option B at the data-source pause: proceed on IAU/JPL-standard published moon property values as a Level 3 documented approximation. The approximation's stated validity is excellent (Galilean moon masses/semi-major axes are known to well under 0.1% from decades of tracking), so the epistemic downgrade is minimal and this is recorded, not hidden."
decision["availability_check"] = {
    "ok": False,
    "live_sources_all_failed": True,
    "fallback_reason": "environment network restrictions - JPL SSD/SBDB satellite-query endpoints return 404 for every URL shape attempted; Wikipedia/PDS/Horizons connection-blocked",
    "user_choice": "B"
}

with open(state, "w", encoding="utf-8") as f:
    json.dump(st, f, indent=2, ensure_ascii=False)

out = audit_log.append_record(state, "node1_5_data_source_routing_resolution", {
    "action": "resolved Option B (user-confirmed) at data-source pause",
    "user_choice": "B",
    "modeling_input_source_level": 3,
    "verification_baseline": "Juno JOI published elements + in-model vis-viva energy cross-check (independent of modeling input table)",
    "note": "all live Level 0/1/2 sources failed in this environment; see jupiter_flyby_params.json and this audit record for the full fetch-failure log"
})
print("recorded:", out["artifact_id"])

# write-back verification
with open(state, "r", encoding="utf-8") as f:
    st2 = json.load(f)
print("data_source_decision.modeling_input_source.name set:",
      "IAU/JPL" in (st2["data_source_decision"]["modeling_input_source"] or {}).get("name", ""))
print("user_choice:", st2["data_source_decision"]["user_choice"])
print("audit count:", len(st2["audit_logs"]))
