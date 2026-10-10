import sys, json, os
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

# Log F1's numbers explicitly so the traceability badge can point at them,
# not just at "the figure file".
sys.path.insert(0, r"E:\agh-test")
import jovian_flyby_model_run2 as M
import importlib
importlib.reload(M)
import numpy as np

r_factors = np.logspace(0.0, np.log10(50.0), 40)
f1_data = {}
for name in M._moon_names():
    deltas = [M.single_encounter_all_moons("head_on", r_p_factor=f)[name]["delta_deg"] for f in r_factors]
    f1_data[name] = {"r_factors": r_factors.tolist(), "delta_deg": deltas,
                     "delta_range": [min(deltas), max(deltas)]}

fig2_grid_data = {}
for geom in ("head_on", "overtaking"):
    r_f = np.logspace(0.0, np.log10(50.0), 30)
    orbit = "io_scale"
    base_dv = M.direct_capture_delta_v(M.CAPTURE_ORBITS[orbit]["a_m"])
    grid = {}
    for name in M._moon_names():
        row = []
        for f in r_f:
            res = M.single_encounter_all_moons(geom, r_p_factor=f)[name]
            v_out = res["v_out_m_s"]
            v_peri = np.sqrt(v_out**2 + 2*M.MU_J / M.CAPTURE_ORBITS[orbit]["a_m"])
            v_circ = np.sqrt(M.MU_J / M.CAPTURE_ORBITS[orbit]["a_m"])
            saving = (M.propellant_fraction(base_dv) - M.propellant_fraction(v_peri - v_circ)) * 100
            row.append(saving)
        grid[name] = {"saving_pct": row, "min": min(row), "max": max(row)}
    fig2_grid_data[geom] = grid

chained = M.best_chained_pair(1.0, 1.0)
for pair in chained:
    pair["net_speed_change_km_s"] = round(pair["net_speed_change_vs_v_inf_m_s"] / 1e3, 6)

st["numerical_artifacts"]["f1_delta_data"] = f1_data
st["numerical_artifacts"]["f2_grid_data"] = fig2_grid_data
st["numerical_artifacts"]["f3_chained_numbers"] = chained
st["numerical_artifacts"]["figures_run2"] = {
    "F1": "figures_2013A_jupiter_flyby_run2/F1_delta_vs_perigee_head_on.png",
    "F2a": "figures_2013A_jupiter_flyby_run2/F2a_saving_surface_head_on.png",
    "F2b": "figures_2013A_jupiter_flyby_run2/F2b_saving_surface_overtaking.png",
    "F3": "figures_2013A_jupiter_flyby_run2/F3_chained_staircase.png",
}

out = audit_log.append_record(state, "run2_node27_figures", {
    "figure_design_principle": "No figure may have a near-blank curve/panel: (F1) switched from plotting v_out (provably pinned to ~20 km/s, the exact near-blank failure mode of run #1) to plotting delta - the quantity that GENUINELY varies across 4 decades; (F2a/F2b) genuine 2D parameter surfaces, not 1D lines; (F3) the chained construction's staircase plot, a genuinely new quantity with an explicit acceptance-threshold line drawn so 'does any pairing clear the bar' is answerable by looking, not by reading a table.",
    "f1_delta_ranges_deg": {k: v["delta_range"] for k, v in f1_data.items()},
    "f2_min_max_saving_pct": {geom: {k: [v["min"], v["max"]] for k, v in g.items()} for geom, g in fig2_grid_data.items()},
    "f3_chained_all_12_pairs_net_km_s": [round(p["net_speed_change_vs_v_inf_m_s"]/1e3, 6) for p in chained],
})
print("F1 delta ranges:", {k: v["delta_range"] for k, v in f1_data.items()})
print("F2 head_on min/max saving %:", {k: [v["min"], v["max"]] for k, v in fig2_grid_data["head_on"].items()})
print("F2 overtaking min/max saving %:", {k: [v["min"], v["max"]] for k, v in fig2_grid_data["overtaking"].items()})
print("F3 all-12-pairs net change (km/s):", [round(p["net_speed_change_vs_v_inf_m_s"]/1e3, 6) for p in chained])
print("recorded:", out["artifact_id"])
json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
