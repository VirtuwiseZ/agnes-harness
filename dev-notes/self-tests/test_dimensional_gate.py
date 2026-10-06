import os
import subprocess
import sys

# dimensional_gate.py lives in program-design/hooks/; run it by absolute path
# so this test works no matter where it is invoked from.
_GATE = os.path.join(os.path.dirname(__file__), "..", "..", "program-design", "hooks", "dimensional_gate.py")
_GATE = os.path.abspath(_GATE)

cases = [
    # (label, args_list_after_python, expected_rc)
    ("PASS-expected", ["--equation", "F = m*a",
     "--dims", '{"F": "force", "m": "mass", "a": "acceleration"}'], 0),
    ("FAIL-expected", ["--equation", "F = m",
     "--dims", '{"F": "force", "m": "mass"}'], 1),
    ("PASS-with-warning", ["--equation", "E = exp(-x/L)",
     "--dims", '{"E": "dimensionless", "x": "length", "L": "length"}'], 0),
    ("WARN-only (bad transcendental arg)", ["--equation", "y = sin(x)",
     "--dims", '{"y": "dimensionless", "x": "length"}'], 0),
    # --- new: extended alias coverage (the two that broke the 02 run, plus a few more) ---
    ("PASS-extended: area", ["--equation", "F = 0.5*rho*A*v*v",
     "--dims", '{"F": "force", "rho": "density", "A": "area", "v": "velocity"}'], 0),
    ("PASS-extended: specific_energy", ["--equation", "E = 0.5*m*u",
     "--dims", '{"E": "energy", "m": "mass", "u": "specific_energy"}'], 0),
    ("PASS-extended: momentum", ["--equation", "J = m*v",
     "--dims", '{"J": "momentum", "m": "mass", "v": "velocity"}'], 0),
    ("PASS-extended: viscosity", ["--equation", "tau = mu*dU/dy",
     "--dims", '{"tau": "pressure", "mu": "viscosity", "dU": "velocity", "dy": "length"}'], 0),
    # --- new: fallback — caller passes a concrete unit expression directly ---
    ("PASS-fallback: raw unit expr", ["--equation", "E = m*u",
     "--dims", '{"E": "J", "m": "kg", "u": "J/kg"}'], 0),
    ("ERROR-fallback: garbage key still errors cleanly",
     ["--equation", "E = m*u",
      "--dims", '{"E": "J", "m": "kg", "u": "not_a_unit_or_alias"}'], 2),
    # --- new: Derivative (ODE-form) handling, the real du/dx equation from the 02 run ---
    # u = v^2/2 (specific energy, L^2 T^-2), x = fallen distance (length, L)
    # du/dx should have dimension L T^-2, same as g_eff (acceleration, L T^-2)
    ("PASS-ODE: du/dx = g - k*u (function-form Derivative)",
     ["--expression", "Derivative(u(x), x) - g + (rho*CD*A/(2*m))*u",
      "--dims", '{"u": "specific_energy", "x": "length", "g": "acceleration",'
                 ' "rho": "density", "CD": "dimensionless", "A": "area", "m": "mass"}'], 0),
    ("PASS-ODE: du/dx = g (plain-Symbol Derivative)",
     ["--expression", "Derivative(u, x) - g",
      "--dims", '{"u": "specific_energy", "x": "length", "g": "acceleration"}'], 0),
    ("FAIL-ODE: du/dx = m (wrong: dimension should be L T^-2 but m is [mass])",
     ["--expression", "Derivative(u, x) - m",
      "--dims", '{"u": "specific_energy", "x": "length", "m": "mass"}'], 1),
]

failures = 0
for label, args, expected_rc in cases:
    r = subprocess.run(
        [sys.executable, _GATE] + args,
        capture_output=True, text=True,
    )
    ok = r.returncode == expected_rc
    marker = "PASS" if ok else "FAIL"
    if not ok:
        failures += 1
    print(f"=== {marker} {label} (rc={r.returncode}, expected {expected_rc}) ===")
    print(r.stdout)
    if not ok:
        print(r.stderr)
        print("UNEXPECTED EXIT CODE")
    print()

if failures:
    print(f"{failures}/{len(cases)} case(s) FAILED")
    sys.exit(1)
print(f"all {len(cases)} cases passed")
