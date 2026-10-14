"""
generate_figures.py
===================
Prepares and renders scientific figures for the Jupiter gravity assist evaluation report:
1. `fig_assist_vs_capture`: Bar chart comparing gravity assist deceleration vs capture requirements.
2. `fig_velocity_sweep`: Parametric sweep curve showing deflection deceleration degradation at high encounter speeds.
Updates `problem_state.json`'s `numerical_artifacts.figures` and runs `make_report_figures.py`.
"""

import os
import sys
import json
import subprocess
import math

TASK_SLUG = "jupiter-moon-gravity-assist-decel"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TASK_DIR = os.path.join(BASE_DIR, "physics-agent", "runtime", TASK_SLUG)
HOOKS_DIR = os.path.join(BASE_DIR, "physics-agent", "hooks")
STATE_PATH = os.path.join(TASK_DIR, "problem_state.json")
FIG_DIR = os.path.join(TASK_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

sys.path.insert(0, HOOKS_DIR)
import audit_log

# Load calculation results
with open(os.path.join(TASK_DIR, "results.json"), "r", encoding="utf-8") as f:
    res = json.load(f)

# Moon constants
moons = res["moons"]

# 1. Figure 1: Bar chart
categories = ["木卫一 (Io)", "木卫二 (Europa)", "木卫三 (Ganymede)", "木卫四 (Callisto)"]
assist_vals = [
    round(moons["Io"]["max_assist_delta_v_km_s"], 3),
    round(moons["Europa"]["max_assist_delta_v_km_s"], 3),
    round(moons["Ganymede"]["max_assist_delta_v_km_s"], 3),
    round(moons["Callisto"]["max_assist_delta_v_km_s"], 3)
]
capture_vals = [
    round(moons["Io"]["direct_capture_delta_v_at_moon_km_s"], 3),
    round(moons["Europa"]["direct_capture_delta_v_at_moon_km_s"], 3),
    round(moons["Ganymede"]["direct_capture_delta_v_at_moon_km_s"], 3),
    round(moons["Callisto"]["direct_capture_delta_v_at_moon_km_s"], 3)
]

fig1 = {
    "kind": "bar",
    "title": "伽利略四卫星单次飞掠最大减速量与轨道捕获制动需求对比",
    "categories": categories,
    "series": [
        {
            "name": "单次飞掠最大理论减速量 (km/s)",
            "values": assist_vals,
            "color": "#38bdf8"
        },
        {
            "name": "卫星高度直接捕获所需制动量 (km/s)",
            "values": capture_vals,
            "color": "#ef4444"
        }
    ],
    "thresholds": [
        {
            "axis": "y",
            "value": round(res["baseline_capture"]["delta_v_parabolic_cap_km_s"], 3),
            "label": "近木点极限奥伯斯特捕获需求 (3.35 km/s)"
        }
    ],
    "axes": {
        "x": {"label": "天体目标"},
        "y": {"label": "速度变化量 Δv (km/s)"}
    }
}

# 2. Figure 2: Parametric sweep curve
# v_rel from 8 to 40 km/s
v_sweep = [float(f"{v:.1f}") for v in [8.0 + 0.5 * i for i in range(65)]]

def calc_curve(r_m, mu_m):
    y = []
    for v in v_sweep:
        denom = 1.0 + (r_m * (v ** 2)) / mu_m
        s_half = 1.0 / denom
        y.append(round(2.0 * v * s_half, 4))
    return y

curve_io = calc_curve(1821.6, 5959.916)
curve_eur = calc_curve(1560.8, 3202.739)
curve_gan = calc_curve(2634.1, 9887.834)
curve_cal = calc_curve(2410.3, 7179.289)

fig2 = {
    "kind": "curve",
    "title": "伽利略四卫星最大引力助推减速能力随相对相遇速度衰减规律",
    "axes": {
        "x": {"label": "相对相遇速度 v_inf,rel (km/s)"},
        "y": {"label": "最大理论减速量 Δv_max (km/s)"}
    },
    "series": [
        {
            "name": "木卫三 (Ganymede, R=2634km)",
            "role": "theory",
            "points": {"x": v_sweep, "y": curve_gan}
        },
        {
            "name": "木卫一 (Io, R=1822km)",
            "role": "simulation",
            "points": {"x": v_sweep, "y": curve_io}
        },
        {
            "name": "木卫四 (Callisto, R=2410km)",
            "role": "fit",
            "points": {"x": v_sweep, "y": curve_cal}
        },
        {
            "name": "木卫二 (Europa, R=1561km)",
            "role": "experiment",
            "points": {"x": v_sweep, "y": curve_eur}
        }
    ],
    "markers": [
        {
            "x": round(moons["Ganymede"]["min_relative_speed_v_inf_rel_km_s"], 2),
            "y": round(moons["Ganymede"]["max_assist_delta_v_km_s"], 3),
            "label": "木卫三实际工作点 (14.35 km/s, 0.51 km/s)"
        },
        {
            "x": round(moons["Io"]["min_relative_speed_v_inf_rel_km_s"], 2),
            "y": round(moons["Io"]["max_assist_delta_v_km_s"], 3),
            "label": "木卫一实际工作点 (14.30 km/s, 0.45 km/s)"
        }
    ]
}

# Update problem_state.json
with open(STATE_PATH, "r", encoding="utf-8") as f:
    state = json.load(f)

if "numerical_artifacts" not in state:
    state["numerical_artifacts"] = {}

state["numerical_artifacts"]["figures"] = {
    "fig_assist_vs_capture": fig1,
    "fig_velocity_sweep": fig2
}

with open(STATE_PATH, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print("已写入 figures 定义至 problem_state.json！")

# Invoke make_report_figures.py
script_path = os.path.join(HOOKS_DIR, "make_report_figures.py")
cmd = [
    sys.executable,
    script_path,
    "--state", STATE_PATH,
    "--out-dir", FIG_DIR,
    "--format", "png"
]
proc = subprocess.run(cmd, capture_output=True, text=True)
print(f"绘图退出码: {proc.returncode}")
print(proc.stdout)
if proc.stderr:
    print(proc.stderr)

if proc.returncode != 0:
    raise RuntimeError(f"绘图失败! {proc.stderr}")

rec = audit_log.append_record(
    state_path=STATE_PATH,
    source="agent-node2.7-figures",
    args={
        "note": "生成引力助推减速与入轨需求对比柱状图及相对速度敏感性扫描曲线图，完成 Node 2.7 科学可视化资产构建。"
    },
    extras={
        "script_path": "physics-agent/hooks/make_report_figures.py",
        "stdin_or_argv": "make_report_figures.py --format png",
        "stdout_tail": proc.stdout[-500:],
        "stderr": proc.stderr[-500:],
        "exit_code": proc.returncode,
        "iteration_index": 1
    }
)
print(f"绘图审计已记录: artifact_id = {rec['artifact_id']}")
