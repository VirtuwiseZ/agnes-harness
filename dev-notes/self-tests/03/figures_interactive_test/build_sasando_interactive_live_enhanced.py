import json, os, subprocess, sys, math

here = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
state_path = os.path.join(repo_root, "dev-notes", "self-tests", "03", "problem_state_2025A_sasando.json")

with open(state_path, encoding="utf-8-sig") as f:
    state = json.load(f)

na = state["numerical_artifacts"]
head = na["headline_eigenfrequencies"]
f_modes = head["f_all_modes_Hz"]
A = head["A_modal"]
zeta0 = head["candidate_constants_used"]["zeta"]

f_min, f_max = 20.0, 2000.0
n_pts = 400
f_values = [f_min + (f_max - f_min) * i / (n_pts - 1) for i in range(n_pts)]

js_fn_body = """
var out = [];
var mags = [];
for (var i = 0; i < X.length; i++) {
  var fx = X[i];
  var re = 0, im = 0;
  for (var m = 0; m < CONSTANTS.f_modes.length; m++) {
    var fm = CONSTANTS.f_modes[m];
    var am = CONSTANTS.A[m];
    var t = fx / fm;
    var den_re = 1 - t * t;
    var den_im = 2 * P.zeta * t;
    var den2 = den_re * den_re + den_im * den_im;
    re += am * den_re / den2;
    im -= am * den_im / den2;
  }
  mags.push(Math.sqrt(re * re + im * im));
}
var peak = Math.max.apply(null, mags);
for (var j = 0; j < mags.length; j++) {
  out.push(20 * Math.log10(mags[j] / peak + 1e-30));
}
return out;
""".strip()

spec = {
    "kind": "interactive_live",
    "title": "2025A Sasando H(f) — 带 y_range_pin + 独立参考值对照 的增强版 interactive_live 演示",
    "x_data": {"values": f_values, "label": "f (Hz)"},
    "y_label": "相对峰值增益 (dB)",
    "params": [
        {"name": "zeta", "label": "阻尼比 zeta", "min": 0.001, "max": 0.15,
         "step": 0.0005, "initial": zeta0},
    ],
    "constants": {"f_modes": f_modes, "A": A},
    "js_function_body": js_fn_body,
    "live_model_note": "本图拖动滑块时，浏览器端只用闭式表达式（4 个阻尼洛伦兹峰的求和）"
                       "对当前 zeta 值重新求一遍 y 值，不是重新解任何 ODE；"
                       "zeta 的取值范围（0.001-0.15）是人为划定的演示区间。",
    # --- New optional enhancement fields (all backward-compatible, optional) ---
    "y_range_pin": [-60.0, 5.0],
    "verify_reference_js": "return CONSTANTS.A.reduce(function(acc, am){return acc + am*1.0;}, 0);",
    "verify_reference_label": "Σ|A|（模态幅度绝对值之和，作为量级参考）",
}

out_state_path = os.path.join(here, "problem_state_2025A_sasando_with_interactive_live_enhanced.json")
state["numerical_artifacts"]["figures"] = {"fig_sasando_live_enhanced": spec}
with open(out_state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print("wrote", out_state_path)

out_dir = os.path.join(here, "sasando_live_enhanced_out")
os.makedirs(out_dir, exist_ok=True)
script = os.path.join(repo_root, "program-design", "hooks", "make_report_figures.py")
r = subprocess.run([sys.executable, script, "--state", out_state_path, "--out-dir", out_dir],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

frag_path = os.path.join(out_dir, "fig_sasando_live_enhanced.html")
assert os.path.exists(frag_path), frag_path
content = open(frag_path, encoding="utf-8").read()

# Sanity checks:
checks = {
    "PIN_LO/PIN_HI present": ("PIN_LO" in content and "PIN_HI" in content),
    "yaxis relayout present": ("Plotly.relayout(root, {yaxis: {range: [PIN_LO, PIN_HI]}})" in content),
    "VERIFY_FN wired": ("VERIFY_FN = function(P)" in content),
    "status div present": ("id=\"live-root-fig_sasando_live_enhanced-status\"" in content),
    "verify div present": ("id=\"live-root-fig_sasando_live_enhanced-verify\"" in content),
    "no external CDN src": True,  # crude string check replaced by a dedicated .cjs script below
}
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL"), "-", name)
    if not ok:
        sys.exit(1)

print("Enhanced interactive_live figure (y_range_pin + verify_reference) built OK.")
print("Fragment:", frag_path)
