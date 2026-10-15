"""
generate_figures_data.py
========================
Prepares figure specifications for Node 2.7 and calls make_report_figures.py.
Figures generated:
  1. fig_slit_dispersion: Multi-wavelength diffraction intensity curves (450nm, 532nm, 633nm).
  2. fig_airy_rayleigh: Airy disk profile & Rayleigh saddle dip at v1=3.8317.
  3. fig_orbit_resolution_great_wall: Ground resolution Delta x(h) vs Great Wall widths (5~8m).
  4. fig_microscope_resolution_bar: Abbe & Rayleigh microscope resolution at NA=1.4.
"""

import os
import sys
import json
import subprocess
import numpy as np
import scipy.special as sp

TASK_SLUG = "wave-optics-diffraction-resolution"
STATE_PATH = f"physics-agent/runtime/{TASK_SLUG}/problem_state.json"
FIG_OUT_DIR = f"physics-agent/runtime/{TASK_SLUG}/figures"
os.makedirs(FIG_OUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Figure 1: Slit Dispersion
# -----------------------------------------------------------------------------
a = 50e-6 # 50 um
theta_mrad = np.linspace(-30.0, 30.0, 301)
theta_rad = theta_mrad * 1e-3

def calc_slit_I(wl):
    beta = (np.pi * a / wl) * np.sin(theta_rad)
    val = np.sinc(beta / np.pi)
    return (val ** 2).tolist()

fig1_spec = {
    "title": "不同波长单缝夫琅禾费衍射归一化光强分布与色散展宽对比 (a = 50 μm)",
    "kind": "curve",
    "axes": {
        "x": {"label": "衍射角 θ (mrad)"},
        "y": {"label": "归一化光强 I(θ) / I_0"}
    },
    "series": [
        {
            "name": "蓝光 (λ = 450 nm)",
            "role": "theory",
            "points": {
                "x": theta_mrad.tolist(),
                "y": calc_slit_I(450e-9)
            }
        },
        {
            "name": "绿光 (λ = 532 nm)",
            "role": "simulation",
            "points": {
                "x": theta_mrad.tolist(),
                "y": calc_slit_I(532e-9)
            }
        },
        {
            "name": "红光 (λ = 633 nm)",
            "role": "fit",
            "points": {
                "x": theta_mrad.tolist(),
                "y": calc_slit_I(633e-9)
            }
        }
    ]
}

# -----------------------------------------------------------------------------
# 2. Figure 2: Airy Disk & Rayleigh Dip
# -----------------------------------------------------------------------------
v_arr = np.linspace(-8.0, 8.0, 321)

def airy_intensity(v):
    res = np.ones_like(v)
    nz = np.abs(v) > 1e-12
    v_nz = v[nz]
    res[nz] = (2.0 * sp.jv(1, v_nz) / v_nz) ** 2
    return res

v1 = 3.83170597
I_single = airy_intensity(v_arr)
# Two point sources separated by v1
I_two_sources = airy_intensity(v_arr - v1 / 2.0) + airy_intensity(v_arr + v1 / 2.0)
# Normalize two-source sum relative to single peak
I_two_sources_norm = I_two_sources / 1.0

fig2_spec = {
    "title": "圆孔衍射艾里斑分布与瑞利判据鞍部光强对比 (第一零点 v1 = 3.832)",
    "kind": "curve",
    "axes": {
        "x": {"label": "广义衍射角坐标 v = (πD/λ)·sin(θ)"},
        "y": {"label": "相对光强 I / I_max"}
    },
    "thresholds": [
        {
            "axis": "y",
            "value": 0.735,
            "label": "瑞利判据鞍部相对光强 (73.5%)",
            "color": "#ef4444",
            "style": "--"
        }
    ],
    "series": [
        {
            "name": "单圆孔艾里斑相对强度 [2J1(v)/v]²",
            "role": "theory",
            "points": {
                "x": v_arr.tolist(),
                "y": I_single.tolist()
            }
        },
        {
            "name": "双点源重叠合成光强 (间距 Δv = 3.832)",
            "role": "simulation",
            "points": {
                "x": v_arr.tolist(),
                "y": I_two_sources_norm.tolist()
            }
        }
    ]
}

# -----------------------------------------------------------------------------
# 3. Figure 3: Orbit Resolution vs Great Wall
# -----------------------------------------------------------------------------
h_km = np.linspace(200.0, 400.0, 21)
theta_min_rad = 1.21966989 * (550e-9 / 2.5e-3) # 2.68327e-4 rad
dx_m = h_km * 1e3 * theta_min_rad

fig3_spec = {
    "title": "近地轨道高度 (200~400 km) 肉眼极限地面分辨距离与长城宽度对比",
    "kind": "curve",
    "axes": {
        "x": {"label": "近地轨道高度 h (km)"},
        "y": {"label": "地面线分辨极限 Δx (m)"}
    },
    "thresholds": [
        {
            "axis": "y",
            "value": 8.0,
            "label": "长城关隘/基底最大宽度 (8 m)",
            "color": "#f59e0b",
            "style": "-."
        },
        {
            "axis": "y",
            "value": 5.0,
            "label": "长城顶宽公称典型值 (5 m)",
            "color": "#10b981",
            "style": ":"
        }
    ],
    "series": [
        {
            "name": "航天员肉眼衍射极限分辨线度 Δx(h) = h·θ_min",
            "role": "theory",
            "points": {
                "x": h_km.tolist(),
                "y": dx_m.tolist()
            }
        }
    ]
}

# -----------------------------------------------------------------------------
# 4. Figure 4: Microscope Abbe & Rayleigh Limits Bar Chart
# -----------------------------------------------------------------------------
cat_names = ["紫光 (400nm)", "蓝光 (450nm)", "绿光 (532nm)", "黄绿光 (550nm)", "红光 (633nm)"]
na_val = 1.4
wl_list = [400.0, 450.0, 532.0, 550.0, 633.0]
abbe_vals = [round(wl / (2.0 * na_val), 1) for wl in wl_list]
rayleigh_vals = [round(0.60983494 * wl / na_val, 1) for wl in wl_list]

fig4_spec = {
    "title": "油浸物镜极限数值孔径 (NA = 1.4) 下普通可见光显微镜空间分辨率极限对比",
    "kind": "bar",
    "categories": cat_names,
    "axes": {
        "y": {"label": "极限空间分辨率 (nm)"}
    },
    "series": [
        {
            "name": "阿贝衍射极限 d = λ / (2·NA)",
            "values": abbe_vals,
            "color": "#3b82f6"
        },
        {
            "name": "瑞利判据极限 d = 0.61·λ / NA",
            "values": rayleigh_vals,
            "color": "#8b5cf6"
        }
    ]
}

# -----------------------------------------------------------------------------
# Update problem_state.json with figures dictionary
# -----------------------------------------------------------------------------
with open(STATE_PATH, "r", encoding="utf-8") as f:
    state = json.load(f)

if "numerical_artifacts" not in state:
    state["numerical_artifacts"] = {}

state["numerical_artifacts"]["figures"] = {
    "fig_slit_dispersion": fig1_spec,
    "fig_airy_rayleigh": fig2_spec,
    "fig_orbit_resolution_great_wall": fig3_spec,
    "fig_microscope_resolution_bar": fig4_spec
}

with open(STATE_PATH, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print(">>> problem_state.json updated with 4 figure specifications.")

# -----------------------------------------------------------------------------
# Execute make_report_figures.py
# -----------------------------------------------------------------------------
cmd = [
    sys.executable,
    "physics-agent/hooks/make_report_figures.py",
    "--state", STATE_PATH,
    "--out-dir", FIG_OUT_DIR
]
print(">>> Running make_report_figures.py...")
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
print("STDOUT:", res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
if res.returncode != 0:
    print(f"Error: make_report_figures.py exited with code {res.returncode}")
    sys.exit(res.returncode)

# Append audit log
sys.path.append("physics-agent/hooks")
import audit_log
audit_log.append_record(
    STATE_PATH,
    source="make_report_figures.py",
    args={"note": "完成 Node 2.7 科学图表绘制：生成单缝多波长色散曲线族、圆孔艾里斑与瑞利鞍部光强图、近地轨道人眼分辨率与长城尺度对照曲线、以及极限浸油显微物镜最高空间分辨率柱状图，共 4 幅自包含矢量图表。"},
    extras={
        "script_path": "physics-agent/hooks/make_report_figures.py",
        "stdin_or_argv": f"python make_report_figures.py --state {STATE_PATH} --out-dir {FIG_OUT_DIR}",
        "stdout_tail": res.stdout.strip(),
        "stderr": res.stderr.strip() if res.stderr else "",
        "exit_code": res.returncode,
        "iteration_index": 1
    }
)
print(">>> Node 2.7 Charting and Audit Log Complete.")
