"""Test 3: OWID Annual CO2 emissions per country — 类别 × 时间热图（非地理网格）

按 heatmap推荐数据源.md 的建议实现。重点验证：
- 长表转宽表 (pivot_table)
- 类别轴 (国家名) 排序
- 缺失值留白
- 三种色标策略对比（线性 / 对数 / 按国家行归一化）
依赖：pandas, matplotlib。列名不硬编码，先检查实际列名（参考文件明确要求）。
"""
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "figs_heatmap_owid_co2")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, r"E:\agnes-harness\program-design\hooks")
import make_report_figures as m
m._configure_cjk_font()

CSV_PATH = os.path.join(DATA, "owid_co2_per_country.csv")
df = pd.read_csv(CSV_PATH)
print("columns:", list(df.columns))
# column names may have changed across versions — inspect, do not assume
country_col = "Entity" if "Entity" in df.columns else "Country"
year_col = "Year"
value_col = next((c for c in df.columns if "CO" in c or "emission" in c.lower()), None)
print(f"using: country_col={country_col!r}, year_col={year_col!r}, value_col={value_col!r}")
if value_col is None:
    raise SystemExit(f"could not identify the CO2 value column from {list(df.columns)}")

COUNTRIES = ["China", "United States", "India", "Japan", "Germany",
             "Russia", "Brazil", "Indonesia", "Canada", "South Korea"]
year_min, year_max = 2000, 2024

# verify the requested countries actually exist in this version of the file
present = set(df[country_col].dropna().unique())
missing_countries = [c for c in COUNTRIES if c not in present]
if missing_countries:
    print("WARNING: not found in this CSV version (names may have changed):", missing_countries)
    COUNTRIES = [c for c in COUNTRIES if c in present]
print("countries actually used:", COUNTRIES)

sub = df[(df[country_col].isin(COUNTRIES)) & df[year_col].between(year_min, year_max)]
print(f"filtered rows: {len(sub)} (expected ~{len(COUNTRIES)} x {year_max - year_min + 1} = "
      f"{len(COUNTRIES) * (year_max - year_min + 1)})")

pivot = sub.pivot_table(index=country_col, columns=year_col, values=value_col, aggfunc="first")
pivot = pivot.sort_index()  # alphabetical country order
n_missing = int(pivot.isna().sum().sum())
print(f"pivot shape: {pivot.shape} ({len(pivot)} countries x {pivot.shape[1]} years); "
      f"missing cells: {n_missing} ({n_missing / pivot.size * 100:.1f}%)")

# --- three color-scale strategies ---
def draw_heatmap(mat, out_path, title, cbar_label, norm=None, cmap="magma", transpose=False):
    data = mat.T if transpose else mat  # our script: rows=y, cols=x
    y_values = [str(i) for i in (mat.columns if transpose else mat.index)]
    x_values = [str(c) for c in (mat.index if transpose else mat.columns)]
    values_2d = [[(None if pd.isna(v) else float(v)) for v in row]
                 for row in (mat.T.values if transpose else mat.values)]
    fig_spec = {
        "kind": "heatmap",
        "title": title,
        "series": [{"grid": {"x_values": x_values, "y_values": y_values, "values_2d": values_2d}}],
        "axes": {"x": {"label": "年份"}, "y": {"label": "国家/地区"}, "z": {"label": cbar_label}},
        "heatmap_style": "pcolormesh",
    }
    fig = m._draw_heatmap(fig_spec, out_path)
    if norm is not None:
        im = fig.axes[0].images[0]
        im.set_norm(norm)
        fig.colorbar(im, ax=fig.axes[0], label=cbar_label)
    fig.savefig(os.path.join(OUT, out_path + ".png"), dpi=150)
    plt.close(fig)
    print(f"wrote {out_path}.png")

# 1. linear color scale
draw_heatmap(pivot, "owid_co2_linear",
             f"OWID 年度CO2排放（{COUNTRIES[0]}等{len(COUNTRIES)}个主要国家/地区，"
             f"{year_min}-{year_max}；线性色标）",
             "年度CO2排放量（万吨）")

# 2. log color scale
log_norm = LogNorm()
draw_heatmap(pivot, "owid_co2_log",
             f"OWID 年度CO2排放（同左；对数色标）",
             "年度CO2排放量（万吨，log色标）", norm=log_norm)

# 3. row-normalized (per-country relative to its own max)
normalized = pivot.div(pivot.max(axis=1), axis=0)
n_missing_norm = int(normalized.isna().sum().sum())
print(f"row-normalized pivot missing cells: {n_missing_norm} "
      f"(should equal {n_missing}, since dividing by a finite max cannot create NaN "
      f"where there was a value, and 0/0 is not present here since max>0)")
draw_heatmap(normalized, "owid_co2_row_normalized",
             f"OWID 年度CO2排放（按国家行归一化：除以该国自身峰值；viridis色标）",
             "相对该国峰值的排放比 (0-1)", cmap="viridis")
# override the default 'magma' cmap for this one, since the script currently hardcodes
# viridis — the script's _draw_heatmap uses "viridis" for the pcolormesh branch
# unconditionally; to honor the request's 'viridis' for this variant we just restate it
# (no-op here, already viridis) — kept for clarity if the script's default ever changes.

print("\n=== summary ===")
print(f"countries: {COUNTRIES}")
print(f"missing cells in raw pivot: {n_missing} (rendered as blank, not 0, by design)")
print("check in the PNGs: linear vs log should differ most dramatically for the top-2 "
      "emitters (China/US) vs smaller countries; row-normalized should show each country's "
      "own time shape regardless of its absolute scale.")
