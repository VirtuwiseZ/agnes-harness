import subprocess, sys

# Run the gate with PYTHONPATH including E:\agh-test so the adapter module is
# importable, since the gate's importlib.import_module() won't see it otherwise.
import os
env = dict(os.environ)
env["PYTHONPATH"] = r"E:\agh-test" + os.pathsep + env.get("PYTHONPATH", "")
r = subprocess.run(
    [sys.executable, r"E:\agh-test\program-design\hooks\boundary_gate.py",
     "--spec", r"E:\agh-test\program-design\knowledge\jupiter_flyby\boundary_spec_run2.json"],
    capture_output=True, text=True, env=env,
)
print("stdout:", r.stdout)
print("stderr:", r.stderr)
print("returncode:", r.returncode)
