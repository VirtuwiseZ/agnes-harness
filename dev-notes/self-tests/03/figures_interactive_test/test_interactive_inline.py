import os, sys, re, subprocess, tempfile, json

repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
base = os.path.join(repo_root, "dev-notes")
tmp = tempfile.mkdtemp()
state_path = os.path.join(repo_root, "dev-notes", "self-tests", "03", "problem_state_2025B_artillery.json")
assert os.path.exists(state_path), f"state_path not found: {state_path}"
with open(state_path, encoding="utf-8-sig") as f:
    state = json.load(f)

sweep_v = state["numerical_artifacts"]["boundary_gate"]["monotonicity_sweep_v0"]
sweep = list(zip(sweep_v["values"], sweep_v["miss_m"]))
state["numerical_artifacts"].setdefault("figures", {})
state["numerical_artifacts"]["figures"]["fig_interactive_demo"] = {
    "kind": "interactive", "backend": "plotly", "layout_3d": False,
    "title": "2025B v0 sweep (interactive demo)",
    "series": [
        {"name": "full sweep", "points": {"x": [i+1 for i in range(len(sweep))], "y": [row[1] for row in sweep]}},
    ] + [{"name": f"v0={row[0]}", "points": {"x": [idx+1], "y": [row[1]]}} for idx, row in enumerate(sweep[::2][:2])],
    "switcher": {"label": "v0", "type": "buttons"},
}
state_mod = os.path.join(tmp, "problem_state_test.json")
json.dump(state, open(state_mod, "w", encoding="utf-8"))

out_dir = os.path.join(tmp, "figs")
r = subprocess.run([sys.executable, os.path.join(repo_root, "program-design", "hooks", "make_report_figures.py"),
                    "--state", state_mod, "--out-dir", out_dir], capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout, r.stderr); sys.exit(1)

# Minimal report md + a minimal trace jsonl so trace_visualizer.py's
# --report path works without needing a real AGH session trace file.
report_md = os.path.join(tmp, "report_test.md")
open(report_md, "w", encoding="utf-8").write(
    "# 测试汇报\n\n## 演示段\n\n{{figure: fig_interactive_demo}}\n\n这是引用交互图占位符的段落。\n")
trace_jsonl = os.path.join(tmp, "trace.jsonl")
open(trace_jsonl, "w", encoding="utf-8").write('{"type":"tool/call","toolName":"shell"}\n')

out_html = os.path.join(tmp, "out_report.html")
script = os.path.join(repo_root, "program-design", "hooks", "trace_visualizer.py")
r2 = subprocess.run([sys.executable, script, "--trace", trace_jsonl, "--report", report_md,
                     "--state", state_mod, "--figures-dir", out_dir, "--out", out_html],
                    capture_output=True, text=True)
print(r2.stdout)
if r2.returncode != 0:
    print(r2.stderr); sys.exit(1)

content = open(out_html, encoding="utf-8").read()
if "report-figure-missing" in content and "fig_interactive_demo" in content:
    m = re.search(r"report-figure-missing[^<]*<code>fig_interactive_demo</code>[^<]*", content)
    print("MISSING-BOX HIT:", m.group(0) if m else "n/a")
    print("=> trace_visualizer did NOT find the .html fragment — check figures-dir wiring")
    sys.exit(1)
if "report-figure-interactive" in content:
    print(f"OK: interactive figure inlined into {out_html} ({len(content):,} bytes total page)")
    print("DONE — trace_visualizer.py .html-fragment inlining path verified")
else:
    print("WARN: 'report-figure-interactive' marker not found — check whether the placeholder was even reached")
    print(content[-2000:])
