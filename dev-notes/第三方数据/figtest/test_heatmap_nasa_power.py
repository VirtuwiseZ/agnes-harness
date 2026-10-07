"""Test 2: NASA POWER T2M — 经纬度空间网格热图（真实地理数据，替代原计划失败的 NOAA）

按 heatmap推荐数据源.md 的建议实现。依赖：pandas, matplotlib。
NASA POWER CSV 前部有元数据（不是标准表头），必须先自动定位表头行（不能硬编码
skiprows），参考文件明确要求这一点。
"""
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "figs_heatmap_nasa_power")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, r"E:\agnes-harness\program-design\hooks")
import make_report_figures as m
m._configure_cjk_font()

CSV_PATH = os.path.join(DATA, "nasa_power_t2m_tokyo_202407.csv")

# --- 1. locate the header row dynamically (do NOT hard-code skiprows) ---
with open(CSV_PATH, encoding="utf-8") as f:
    lines = f.readlines()
header_line = None
for i, line in enumerate(lines, start=1):
    if line.strip().startswith("LAT,LON") or line.strip().startswith("LAT, LON"):
        header_line = i
        break
if header_line is None:
    raise SystemExit(f"could not locate the LAT,LON header row in {CSV_PATH}")
print(f"header located at line {header_line} (0-based {header_line - 1}) — not hard-coded")

df = pd.read_csv(CSV_PATH, skiprows=header_line - 1)
print("columns:", list(df.columns))
print("rows:", len(df))
for col in ("LAT", "LON", "YEAR", "MO", "DY", "T2M"):
    if col not in df.columns:
        raise SystemExit(f"expected column {col!r} not present; actual columns: {list(df.columns)}")
t2m_missing = int(df["T2M"].isna().sum())
print(f"T2M missing values: {t2m_missing} / {len(df)} "
      f"({t2m_missing / len(df) * 100:.1f}%); "
      f"mean T2M={float(df['T2M'].mean()):.2f}°C, "
      f"range=[{float(df['T2M'].min()):.2f}, {float(df['T2M'].max()):.2f}]°C")

# --- 2. pivot to a latitude x longitude matrix (monthly mean over July 2024) ---
t2m_missing_cell_count = 0
pivot = df.pivot_table(index="LAT", columns="LON", values="T2M", aggfunc="mean")
print(f"pivot shape: {pivot.shape} (LAT x LON)")
print("lat range:", pivot.index.min(), "-", pivot.index.max())
print("lon range:", pivot.columns.min(), "-", pivot.columns.max())

# --- 3a. draw with our own script's heatmap kind ---
y_values = [float(v) for v in pivot.index.tolist()]   # latitude (rows)
x_values = [float(v) for v in pivot.columns.tolist()]  # longitude (columns)
# Our script's convention: values_2d[i][j] = value at (x_values[j], y_values[i]),
# i.e. rows match the y axis (lat), columns match the x axis (lon).
# pivot has index=LAT (rows) and columns=LON (cols), so values_2d = pivot.values
# transposed appropriately: pivot.values[i][j] is already (LAT_i, LON_j) -> matches
# our convention directly, no transpose needed.
values_2d = [[(None if pd.isna(v) else float(v)) for v in row] for row in pivot.values]
n_nan_cells = sum(1 for row in values_2d for v in row if v is None)
print(f"nan cells in values_2d: {n_nan_cells} (rendered as blank, not 0, by design)")

fig_spec = {
    "kind": "heatmap",
    "title": "NASA POWER T2M 2m气温（东京周边，2024年7月，日均值按月平均；0.5°×0.625° 网格）",
    "series": [{"grid": {"x_values": x_values, "y_values": y_values, "values_2d": values_2d}}],
    "axes": {"x": {"label": "经度 (°E)"}, "y": {"label": "纬度 (°N)"},
             "z": {"label": "T2M 2m气温 (°C)"}},
}
out1 = os.path.join(OUT, "nasa_power_t2m_heatmap.png")
fig = m._draw_heatmap(fig_spec, "nasa_power_t2m")
fig.savefig(out1, dpi=150)
plt.close(fig)
print("wrote", out1)

# --- 3b. also render a plain-matplotlib version for cross-checking the data path ---
fig2, ax2 = plt.subplots(figsize=(7, 5), dpi=150)
im = ax2.pcolormesh(x_values, y_values, pivot.values, cmap="turbo", shading="auto")
ax2.set_xlabel("经度 (°E)")
ax2.set_ylabel("纬度 (°N)")
cbar = fig2.colorbar(im, ax=ax2)
cbar.set_label("T2M 2m气温 (°C)")
ax2.set_title("NASA POWER T2M 东京周边 2024年7月（matplotlib直绘，交叉验证）")
out2 = os.path.join(OUT, "nasa_power_t2m_heatmap_mpl_direct.png")
fig2.tight_layout()
fig2.savefig(out2, dpi=150)
plt.close(fig2)
print("wrote", out2)

print("\n=== summary ===")
print(f"grid: {len(y_values)} latitudes x {len(x_values)} longitudes, "
      f"{n_nan_cells} blank (NaN) cells out of {len(y_values) * len(x_values)} total")
print("check in the PNG: colors should vary smoothly across the 34-38N / 138-142E "
      "box, no pure-white gaps except where T2M was genuinely missing in the source data.")
