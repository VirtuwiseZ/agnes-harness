import subprocess, sys

cases = [
    ("PASS-expected", "--equation", "F = m*a",
     '{"F": "force", "m": "mass", "a": "acceleration"}', 0),
    ("FAIL-expected", "--equation", "F = m",
     '{"F": "force", "m": "mass"}', 1),
    ("PASS-with-warning", "--equation", "E = exp(-x/L)",
     '{"E": "dimensionless", "x": "length", "L": "length"}', 0),
    ("WARN-only (bad transcendental arg)", "--equation", "y = sin(x)",
     '{"y": "dimensionless", "x": "length"}', 0),
]

for label, eq_flag, eq, dims, expected_rc in cases:
    r = subprocess.run(
        [sys.executable, "dimensional_gate.py", eq_flag, eq, "--dims", dims],
        capture_output=True, text=True,
    )
    print(f"=== {label} (rc={r.returncode}, expected {expected_rc}) ===")
    print(r.stdout)
    if r.returncode != expected_rc:
        print(r.stderr)
        print("UNEXPECTED EXIT CODE")
    print()
