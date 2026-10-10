import sys, json, subprocess

sys.path.insert(0, r"E:\agh-test\program-design\hooks")

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

dim_specs = [
    ("GATE1", "e = 1 + r_p * v_rel^2 / mu_m",
     {"r_p": "length", "v_rel": "velocity", "mu_m": "m^3/s^2", "e": "dimensionless"}),
    ("GATE2", "delta = 2 * asin(1/e)",
     {"e": "dimensionless", "delta": "dimensionless"}),
    ("GATE3", "v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)",
     {"v_rel": "velocity", "v_moon": "velocity", "delta": "dimensionless", "v_out": "velocity"}),
    ("GATE4", "v_out = sqrt((v_moon + v_rel*cos(delta))^2 + (v_rel*sin(delta))^2)",
     {"v_moon": "velocity", "v_rel": "velocity", "delta": "dimensionless", "v_out": "velocity"}),
    ("GATE5", "v_rel2 = v_out_1 + v_moon_B",
     {"v_out_1": "velocity", "v_moon_B": "velocity", "v_rel2": "velocity"}),
    ("GATE6", "v_peri^2 = v_out^2 + 2*mu_j/a_target",
     {"v_out": "velocity", "mu_j": "m^3/s^2", "a_target": "length", "v_peri": "velocity"}),
]

results = []
all_pass = True
for gate_id, eq, dims in dim_specs:
    r = subprocess.run(
        [sys.executable, r"E:\agh-test\program-design\hooks\dimensional_gate.py",
         "--equation", eq, "--dims", json.dumps(dims)],
        capture_output=True, text=True,
    )
    verdict = "PASS" if r.returncode == 0 else "FAIL"
    if r.returncode != 0:
        all_pass = False
    results.append({"gate_id": gate_id, "equation": eq, "dims": dims, "verdict": verdict, "output": (r.stdout or r.stderr).strip()})
    print(f"{gate_id}: {verdict} :: {(r.stdout or r.stderr).strip()[:120]}")

st["dimensional_table"] = results
st["stage"] = "node_2b_modeling"
json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\nALL_PASS:", all_pass)
print("dimensional_table written to state file")
