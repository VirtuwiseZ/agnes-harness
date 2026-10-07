"""Wrapper to run boundary_gate.py with the correct module path so
artillery_model (in program-design/runtime/) is importable."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
runtime_dir = os.path.join(HERE, "program-design", "runtime")
hooks_dir = os.path.join(HERE, "program-design", "hooks")
spec = os.path.join(runtime_dir, "boundary_spec_artillery.json")

env = dict(os.environ)
existing_pp = env.get("PYTHONPATH", "")
env["PYTHONPATH"] = runtime_dir + ((";" + existing_pp) if existing_pp else "")

r = subprocess.run([sys.executable, os.path.join(hooks_dir, "boundary_gate.py"), "--spec", spec],
                   capture_output=True, text=True, env=env, cwd=runtime_dir)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr, file=sys.stderr)
sys.exit(r.returncode)
