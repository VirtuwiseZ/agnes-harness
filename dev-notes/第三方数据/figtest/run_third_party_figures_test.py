"""Build numerical_artifacts.figures JSON for each of the 4 immediately-usable
third-party datasets (curve/scatter/error_bar/interval_highlight x2), then run
make_report_figures.py on each and confirm the output PNGs exist and are
non-trivial in size. Heatmap (NOAA SST) is skipped for now: its data file
(noaa_sst_pacific_20240115.csv) failed to download on this machine (SSL EOF),
and no replacement source has been picked yet — see charting_extension_scenarios
assessment note + this report, not silently papered over.
"""
import csv
import json
import math
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

THIRD = r"E:\agnes-harness\dev-notes\第三方数据"
FIGTEST = os.path.join(THIRD, "figtest")
SCRIPT = r"E:\agnes-harness\program-design\hooks\make_report_figures.py"


def run_figures(figures, label, out_dir):
    state = os.path.join(out_dir, f"_state_{label}.json")
    with open(state, "w", encoding="utf-8") as f:
        json.dump({"numerical_artifacts": {"figures": figures}}, f, ensure_ascii=False, indent=2)
    out = os.path.join(out_dir, f"figs_{label}")
    r = subprocess.run([sys.executable, SCRIPT, "--state", state, "--out-dir", out],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"\n=== {label} ===")
    print("returncode:", r.returncode)
    print(r.stdout.strip())
    if r.returncode != 0:
        print("STDERR:", r.stderr.strip())
    produced = []
    if os.path.isdir(out):
        for f in sorted(os.listdir(out)):
            p = os.path.join(out, f)
            size = os.path.getsize(p)
            produced.append((f, size))
            print("  ", f, size, "bytes")
    return produced, r.returncode


# ─── 1. curve: gistemp global annual anomaly (J-D column) ──────────────────
def build_gistemp_curve():
    years, anoms = [], []
    with open(os.path.join(THIRD, "gistemp_global_anomaly_1880-2026.csv"), encoding="utf-8") as f:
        lines = f.readlines()
    # find header line
    header = next(i for i, l in enumerate(lines) if l.startswith("Year,"))
    cols = lines[header].strip().split(",")
    jd_idx = cols.index("J-D")
    for line in lines[header + 1:]:
        parts = line.strip().split(",")
        if len(parts) < len(cols) or not parts[0].isdigit():
            continue
        y = int(parts[0])
        v = parts[jd_idx]
        if v.strip() in ("", "***"):
            continue
        years.append(y)
        anoms.append(float(v))
    return {
        "gistemp_annual_anomaly": {
            "kind": "curve",
            "title": "全球平均气温距平（年距平，相对 1951–1980 基准，°C）",
            "axes": {"x": {"label": "年份"}, "y": {"label": "年距平 (°C)"}},
            "series": [
                {"name": "年距平 (°C)", "kind_hint": "line_scatter",
                 "points": {"x": years, "y": anoms}},
            ],
            "highlights": [
                {"x0": 1998, "x1": 2012, "label": "持续偏暖区间（举例，非精确物理断言）"},
            ],
        }
    }


