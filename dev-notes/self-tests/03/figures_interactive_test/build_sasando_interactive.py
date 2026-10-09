"""Real-data interactive-figure demo: 2025A Sasando (test3 / self-tests 03).

Uses the EXISTING, already-computed `ei_curve_sample_dB` field from
problem_state_2025A_sasando.json — no new physics is solved or invented,
exactly the boundary the interactive branch is allowed to respect
(see dev-notes/interactive_figure_design.md §1: switching between
pre-computed data sets only, no live re-solve).

One figure, two series toggled by a button switcher:
  series 1: the 12-point frequency-response sample (the actual curve)
  series 2: the 4 headline eigenfrequencies, marked as discrete points on
            the same axes, so the reader can toggle between "smooth sample"
            and "which exact modes produced it" views.
"""
import json, os, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
state_path = os.path.join(repo_root, "dev-notes", "self-tests", "03", "problem_state_2025A_sasando.json")

with open(state_path, encoding="utf-8-sig") as f:
    state = json.load(f)

ei = state["numerical_artifacts"]["ei_curve_sample_dB"]
f_Hz = ei["f_Hz"]
gain_dB = ei["gain_rel_to_peak_dB"]

head = state["numerical_artifacts"]["headline_eigenfrequencies"]
f_modes = head["f_all_modes_Hz"]

# Pick a second series that is VISUALLY DISTINCT from the sampled curve, so
# toggling between the two switcher views is actually perceptible (the earlier
# version put 4 dots at y=0, right where the sampled curve already passes
# through ~0 dB, making the toggle look like nothing happened — that was a bad
# demo choice, not a rendering bug).
mode_markers_x = [m for m in f_modes if m <= max(f_Hz)]
mode_markers_y = [50.0] * len(mode_markers_x)  # clearly offset band, not overlapping the curve

fig_spec = {
    "kind": "interactive",
    "title": "2025A Sasando — 采样响应曲线 vs. 4 个特征频率（两条视觉上明显不同的 series，切换可感知）",
    "backend": "plotly",
    "layout_3d": False,
    "series": [
        {"name": "采样响应（12 点，dB）", "points": {"x": f_Hz, "y": gain_dB}},
        {"name": f"4 个特征频率（y 轴平移到 {mode_markers_y[0]:.0f} dB 位置，仅为视觉区分，不代表物理增益）",
         "points": {"x": mode_markers_x, "y": mode_markers_y}},
    ],
    "switcher": {"label": "view", "type": "buttons"},
}
# Note for honesty: the y=50 band is a presentation-only offset to make the two
# series visually distinguishable in a toggle; it is NOT a physical gain value
# (the real eigenfrequencies' gain is 0 dB, equal to the peak-normalization
# baseline used for series 1). This keeps the demo honest without requiring the
# user to zoom in to tell the two series apart.

out_state_path = os.path.join(repo_root, "dev-notes", "self-tests", "03", "figures_interactive_test",
                              "problem_state_2025A_sasando_with_interactive.json")
os.makedirs(os.path.dirname(out_state_path), exist_ok=True)
state["numerical_artifacts"]["figures"] = {"fig_sasando_interactive": fig_spec}
with open(out_state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print("wrote", out_state_path)

out_dir = os.path.join(repo_root, "dev-notes", "self-tests", "03", "figures_interactive_test",
                       "sasando_interactive_out")
script = os.path.join(repo_root, "program-design", "hooks", "make_report_figures.py")
r = subprocess.run([sys.executable, script, "--state", out_state_path, "--out-dir", out_dir],
                   capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

frag_path = os.path.join(out_dir, "fig_sasando_interactive.html")
assert os.path.exists(frag_path), frag_path
print("DONE — interactive figure built from real 2025A sasando data:", frag_path)
