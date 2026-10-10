import subprocess, sys, json
gate = r"E:\agh-test\program-design\hooks\dimensional_gate.py"

def run(equation, dims):
    r = subprocess.run([sys.executable, gate, "--equation", equation, "--dims", json.dumps(dims)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return {"raw_stdout": r.stdout, "raw_stderr": r.stderr, "rc": r.returncode}

# 1) Turning angle eccentricity relation: e = 1 + r_p*v_rel^2/mu  (check the r_p*v^2/mu term is dimensionless)
print("GATE 1: e = 1 + r_p*v_rel^2/mu")
print(json.dumps(run("e = 1 + r_p*v_rel^2/mu", {
    "e": "dimensionless", "r_p": "length", "v_rel": "velocity", "mu": "m^3/s^2"}), indent=1))

# 2) Exit speed squared relation (head-on kinematics): v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)
print("GATE 2: v_out^2 = v_rel^2 + v_moon^2 - 2*v_rel*v_moon*cos(delta)")
print(json.dumps(run("v_out**2 = v_rel**2 + v_moon**2 - 2*v_rel*v_moon*cos(delta)", {
    "v_out": "velocity", "v_rel": "velocity", "v_moon": "velocity", "delta": "dimensionless"}), indent=1))

# 3) Bound-orbit test expression: v_out^2 + 2*mu_j/r (must have dimensions of specific energy, i.e. velocity^2)
print("GATE 3: v_out^2 + 2*mu/r")
print(json.dumps(run("v_out**2 + 2*mu/r", {
    "v_out": "velocity", "mu": "m^3/s^2", "r": "length"}), indent=1))

# 4) v_moon^2 = mu_j/a
print("GATE 4: v_moon^2 = mu_j/a")
print(json.dumps(run("v_moon**2 = mu_j/a", {
    "v_moon": "velocity", "mu_j": "m^3/s^2", "a": "length"}), indent=1))
