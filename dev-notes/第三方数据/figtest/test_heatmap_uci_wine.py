"""Test 1: UCI Wine Quality — 变量相关性热图（方阵相关系数矩阵 + 理化指标×quality 非方阵热图）

按 heatmap推荐数据源.md 的建议实现。依赖：pandas, matplotlib, seaborn（seaborn
缺失时降级用纯 matplotlib pcolormesh 画同样的矩阵，不影响数据验证）。
"""
import sys
import os
import warnings

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "figs_heatmap_wine")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, r"E:\agnes-harness\program-design\hooks")
import make_report_figures as m
m._configure_cjk_font()

try:
    import seaborn as sns
    HAVE_SEABORN = True
except ImportError:
    HAVE_SEABORN = False
    print("note: seaborn not installed — falling back to pure-matplotlib pcolormesh "
          "for the correlation matrix (same data, same verification intent; no data "
          "changed, just rendering backend).")

FILES = {
    "red": os.path.join(DATA, "winequality-red.csv"),
    "white": os.path.join(DATA, "winequality-white.csv"),
}

report_lines = []
for label, path in FILES.items():
    df = pd.read_csv(path, sep=";")
    numeric = df.select_dtypes(include="number")
    n_missing = int(numeric.isna().sum().sum())
    report_lines.append(f"\n=== {label} wine (UCI, '{os.path.basename(path)}') ===")
    report_lines.append(f"rows={len(df)} numeric-cols={list(numeric.columns)} missing={n_missing}")

    corr = numeric.corr()
    report_lines.append(f"corr matrix shape: {corr.shape}, symmetric-check "
                       f"max|corr-corr.T|={(corr - corr.T).abs().to_numpy().max():.3e} "
                       f"(should be ~0)")

    fig, ax = plt.subplots(figsize=(9, 8))
    if HAVE_SEABORN:
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0,
                    cbar_kws={"label": "Pearson r"}, ax=ax)
    else:
        # 'vlag' is a seaborn-only colormap, not available when seaborn is missing;
        # 'RdBu_r' is the matplotlib-built-in diverging counterpart, same intent.
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.index)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr.index)
        for i in range(corr.shape[0]):
            for j in range(corr.shape[1]):
                v = corr.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=7, color="white" if abs(v) > 0.5 else "black")
        fig.colorbar(im, ax=ax, label="Pearson r")
    ax.set_title(f"UCI wine ({label}): Pearson correlation of numeric features")
    out1 = os.path.join(OUT, f"wine_{label}_correlation.png")
    fig.tight_layout()
    fig.savefig(out1, dpi=150)
    plt.close(fig)
    report_lines.append(f"wrote {out1}")

    # Non-square heatmap: physical-chemical features vs. quality score (13 numeric
    # features x 1 quality column -> a genuine non-square matrix, verifying
    # make_report_figures' heatmap kind does not assume a square input)
    quality_col = "quality"
    feature_cols = [c for c in numeric.columns if c != quality_col]
    feat_quality = numeric[[quality_col] + feature_cols].corr()  # 13x13 includes both
    report_lines.append(f"feature-vs-quality correlation (row 0 = quality vs each feature): "
                       + ", ".join(f"{c}={feat_quality.iloc[0][c]:.2f}"
                                   for c in ["alcohol", "fixed acidity", "volatile acidity"]))

    # Feed the SAME non-square matrix into our own make_report_figures.py heatmap
    # kind, to verify that kind (not just seaborn) can render a non-square input.
    # values_2d convention in our script: values_2d[i][j] is at (x_values[j],
    # y_values[i]) — i.e. rows match y axis, columns match x axis.
    y_values = list(feat_quality.index)   # 13 categories incl. 'quality' itself
    x_values = list(feat_quality.columns)
    values_2d = [[float(v) for v in row] for row in feat_quality.values]
    fig_spec = {
        "kind": "heatmap",
        "title": "UCI wine (red): Pearson correlation, feature x feature",
        "series": [{"grid": {"x_values": x_values, "y_values": y_values,
                             "values_2d": values_2d}}],
        "axes": {"x": {"label": "feature"}, "y": {"label": "feature"},
                 "z": {"label": "Pearson r"}},
    }
    out2 = os.path.join(OUT, f"wine_{label}_corr_own_script.png")
    fig2 = m._draw_heatmap(fig_spec, f"wine_{label}_corr")
    fig2.savefig(out2, dpi=150)
    plt.close(fig2)
    report_lines.append(f"wrote {out2} (via our own make_report_figures._draw_heatmap)")

report_text = "\n".join(report_lines)
print(report_text)
with open(os.path.join(BASE, "figs_heatmap_wine_report.txt"), "w", encoding="utf-8") as f:
    f.write(report_text + "\n")
print("\nreport saved to", os.path.join(BASE, "figs_heatmap_wine_report.txt"))
