import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

STATE = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby.json"
st = json.load(open(STATE, encoding="utf-8"))

st["stage"] = "node_3_report"
st["report"]["conclusion"] = (
    "NOT feasible as a significant fuel-saving strategy. For every Galilean moon "
    "(Io, Europa, Ganymede, Callisto), a single head-on (closing-speed) gravity-assist "
    "flyby at v_inf = 20 km/s (Jupiter frame) mathematically cannot reduce the "
    "spacecraft's Jupiter-frame speed - the exact two-vector kinematics gives "
    "v_out >= v_inf always (algebraic identity, not a numerical approximation); "
    "computed maximum deflection angles are only 0.02-0.45 deg even skimming a moon's "
    "surface, so the effect is a tiny speed-UP of order 0.0001-0.001%, and the "
    "resulting propellant 'saving' vs. a direct insertion burn is negative "
    "(-0.0002% to -0.0005%), i.e. the maneuver actually costs propellant, never "
    "approaching the 10% 'significant saving' acceptance threshold. Verified via "
    "three independent checks (in-model double-path kinematics, an independent "
    "energy-bookkeeping formula, and a real-mission plausibility anchor: no published "
    "Jovian-orbit-insertion mission has ever used a single moon-assist for deceleration).")
st["report"]["traceability"] = {
    "closing-speed geometry v_rel = v_inf + v_moon": "jovian_flyby_model.py docstring + run_model (head-on branch)",
    "turning angle formula (delta, e)": "jovian_flyby_model.hyperbolic_turning_angle; dimensional gate GATE1 PASS (audit: node2b_dimensional_gate_runs)",
    "v_out two-vector kinematics + v_out>=v_inf identity": "jovian_flyby_model.v_out_head_on; dimensional gate GATE2 PASS",
    "specific-energy dimensional check": "dimensional_gate.py GATE3 PASS (run_dim_gate3.py artifact)",
    "all main-case + perigee-sweep numbers (delta, v_out, saving %)": "problem_state.json numerical_artifacts.main_cases_r_p_equals_R_moon + perigee_factor_sweep (audit: node2b_main_model_run / node2b_perigee_sweep)",
    "boundary/degenerate-limit verdict": "boundary_gate.py, verdict PASS all 5 cases + monotonic sweep (audit: node2b_boundary_gate)",
    "independent verification (3 checks)": "problem_state.json verification block (audit: node2b_independent_verification)",
    "capture delta-v baseline + Tsiolkovsky propellant fraction": "jovian_flyby_model.direct_capture_deltav / assisted_capture_deltav / propellant_mass_fraction (report 建模 section 2)",
    "constant provenance (mu_j, moon a/M/R)": "jupiter_flyby_params.json + Node 1.5 audit record (Level-3 IAU/JPL standard values; no live source reachable in this environment)"
}

audit_log.append_record(STATE, "node3_report_written", {
    "file": "program-design/runtime/report_2013A_jupiter_flyby.md",
    "note": "full report structure per report_structure_guide.md: abstract/conclusion-first, introduction, numbered assumptions, modeling, independent verification (3 checks), results table + figures, strengths/weaknesses, discussion"
})
json.dump(st, open(STATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("node 3 recorded; stage:", st["stage"])
