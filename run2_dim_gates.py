import sys, json, subprocess, os

sys.path.insert(0, r"E:\agh-test\program-design\hooks")

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

# --- Dimensional gate, applied to THIS RUN's three governing equations (same
# hook as run #1, but a genuinely fresh set of equation/dims pairs, since the
# overtaking closed form and the chained-construction composition are new).
dim_specs = [
    {
        "equation": "e = 1 + r_p * v_rel^2 / mu_m",
        "dims": {"r_p": "length", "v_rel": "velocity", "mu_m": "m^3/s^2", "e": "dimensionless"},
    },
    {
        "equation": "delta = 2 * asin(1/e)",
        "dims": {"e": "dimensionless", "delta": "dimensionless (radians, treated as a pure number in this model)"},
    },
    {
        "equation": "v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)",
        "dims": {"v_rel": "velocity", "v_moon": "velocity", "delta": "dimensionless (argument of cos must be a pure angle/radians, already verified dimensionless via e)"},
    },
    {
        "equation": "v_out = sqrt((v_moon + v_rel*cos(delta))^2 + (v_rel*sin(delta))^2)   [overtaking branch, run #2]",
        "dims": {"v_moon": "velocity", "v_rel": "velocity", "delta": "dimensionless"},
    },
    {
        "equation": "chained: v_out_2 = sqrt((v_moon_B + v_rel2*cos(delta_2))^2 + (v_rel2*sin(delta_2))^2),  v_rel2 = v_out_1 + v_moon_B (anti-parallel closing, encounter 2)",
        "dims": {"v_out_1": "velocity", "v_moon_B": "velocity", "delta_2": "dimensionless"},
    },
    {
        "equation": "v_peri^2 = v_out^2 + 2*mu_j/a_target ;  v_circ^2 = mu_j/a_target ;  delta_v_capture = v_peri - v_circ",
        "dims": {"v_out": "velocity", "mu_j": "m^3/s^2", "a_target": "length", "v_peri": "velocity", "v_circ": "velocity"},
    },
]

results = []
for i, spec in enumerate(dim_specs, 1):
    r = subprocess.run(
        [sys.executable, r"E:\agh-test\program-design\hooks\dimensional_gate.py",
         "--equation", spec["equation"], "--dims", json.dumps(spec["dims"])],
        capture_output=True, text=True,
    )
    results.append({"gate": f"GATE{i}", "equation": spec["equation"], "returncode": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()})
    print(f"GATE{i}: {r.returncode} :: {r.stdout.strip() or r.stderr.strip()}")

st["dimensional_table"] = {f"GATE{i}": {"equation": s["equation"], "dims": s["dims"], "gate_stdout": s["stdout"]} for i, s in zip(range(1, 7), results)}
json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("dimensional table written to state file")
