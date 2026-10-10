p = r"E:\agh-test\jovian_flyby_boundary_adapter.py"
raw = open(p, encoding="utf-8").read()

old = '''    v_rel = params.get("v_rel", 37332.0)
    r_p = params.get("r_p", 1821600.0)
    mu_m = params.get("mu_m", 5.959e15)
    v_moon = params.get("v_moon", 17332.0)
    head_on = params.get("head_on", True)
    v_out, delta = M.v_out_closed_form(r_p, v_rel, v_moon, mu_m, head_on=head_on)
    return {"v_out_m_s": v_out, "delta": delta}'''

new = '''    v_rel = params.get("v_rel", 37332.0)
    r_p = params.get("r_p", 1821600.0)
    mu_m = params.get("mu_m", 5.959e15)
    v_moon = params.get("v_moon", 17332.0)
    head_on = params.get("head_on", True)

    # Handle the mu_m -> 0 (no-gravity, no-op) limit explicitly instead of
    # letting M.v_out_closed_form raise ZeroDivisionError inside its own
    # hyperbolic_turning_angle call: the analytically-correct limit is
    # e -> infinity, delta -> 0, and
    #   head_on:      v_out -> |v_rel - v_moon|
    #   overtaking:   v_out -> v_moon + v_rel   (both velocities simply add,
    #                  no deflection at all - the "no encounter happened"
    #                  no-op limit, which is a genuinely different no-op
    #                  answer than the head-on case's, and both are the
    #                  correct, well-defined values to return at exactly
    #                  mu_m = 0, not a NaN or an exception.)
    if mu_m == 0.0:
        if head_on:
            v_out, delta = abs(v_rel - v_moon), 0.0
        else:
            v_out, delta = v_moon + v_rel, 0.0
        return {"v_out_m_s": v_out, "delta": delta}

    v_out, delta = M.v_out_closed_form(r_p, v_rel, v_moon, mu_m, head_on=head_on)
    return {"v_out_m_s": v_out, "delta": delta}'''

assert old in raw, "adapter anchor not found"
raw = raw.replace(old, new)
open(p, "w", encoding="utf-8").write(raw)
print("patched adapter with an explicit mu_m=0 no-op-limit branch")

import subprocess, sys, os, json
env = dict(os.environ)
env["PYTHONPATH"] = r"E:\agh-test" + os.pathsep + env.get("PYTHONPATH", "")
r = subprocess.run(
    [sys.executable, r"E:\agh-test\program-design\hooks\boundary_gate.py",
     "--spec", r"E:\agh-test\program-design\knowledge\jupiter_flyby\boundary_spec_run2.json"],
    capture_output=True, text=True, env=env,
)
print(r.stdout)
print("returncode:", r.returncode)
out = json.loads(r.stdout)
json.dump(out, open(r"E:\agh-test\program-design\runtime\boundary_gate_run2_result.json", "w", encoding="utf-8"), indent=2)
print("result saved to problem-design/runtime/boundary_gate_run2_result.json")