# ─── 2. scatter: exoplanet mass vs radius ─────────────────────────────────
def build_exoplanet_scatter():
    xs, ys, names = [], [], []
    with open(os.path.join(THIRD, "nasa_exoplanets_mass_radius.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                m = float(row["pl_masse"])
                r = float(row["pl_rade"])
            except (ValueError, KeyError):
                continue
            if not (math.isfinite(m) and math.isfinite(r)):
                continue
            xs.append(m)
            ys.append(r)
            names.append(row.get("pl_name", "").strip('"'))
    return {
        "exoplanet_mass_radius": {
            "kind": "scatter",
            "title": "Neptune 以内系外行星：质量–半径（地球单位）",
            "axes": {"x": {"label": "质量 M⊕"}, "y": {"label": "半径 R⊕"}},
            "series": [
                {"name": "M⊕ vs R⊕", "kind_hint": "scatter", "points": {"x": xs, "y": ys}},
            ],
            "markers": [],
            "n_points": len(xs),
        }
    }


# ─── 3. error_bar: NIST CODATA 2022, one dimensional family (kg) ─────────
# Parser extracted to codata_parser.py (same dir) after repeated failures to
# get the inline version's "..."/(exact) handling right — see that module's
# docstring for the format quirks (fixed-width, no literal pipes, thousands
# separators are single spaces, 5+-space field boundaries with a few 4-space
# exceptions).
from codata_parser import kg_constants_with_real_uncertainty


def build_codata_errorbar():
    kg, skipped = kg_constants_with_real_uncertainty(
        os.path.join(THIRD, "nist_codata2022_constants.txt"))
    print(f"codata parser: {len(kg)} kg-unit constants with a real (non-exact) "
          f"uncertainty; {skipped} rows skipped (no parseable value, or not a "
          f"data row / no 'kg' unit) — accounted for, not silently dropped.")
    if not kg:
        return {"codata_kg": {"kind": "error_bar", "series": [
            {"name": "none", "points": {"x": [], "y": []}}]}}

    picked = kg[:8]
    xs = list(range(1, len(picked) + 1))
    ys = [v for (_, _, v, _) in picked]
    errs = [u for (_, _, _, u) in picked]
    names = [q for (_, q, _, _) in picked]
    return {
        "codata_kg_errorbar": {
            "kind": "error_bar",
            "title": "NIST CODATA 2022 基本常数（kg 量纲子集，按组内相对编号排列；误差棒 = 标准不确定度）",
            "axes": {"x": {"label": "常数编号（本组内相对序号，非原始编号）"},
                     "y": {"label": "数值（kg，未归一化，仅本组内比较）"}},
            "series": [
                {"name": "kg 子集", "points": {"x": xs, "y": ys}, "y_err": errs},
            ],
            "const_names": names,
        }
    }


# ─── 4. interval_highlight: hydrogen emission lines + visible band ────────
def build_hydrogen_interval():
    rows = []
    with open(os.path.join(THIRD, "hydrogen_emission_lines.csv"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) < 6:
                continue
            wl = float(parts[0])
            series_name = parts[1]
            rel = float(parts[5])
            rows.append((wl, series_name, rel))
    wls = [r[0] for r in rows]
    intens = [r[2] for r in rows]
    series_groups = {}
    for wl, sname, rel in rows:
        series_groups.setdefault(sname, []).append((wl, rel))
    series = []
    for sname, pts in series_groups.items():
        pts_sorted = sorted(pts, key=lambda p: p[0])
        series.append({
            "name": sname,
            "kind_hint": "line_scatter",
            "points": {"x": [p[0] for p in pts_sorted], "y": [p[1] for p in pts_sorted]},
        })
    return {
        "hydrogen_lines_visible_band": {
            "kind": "interval_highlight",
            "title": "氢原子 H I 发射谱线（相对强度）+ 可见光区间高亮",
            "axes": {"x": {"label": "波长 (nm)"}, "y": {"label": "相对强度（各系内归一化）"}},
            "series": series,
            "highlights": [
                {"x0": 380, "x1": 780, "label": "可见光区间 380–780 nm"},
            ],
        }
    }


# ─── 5. interval_highlight: sunspot monthly + (illustrative) solar-max band
def build_sunspot_interval():
    year_frac, val, sd = [], [], []
    max_val = 0.0
    with open(os.path.join(THIRD, "sidc_sunspot_monthly_1749-2026.csv"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(";")]
            if len(parts) < 4:
                continue
            try:
                frac = float(parts[2])
                v = float(parts[3])
            except ValueError:
                continue
            year_frac.append(frac)
            val.append(v)
            max_val = max(max_val, v)

    # Downsample the 1749–present monthly series for a readable figure: keep one
    # value per year (take the last month of each year available) so the curve
    # is not a 277-year daily-resolution smear.
    by_year = {}
    for f_, v in zip(year_frac, val):
        y = int(f_)
        by_year[y] = v  # later months of the same year overwrite earlier ones
    yrs = sorted(by_year.keys())
    yearly_val = [by_year[y] for y in yrs]

    return {
        "sunspot_yearly_mean": {
            "kind": "interval_highlight",
            "title": "国际太阳黑子数（年距平，每年取该年最后一期的月均值近似）",
            "axes": {"x": {"label": "年份"}, "y": {"label": "年均太阳黑子数"}},
            "series": [
                {"name": "年均 ISN", "kind_hint": "line_scatter",
                 "points": {"x": yrs, "y": yearly_val}},
            ],
            # NOTE: this is a deliberately crude illustrative band, not an
            # actual solar-cycle calculation (that would be a physics judgment
            # this test is not trying to make) — it just exercises the
            # interval_highlight rendering path with a real highlight range.
            "highlights": [
                {"x0": min(yrs), "x1": max(yrs), "label": "有观测记录的全时段（示意性高亮，非物理断言）"},
            ],
        }
    }


def main():
    os.makedirs(FIGTEST, exist_ok=True)
    all_results = {}

    all_results["curve_gistemp"] = run_figures(build_gistemp_curve(), "curve_gistemp", FIGTEST)
    all_results["scatter_exoplanets"] = run_figures(build_exoplanet_scatter(), "scatter_exoplanets", FIGTEST)
    all_results["errorbar_codata"] = run_figures(build_codata_errorbar(), "errorbar_codata", FIGTEST)
    all_results["interval_hydrogen"] = run_figures(build_hydrogen_interval(), "interval_hydrogen", FIGTEST)
    all_results["interval_sunspot"] = run_figures(build_sunspot_interval(), "interval_sunspot", FIGTEST)

    print("\n=== SUMMARY ===")
    for k, (produced, rc) in all_results.items():
        print(f"{k}: rc={rc} produced={len(produced)} file(s)")
        for f, size in produced:
            print(f"    {f} ({size} bytes)")

    # Also dump the assembled state files so a human can inspect the exact
    # figures JSON each test used.
    for label in ["curve_gistemp", "scatter_exoplanets", "errorbar_codata",
                   "interval_hydrogen", "interval_sunspot"]:
        src = os.path.join(FIGTEST, f"_state_{label}.json")
        if os.path.exists(src):
            print(f"\nstate file for {label}: {src}")


if __name__ == "__main__":
    main()
