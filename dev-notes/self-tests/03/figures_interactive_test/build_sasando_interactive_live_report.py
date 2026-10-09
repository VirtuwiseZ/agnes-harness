"""Render the full Node-4-style report page around the interactive_live sasando
figure, verifying the .html-fragment inlining path works for interactive_live
figures too (same code path as plain 'interactive' — no separate handling
needed, since both produce <figure_id>.html)."""
import json, os, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
state_path = os.path.join(here, "problem_state_2025A_sasando_with_interactive_live.json")
figures_dir = os.path.join(here, "sasando_live_out")

report_md_path = os.path.join(here, "report_sasando_interactive_live_demo.md")
with open(report_md_path, "w", encoding="utf-8") as f:
    f.write(
        "# 2025A 竹响器（Sasando）— 拖动 zeta 实时看曲线变化（interactive_live 演示）\n\n"
        "## 说明\n\n"
        "这张图用第 8 种 figure kind（`interactive_live`）：拖动下方的 zeta（阻尼比）"
        "滑块时，浏览器端会对这条 H(f) 闭式表达式（4 个阻尼洛伦兹峰的求和，跟 "
        "`problem_state.json` 里已算好的 `headline_eigenfrequencies` 同一套数学）"
        "重新求一遍 y 值，实时改变曲线形态 —— 这就是 GeoGebra 式\"调参数实时看图\"的效果，"
        "全程不需要服务器，不需要重新解任何方程（因为这里要调的 zeta 只影响峰的宽度/高度，"
        "不影响特征频率本身，是一个便宜的闭式重算，不是数值模型重解）。\n\n"
        "## 图（拖动滑块试试）\n\n"
        "{{figure: fig_sasando_live}}\n"
    )

trace_path = os.path.join(here, "trace_minimal.jsonl")
with open(trace_path, "w", encoding="utf-8") as f:
    f.write('{"type":"tool/call","toolName":"shell"}\n')

out_html = os.path.join(here, "research_report_sasando_interactive_live.html")
script = os.path.join(repo_root, "program-design", "hooks", "trace_visualizer.py")
r = subprocess.run([sys.executable, script, "--trace", trace_path, "--report", report_md_path,
                    "--state", state_path, "--figures-dir", figures_dir, "--out", out_html],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

content = open(out_html, encoding="utf-8").read()
assert "report-figure-interactive" in content, "interactive_live inlining marker not found"
assert "zeta" in content and "live-root" in content, "slider controls not found in final page"
print(f"OK: {out_html} ({len(content):,} bytes), interactive_live figure inlined with live sliders.")
print("DONE:", out_html)
