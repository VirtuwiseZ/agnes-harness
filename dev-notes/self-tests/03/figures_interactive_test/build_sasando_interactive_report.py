"""Render a minimal Node-4-style HTML page around the real 2025A sasando
interactive figure, using the real trace_visualizer.py inlining path —
not a standalone fragment — so the result is exactly what the pipeline
would produce in a real run."""
import json, os, subprocess, sys, re

here = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
state_path = os.path.join(here, "problem_state_2025A_sasando_with_interactive.json")
figures_dir = os.path.join(here, "sasando_interactive_out")

report_md_path = os.path.join(here, "report_sasando_interactive_demo.md")
with open(report_md_path, "w", encoding="utf-8") as f:
    f.write(
        "# 2025A 竹响器（Sasando）交互图演示\n\n"
        "## 说明\n\n"
        "这张图用的是 2025A 题目**已经算好的**真实数据（`problem_state.json` 的 "
        "`ei_curve_sample_dB` 12 个采样点 + `headline_eigenfrequencies` 4 个特征频率），"
        "没有重新解任何方程，只是把这两组已有数字做成可切换查看的交互图，"
        "验证第 7 种 figure kind（`interactive`）端到端跑通。\n\n"
        "## 图\n\n"
        "{{figure: fig_sasando_interactive}}\n"
    )

trace_path = os.path.join(here, "trace_minimal.jsonl")
with open(trace_path, "w", encoding="utf-8") as f:
    f.write('{"type":"tool/call","toolName":"shell"}\n')

out_html = os.path.join(here, "research_report_sasando_interactive.html")
script = os.path.join(repo_root, "program-design", "hooks", "trace_visualizer.py")
r = subprocess.run([sys.executable, script, "--trace", trace_path, "--report", report_md_path,
                    "--state", state_path, "--figures-dir", figures_dir, "--out", out_html],
                   capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

content = open(out_html, encoding="utf-8").read()
assert "report-figure-interactive" in content, "interactive inlining marker not found"
assert "fig_sasando_interactive" not in re.search(r"report-figure-missing[^<]*fig_sasando_interactive", content).group(0) if re.search(r"report-figure-missing[^<]*fig_sasando_interactive", content) else True
print(f"OK: {out_html} ({len(content):,} bytes), interactive figure inlined, not a missing-box.")
print("DONE:", out_html)
