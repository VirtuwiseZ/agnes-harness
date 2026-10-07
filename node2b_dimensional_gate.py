"""Node 2b step 1: run the dimensional gate on this problem's governing ODE.

Governing equations (2D projectile motion with quadratic air drag + wind),
time t as independent variable:

   dvx/dt = -(rho(z) * CD * A / (2m)) * vx * |v| * (1 - ... )  -- NOT this form;
   the correct quadratic-drag form (drag opposes instantaneous velocity relative
   to the air, and the air itself moves with the wind) is:

   u = vx - u_wind   (x-component of projectile velocity RELATIVE to the air)
   w = vz - 0        (z-component of projectile velocity relative to the air;
                     wind is assumed purely horizontal, so no vertical wind)
   vrel = sqrt(u^2 + w^2)
   F_drag_x = -(1/2) * rho(z) * CD * A * vrel * u
   F_drag_z = -(1/2) * rho(z) * CD * A * vrel * w

   Derivative(vx, t) = F_drag_x / m
   Derivative(vz, t) = -g + F_drag_z / m

   d(x)/dt = vx
   d(z)/dt = vz

where vx, vz are the projectile's velocity components (velocity dimension),
x, z are position coordinates (length), g is gravity (acceleration),
rho(z) is the local air density (density), CD is the (dimensionless) drag
coefficient, A is cross-sectional area (area), m is mass, u_wind is the
wind speed (velocity).

The dimensional gate checks the two ODE lines (the acceleration-level ones,
since those are where every term must carry acceleration's dimension); the
two position-velocity lines are trivially dimensionally sound (d(length)/
d(time) = velocity).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
gate = os.path.join(HERE, "program-design", "hooks", "dimensional_gate.py")

cases = [
    (
        "x-acceleration ODE (with horizontal wind)",
        "Derivative(vx, t) = -K*rho*A*vrel*ux/m",
        json.dumps({
            "vx": "velocity", "t": "time", "K": "dimensionless",
            "rho": "density", "A": "area", "vrel": "velocity",
            "ux": "velocity", "m": "mass",
        }),
    ),
    (
        "z-acceleration ODE (no vertical wind)",
        "Derivative(vz, t) = -g - K*rho*A*vrel*wz/m",
        json.dumps({
            "vz": "velocity", "t": "time", "g": "acceleration",
            "K": "dimensionless", "rho": "density", "A": "area",
            "vrel": "velocity", "wz": "velocity", "m": "mass",
        }),
    ),
    (
        "x-position ODE",
        "Derivative(x, t) = vx",
        json.dumps({"x": "length", "t": "time", "vx": "velocity"}),
    ),
    (
        "z-position ODE",
        "Derivative(z, t) = vz",
        json.dumps({"z": "length", "t": "time", "vz": "velocity"}),
    ),
]

results = []
for label, equation, dims in cases:
    r = subprocess.run(
        [sys.executable, gate, "--equation", equation, "--dims", dims],
        capture_output=True, text=True,
    )
    out = json.loads(r.stdout)
    results.append({"case": label, "equation": equation, "returncode": r.returncode, "result": out})
    print(f"\n=== {label} ===\n{equation}\nrc={r.returncode}: {json.dumps(out)}")

sys.path.insert(0, os.path.join(HERE, "program-design", "hooks"))
import audit_log
state_path = os.path.abspath(os.path.join(HERE, "program-design", "runtime", "problem_state_2025B_artillery.json"))
audit_log.append_record(
    state_path=state_path,
    source="dimensional_gate_run",
    args={"all_results": results},
)

all_pass = all(res["result"].get("verdict") == "PASS" and res["returncode"] == 0 for res in results)
print("\nALL PASS" if all_pass else "\nNOT ALL PASS - see above")
sys.exit(0 if all_pass else 1)
