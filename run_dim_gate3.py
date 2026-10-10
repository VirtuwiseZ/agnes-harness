import subprocess, sys, json
gate = r"E:\agh-test\program-design\hooks\dimensional_gate.py"

def run_equation(equation, dims):
    r = subprocess.run([sys.executable, gate, "--equation", equation, "--dims", json.dumps(dims)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return {"raw_stdout": r.stdout, "raw_stderr": r.stderr, "rc": r.returncode}

print("GATE 3 (fixed): E_spec = v_out**2 + 2*mu/r, declared as specific-energy dimension")
out = run_equation("E_spec = v_out**2 + 2*mu/r",
                   {"E_spec": "specific_energy", "v_out": "velocity", "mu": "m^3/s^2", "r": "length"})
print(json.dumps(out, indent=1))
