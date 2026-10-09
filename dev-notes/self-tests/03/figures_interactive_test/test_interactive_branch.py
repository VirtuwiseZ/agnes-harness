import json, subprocess, sys, os, tempfile, re

base = os.path.dirname(os.path.abspath(__file__))  # .../dev-notes/self-tests/03/figures_interactive_test/
repo_root = os.path.abspath(os.path.join(base, "..", "..", "..", ".."))
state_path = os.path.join(repo_root, "dev-notes", "self-tests", "03", "problem_state_2025B_artillery.json")
assert os.path.exists(state_path), f"state_path not found: {state_path}"
with open(state_path, encoding="utf-8-sig") as f:
    state = json.load(f)

# Build one interactive figure from real 2025B data: switch between 3 of the
# 7 v0 sweep points (already computed by boundary_gate, not re-solved).
sweep_v = state["numerical_artifacts"]["boundary_gate"]["monotonicity_sweep_v0"]
sweep = list(zip(sweep_v["values"], sweep_v["miss_m"]))
series = []
for i, row in enumerate(sweep[::2][:3], start=1):
    x = [row[0] for _ in range(1)]
    # x/y for a simple "distance-miss" marker line; z omitted -> 2D
    y = [row[1]]
    series.append({"name": f"v0={row[0]} m/s", "points": {"x": [i], "y": [row[1]]}})
# simpler: one series with all 7 points as a curve, plus 3 single-point
# "selected" series toggled by the switcher, so the demo shows both a base
# curve and switchable markers without fabricating new physics.
state["numerical_artifacts"].setdefault("figures", {})
state["numerical_artifacts"]["figures"]["fig_interactive_demo"] = {
    "kind": "interactive",
    "title": "2025B v0 monotonicity sweep — interactive (synthetic demo, static export, no live re-solve)",
    "backend": "plotly",
    "layout_3d": False,
    "series": [
        {"name": "full sweep", "points": {"x": [i+1 for i in range(len(sweep))], "y": [row[1] for row in sweep]}},
    ] + [
        {"name": f"v0={row[0]}", "points": {"x": [idx+1], "y": [row[1]]}}
        for idx, row in enumerate(sweep[::2][:3])
    ],
    "switcher": {"label": "v0", "type": "buttons"},
}
tmp = tempfile.mkdtemp()
state_mod_path = os.path.join(tmp, "problem_state_test.json")
with open(state_mod_path, "w", encoding="utf-8") as f:
    json.dump(state, f)

out_dir = os.path.join(tmp, "figs")
r = subprocess.run([sys.executable, os.path.join(repo_root, "program-design", "hooks", "make_report_figures.py"),
                    "--state", state_mod_path, "--out-dir", out_dir],
                   capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

# Confirm the .html fragment exists and has no external CDN reference
frag = os.path.join(out_dir, "fig_interactive_demo.html")
assert os.path.exists(frag), f"interactive fragment not written: {frag}"
content = open(frag, encoding="utf-8").read()
assert not re.search(r'src="https?://', content), "external JS reference found — not self-contained!"
print(f"OK: {os.path.basename(frag)} is self-contained ({len(content):,} bytes)")
print("DONE — interactive branch end-to-end test passed via the real make_report_figures.py")
