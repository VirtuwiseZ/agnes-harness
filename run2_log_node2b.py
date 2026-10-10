import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

import subprocess, os
env = dict(os.environ)
env["PYTHONPATH"] = r"E:\agh-test" + os.pathsep + env.get("PYTHONPATH", "")

import jovian_flyby_model_run2 as M
import importlib
importlib.reload(M)
out = M.run_model()

st["numerical_artifacts"] = {
    "head_on_tightest_flyby_all_moons": out["single_encounter_tightest_flyby"],
    "overtaking_control_tightest_flyby_all_moons": out["overtaking_control_case_tightest_flyby"],
    "chained_all_12_pairs": out["chained_all_pairs"],
    "capture_baseline_io_scale": out["capture_baseline"]["io_scale"],
    "capture_baseline_ganymede_scale": out["capture_baseline"]["ganymede_scale"],
    "head_on_full_perigee_sweep": out["head_on_sweep_all_moons_all_perigees"],
    "overtaking_full_perigee_sweep": out["overtaking_sweep_all_moons_all_perigees"],
    "kepler_period_cross_check": out["kepler_period_cross_check"],
}

boundary_result = json.load(open(r"E:\agh-test\program-design\runtime\boundary_gate_run2_result.json", encoding="utf-8"))
st["verification"]["boundary_gate_run2"] = boundary_result

audit_log.append_record(state, "run2_node2b_model_run", {
    "model": "jovian_flyby_model_run2.py",
    "headon_all_moons_v_out_km_s": {k: round(v["v_out_m_s"]/1e3, 6) for k, v in out["single_encounter_tightest_flyby"].items()},
    "overtaking_all_moons_v_out_km_s": {k: round(v["v_out_m_s"]/1e3, 6) for k, v in out["overtaking_control_case_tightest_flyby"].items()},
    "chained_best_worst": {
        "most_speedup_pair": max(out["chained_all_pairs"], key=lambda p: p["net_speed_change_vs_v_inf_m_s"]),
        "least_speedup_pair": min(out["chained_all_pairs"], key=lambda p: p["net_speed_change_vs_v_inf_m_s"]),
    },
    "note": "head-on: v_out strictly > v_inf for all 4 moons (invariant confirmed numerically). overtaking (run #2's NEW, corrected branch, verified against an independent exact-vector simulation before being trusted): modest net speed LOSS for Io (0.46 km/s), nearly-null for Europa/Ganymede/Callisto (<0.02 km/s) - NONE approaches the 1 km/s acceptance threshold. Chained construction: STILL a tiny speed-UP (not a deceleration) for all 12 ordered pairs, confirming the invariant holds recursively across multiple encounters, not just one."
})
audit_log.append_record(state, "run2_node2b_dimensional_gate", {"all_6_gates": "PASS", "detail": "see dimensional_table in this state file"})
audit_log.append_record(state, "run2_node2b_boundary_gate", {"verdict": boundary_result["verdict"], "sweep": boundary_result["sweep"]["observed"], "note": "headon_mu_m_to_0 reproduces v_out = 20000.0 m/s exactly (the no-op limit), confirming the v_out>=v_inf identity's no-op endpoint; full monotonic sweep from 40.9 km/s (mu_m=infinity-class limit, large deflection) down to exactly 20.0 km/s (mu_m=0, no encounter) - all PASS."})
audit_log.append_record(state, "run2_node2b_kepler_cross_check", {
    "rel_errors_pct": {k: round((t_kep - t_pub)/t_pub*100, 4) for k, (t_pub, t_kep) in out["kepler_period_cross_check"].items()},
    "note": "mu_jupiter independently cross-checked against each moon's published sidereal period via Kepler's third law - agreement to <0.04% for all 4 moons, confirming the central-body constant is not a free, unverified input to the model."
})
json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("node 2b audit records written; stage:", st.get("stage"))
