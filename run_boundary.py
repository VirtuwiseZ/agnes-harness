import subprocess, sys, os
env = dict(os.environ)
env["PYTHONPATH"] = "E:\\agh-test"
r = subprocess.run([sys.executable, "E:\\agh-test\\program-design\\hooks\\boundary_gate.py",
                    "--spec", "E:\\agh-test\\boundary_spec.json"],
                   capture_output=True, text=True, env=env)
print(r.stdout)
print(r.stderr)
print("exit code:", r.returncode)
