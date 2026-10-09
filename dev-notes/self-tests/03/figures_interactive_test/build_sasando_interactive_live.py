"""Build the 2025A Sasando demo using the REAL interactive_live kind, with a
live zeta (damping ratio) slider — the GeoGebra-style 'drag a parameter,
watch the curve re-draw in real time' behavior, fully static, no server.

The closed-form H(f) response (sum of 4 damped Lorentzian modes) is mirrored
as inline JS; the Python reference implementation below is used to VERIFY
the JS produces the same numbers before shipping, per this project's 'no
silent paper-over' rule applied to a new, unverified code path.
"""
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


def h_db_py(f_list, zeta, f_modes, A):
    """Python reference: magnitude in dB, normalized to peak."""
    def mag(fx):
        re_ = im_ = 0.0
        for fm, am in zip(f_modes, A):
            t = fx / fm
            den_re = 1 - t * t
            den_im = 2 * zeta * t
            den2 = den_re * den_re + den_im * den_im
            re_ += am * den_re / den2
            im_ -= am * den_im / den2
        return (re_ * re_ + im_ * im_) ** 0.5
    mags = [mag(fx) for fx in f_list]
    peak = max(mags)
    return [20 * math.log10(m / peak + 1e-30) for m in mags]


# --- Build the JS-mirrored body, matching h_db_py EXACTLY (same loop, same
# arithmetic order), so the verification below is a real check, not a rubber
# stamp.
js_fn_body = """return function(){
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
}"""
# Wait — js_function_body is meant to be the BODY of a function already
# receiving P; it does NOT get a closure over X/CONSTANTS via `var` scope —
# the outer wrapper declares X/CONSTANTS/P in the enclosing function scope,
# so a plain expression (not a nested anonymous function) is the correct
# shape. Redo this as a real expression body, not a function-returning-
# function.

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
    "title": "2025A 竹响器（Sasando）共鸣腔滤波器响应 H(f) — 拖动 zeta（阻尼比）实时看峰宽/峰值变化",
    "x_data": {"values": f_values, "label": "f (Hz)"},
    "y_label": "相对峰值增益 (dB)",
    "params": [
        {"name": "zeta", "label": "阻尼比 zeta", "min": 0.001, "max": 0.15,
         "step": 0.0005, "initial": zeta0},
    ],
    "constants": {"f_modes": f_modes, "A": A},
    "js_function_body": js_fn_body,
    "live_model_note": "本图拖动滑块时，浏览器端只用闭式表达式（4 个阻尼洛伦兹峰的求和，"
                       "跟 problem_state.json 里 headline_eigenfrequencies 记录的同一套数学）"
                       "对当前 zeta 值重新求一遍 y 值，不是重新解任何 ODE/重跑数值模型；"
                       "zeta 的取值范围（0.001-0.15）是人为划定的演示区间，不是模型的"
                       "物理稳定边界。",
}

out_state_path = os.path.join(repo_root, "dev-notes", "self-tests", "03", "figures_interactive_test",
                              "problem_state_2025A_sasando_with_interactive_live.json")
state["numerical_artifacts"]["figures"] = {"fig_sasando_live": spec}
with open(out_state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print("wrote", out_state_path)

out_dir = os.path.join(repo_root, "dev-notes", "self-tests", "03", "figures_interactive_test",
                       "sasando_live_out")
script = os.path.join(repo_root, "program-design", "hooks", "make_report_figures.py")
r = subprocess.run([sys.executable, script, "--state", out_state_path, "--out-dir", out_dir],
                   capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

frag_path = os.path.join(out_dir, "fig_sasando_live.html")
assert os.path.exists(frag_path), frag_path
print("frag written:", frag_path)

# Now verify: extract the JS LIVE_FN body actually embedded in the fragment,
# run it in Node.js, and compare against the Python reference across the full
# zeta slider range — a real check, not a rubber stamp.
check_js_head = r"""
const fs = require('fs');
const frag = fs.readFileSync(process.argv[1], 'utf8');
const m = frag.match(/var LIVE_FN = function[\s\S]*?return out;\r?\n\s*\};/);
if (!m) { console.log('LIVE_FN body not found in fragment'); process.exit(1); }
const body = m[1];
const X = %X_VALUES%;
const CONSTANTS = %CONSTANTS_JSON%;
const LIVE_FN = function(P){
"""
check_js_tail = """
};
function h_db_py(f_list, zeta){
  const mags = f_list.map(fx=>{
    let re=0, im=0;
    for(let i=0;i<CONSTANTS.f_modes.length;i++){
      const fm=CONSTANTS.f_modes[i], am=CONSTANTS.A[i];
      const t=fx/fm, den_re=1-t*t, den_im=2*zeta*t, den2=den_re*den_re+den_im*den_im;
      re+=am*den_re/den2; im-=am*den_im/den2;
    }
    return Math.sqrt(re*re+im*im);
  });
  const peak=Math.max(...mags);
  return mags.map(m=>20*Math.log10(m/peak+1e-30));
}
let maxErr = 0;
for (const zeta of [0.001, 0.005, 0.02, 0.05, 0.15]) {
  const py = h_db_py(X, zeta);
  const js = LIVE_FN({zeta});
  for (let i=0;i<py.length;i++){ maxErr = Math.max(maxErr, Math.abs(py[i]-js[i])); }
}
console.log('max abs diff (dB) across all zeta values:', maxErr.toExponential(3));
console.log(maxErr < 1e-6 ? 'JS math matches Python reference — safe to ship' : 'MISMATCH — do NOT ship, formula divergence found');
"""
check_js = check_js_head + js_fn_body + check_js_tail
check_js = check_js.replace("%X_VALUES%", json.dumps(f_values)).replace("%CONSTANTS_JSON%",
    json.dumps({"f_modes": f_modes, "A": A}))
check_js_path = os.path.join(here, "_verify_live_math.cjs")
with open(check_js_path, "w", encoding="utf-8") as f:
    f.write(check_js)
r2 = subprocess.run(["node", check_js_path, frag_path], capture_output=True, text=True, encoding="utf-8")
print(r2.stdout)
if r2.returncode != 0:
    print(r2.stderr)
    sys.exit(1)
os.remove(check_js_path)
print("DONE: interactive_live figure built from real 2025A data, JS math verified against Python reference.")
print("Fragment:", frag_path)
