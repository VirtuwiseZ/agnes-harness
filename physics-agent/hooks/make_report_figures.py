"""Node 2.7 (optional) — render numerical-artifact figures for a report.

Reads ONLY `problem_state.json`'s `numerical_artifacts.figures` (the domain-
neutral sub-schema documented in physics-agent/problem_state_schema.md
§Figures and in dev-notes/self-tests/03/charting_generic_architecture.md §2,
v2) and writes one image file per figure to an output directory, for Node 4
(trace_visualizer.py --figures-dir) to inline into the final HTML.

Design principles (kept deliberately narrow — see the v2 architecture doc):

* **Never invent or silently "fix" data.** If `points.x` and `points.y` have
  different lengths, this script refuses to draw that figure and reports the
  exact mismatch — it does not truncate, pad, or guess. If a value is NaN or
  Inf, matplotlib will skip/clamp it (its default behavior) and this script
  appends a visible footnote naming how many points were affected, instead of
  quietly replacing them with a finite number.
* **Presentation-layer judgment is allowed, physics-layer judgment is not.**
  What the agent (upstream, in Node 2.7) decides: which data points belong in
  which series, which `role` each series gets, what the axis labels say. What
  this script decides on its own, with no hidden physics: axis limits that
  include every finite data point (no silent cropping); a deterministic
  style table per `role` (so theory/experiment/simulation/residual/fit read
  consistently across figures); legend ordering (series order as given, then
  role, then name — stable, not re-sorted by value); and, only when two or
  more points share an identical (x,y) coordinate on a scatter series, a
  small fixed-size jitter applied purely so the overlap is visible — the
  jitter is uniform in magnitude and applied to the copy drawn on screen,
  never written back anywhere, and the original numbers are unchanged on
  disk. Everything else (units, "is this number physically plausible",
  "should this point be here at all") is NOT this script's job — that has
  already been the dimensional/boundary gates' job upstream; this script
  trusts it and moves on.
* **No silent success on missing input.** `figures` empty/absent is a valid,
  explicitly-handled case (nothing to draw, say so plainly, exit 0) — not the
  same as `figures` present but malformed, which is an error.

Usage:
    python physics-agent/hooks/make_report_figures.py \
        --state physics-agent/runtime/problem_state_<task-slug>.json \
        --out-dir physics-agent/runtime/figures_<task-slug> \
        [--format png|svg]
"""
import argparse
import html as html_lib
import json
import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")  # headless, no display needed — always a non-interactive run
import matplotlib.font_manager as _fm
import matplotlib.pyplot as plt
import platform
import warnings

def _configure_cjk_font():
    """matplotlib's default font (DejaVu Sans) has no CJK glyphs — any figure
    with a Chinese title/label would otherwise render as tofu boxes with a
    flood of UserWarnings. Pick the first CJK-capable system font that's
    actually installed, in order of likelihood on this project's target
    machine (Windows); if none are found, fall back to the default and emit
    a single visible warning so the missing-glyph problem is never silent."""
    candidates = [
        ["Microsoft YaHei", "微软雅黑"],
        ["SimHei", "黑体"],
        ["Noto Sans CJK SC", "Noto Sans CJK SC"],
        ["WenQuanYi Zen Hei", "WenQuanYi Zen Hei"],
        ["Arial Unicode MS"],
    ]
    available = {f.name for f in _fm.fontManager.ttflist}
    for fam in candidates:
        if any(f in available for f in fam):
            keep = list(plt.rcParams["font.sans-serif"])
            for f in reversed(fam):
                if f in keep:
                    keep.remove(f)
            plt.rcParams["font.sans-serif"] = fam + keep
            plt.rcParams["axes.unicode_minus"] = False
            return
    warnings.warn(
        "make_report_figures: no CJK-capable font found on this system; figures "
        "with Chinese text will render with missing glyphs. Install e.g. "
        "'Noto Sans CJK SC' or 'Microsoft YaHei' and retry.")

_configure_cjk_font()

ROLE_STYLE = {
    "theory": dict(linestyle="-", marker="o"),
    "experiment": dict(linestyle=":", marker="^"),
    "simulation": dict(linestyle="--", marker="s"),
    "residual": dict(linestyle="--", color="0.5"),
    "fit": dict(linestyle="-.", marker="d"),
}
DEFAULT_ROLE_STYLE = dict(linestyle="-", marker="o")


class FigureError(Exception):
    """A figure in `numerical_artifacts.figures` is malformed in a way that
    must not be papered over (dimension mismatch, unknown kind, etc.)."""


def _require_same_len(name, x, y):
    if len(x) != len(y):
        raise FigureError(
            f"series '{name}': x has {len(x)} points, y has {len(y)} points; "
            f"refusing to draw — pad or remove the mismatched series upstream "
            f"(this script does not truncate, pad, or guess)."
        )


def _finite_counts(vals):
    n_nan = sum(1 for v in vals if isinstance(v, (int, float)) and math.isnan(v))
    n_inf = sum(1 for v in vals if isinstance(v, (int, float)) and math.isinf(v))
    return n_nan, n_inf


def _axis_label(fig_spec, axis, fallback_series_names):
    axes = fig_spec.get("axes") or {}
    label = (axes.get(axis) or {}).get("label")
    if label:
        return label
    return fallback_series_names[0] if fallback_series_names else axis


def _axis_scale(fig_spec, axis):
    """Per-axis scale: 'linear' (default, absence of the field) or 'log'.
    Only meaningful for numeric axes; a categorical/integer-tick axis that
    is not actually numeric (e.g. a label list used via a categorical heatmap
    branch) must not ask for 'log' — that combination is rejected at the
    call site, not silently ignored."""
    axes = fig_spec.get("axes") or {}
    return (axes.get(axis) or {}).get("scale", "linear")


def _count_nonpositive(vals):
    """How many of these values are <= 0 (NaN/Inf excluded from the count;
    they are handled by the existing NaN/Inf footnote, not by this one — a
    NaN is not 'non-positive', it is simply not a number)."""
    n = 0
    for v in vals:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if math.isnan(v) or math.isinf(v):
                continue
            if v <= 0:
                n += 1
    return n


def _apply_scientific_axes_style(ax):
    """Apply clean publication-grade styling (gridlines, despined top/right)."""
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.35, color="#888888")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        if side in ax.spines:
            ax.spines[side].set_visible(False)


def _draw_thresholds(ax, fig_spec, all_x, all_y):
    """Draw horizontal/vertical physical reference threshold lines and include
    their values in all_x/all_y so axis limits never clip a threshold line."""
    for th in fig_spec.get("thresholds") or []:
        axis_name = th.get("axis", "y")
        val = th.get("value")
        if not isinstance(val, (int, float)) or not math.isfinite(val):
            continue
        color = th.get("color", "#d62728")
        style = th.get("style", "--")
        label = th.get("label") or f"{axis_name} = {val}"
        if axis_name == "x":
            ax.axvline(val, color=color, linestyle=style, linewidth=1.6, label=label, zorder=4)
            all_x.append(val)
        else:
            ax.axhline(val, color=color, linestyle=style, linewidth=1.6, label=label, zorder=4)
            all_y.append(val)


def _check_degeneracy_and_scale(series, fig_id, y_scale, footnotes, allow_constant=False):
    """Anti-Blank / Anti-Flat Gate (preventing Test 5 Run #1's 'near-blank curve' failure):
    1. Rejects figures where ALL multi-point series are completely flat (zero variance),
       unless allow_constant=True is explicitly set.
    2. Footnotes when positive values span >50x on a linear axis with >75% of points
       compressed into the bottom 10% of the range."""
    if not series or allow_constant:
        return
    non_flat_count = 0
    multi_point_count = 0
    all_finite_y = []
    for s in series:
        pts = s.get("points") or {}
        ys = [v for v in (pts.get("y") or []) if isinstance(v, (int, float)) and math.isfinite(v)]
        all_finite_y.extend(ys)
        if len(ys) >= 3:
            multi_point_count += 1
            y_span = max(ys) - min(ys)
            y_scale_ref = max(abs(sum(ys) / len(ys)), 1.0)
            if y_span > 1e-9 * y_scale_ref:
                non_flat_count += 1
    if multi_point_count > 0 and non_flat_count == 0:
        raise FigureError(
            f"figure '{fig_id}': all {multi_point_count} series have near-zero variance across the x-range "
            f"(flat horizontal line). This repeats the Test 5 'near-blank curve' failure mode. "
            f"Plot a physical quantity that genuinely varies with x, or declare constant reference bounds in 'thresholds'."
        )
    if y_scale == "linear" and len(all_finite_y) >= 6:
        pos_y = [v for v in all_finite_y if v > 0]
        if len(pos_y) == len(all_finite_y):
            lo, hi = min(pos_y), max(pos_y)
            if lo > 0 and (hi / lo) > 50.0:
                threshold_10pct = lo + 0.10 * (hi - lo)
                compressed_frac = sum(1 for v in pos_y if v <= threshold_10pct) / len(pos_y)
                if compressed_frac >= 0.75:
                    footnotes.append(
                        f"提示：纵轴正值跨度达 {hi/lo:.1f} 倍且 {int(compressed_frac*100)}% 的数据点集中在低值区，"
                        "若需观察低值区细节可设置 axes.y.scale='log'。"
                    )


def _draw_1d(fig_spec, fig_id):
    kind = fig_spec.get("kind", "curve")
    series = fig_spec.get("series") or []
    # kind 'interval_highlight' is a legitimate background-band-only figure:
    # it draws `highlights` with zero data series. Every other kind requires at
    # least one series with points.
    if not series and kind not in ("interval_highlight",):
        raise FigureError(f"figure '{fig_id}': kind '{kind}' requires at least one series with points.")

    x_names = [s.get("name") or "" for s in series]
    y_names = [s.get("name") or "" for s in series]
    xlabel = _axis_label(fig_spec, "x", x_names)
    ylabel = _axis_label(fig_spec, "y", y_names)

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    footnotes = []
    n_nan_total = 0
    n_inf_total = 0

    x_scale = _axis_scale(fig_spec, "x")
    y_scale = _axis_scale(fig_spec, "y")
    for scale, axis_name in ((x_scale, "x"), (y_scale, "y")):
        if scale not in ("linear", "log"):
            raise FigureError(
                f"figure '{fig_id}': axes.{axis_name}.scale={scale!r} is not 'linear' or 'log'.")

    for s in series:
        points = s.get("points") or {}
        x = points.get("x") or []
        y = points.get("y") or []
        _require_same_len(s.get("name") or "(unnamed series)", x, y)
        nn, ni = _finite_counts(x + y)
        n_nan_total += nn
        n_inf_total += ni

        role = s.get("role")
        style = ROLE_STYLE.get(role, DEFAULT_ROLE_STYLE) if role else DEFAULT_ROLE_STYLE
        kind_hint = s.get("kind_hint")

        if kind == "scatter" or kind_hint == "scatter":
            # Overlap-visibility jitter: only when two or more points share an
            # identical (x, y) coordinate, and only on the copy drawn to screen.
            key_counts = {}
            for a, b in zip(x, y):
                key_counts[(a, b)] = key_counts.get((a, b), 0) + 1
            dup = any(c > 1 for c in key_counts.values())
            xs = list(x)
            ys = list(y)
            if dup:
                n_dup = sum(c - 1 for c in key_counts.values() if c > 1)
                step = 0.02 * (max(map(abs, x), default=1) or 1)
                offset = 0
                for i in range(len(xs)):
                    if key_counts.get((xs[i], ys[i]), 0) > 1:
                        xs[i] = xs[i] + (step * offset % 3 - 1) * 0.5
                        ys[i] = ys[i] + (step * (offset + 1) % 3 - 1) * 0.5
                        offset += 1
                footnotes.append(
                    f"部分 (x, y) 点完全重合（共 {n_dup} 个重复点），"
                    f"画面上施加了定幅可视抖动（仅屏幕层面，原始数值未改动）。"+
                    f"[系列: {s.get('name') or ''}]")
            err_y = s.get("y_err")
            if err_y is not None:
                _require_same_len((s.get("name") or "") + ".y_err", x, err_y)
                ax.errorbar(xs, ys, yerr=err_y, fmt="none", ecolor=style.get("color", "0.3"),
                            label=s.get("name") or "", capsize=4)
            else:
                ax.scatter(xs, ys, marker=style.get("marker", "o"),
                           color=style.get("color", "none"), label=s.get("name") or "")
        elif kind == "error_bar" and s.get("y_err") is not None:
            err_y = s.get("y_err")
            _require_same_len((s.get("name") or "") + ".y_err", x, err_y)
            ax.errorbar(x, y, yerr=err_y, fmt=style.get("linestyle", "-") + "o",
                       color=style.get("color", "0.2"), label=s.get("name") or "", capsize=4)
        elif kind == "error_bar" and s.get("y_err") is None:
            footnotes.append(
                f"系列「{s.get('name') or ''}」声明为 error_bar 但未提供 y_err；"
                f"按普通折线绘制（不画误差棒），已在图注中明确标出，未静默当作有误差棒。")
            ax.plot(x, y, style.get("linestyle", "-"), color=style.get("color", "0.2"),
                    label=s.get("name") or "")
        else:
            # Marker policy: for small point counts, mark every point (so a
            # 4-point curve is not misleadingly drawn with just 1 visible
            # marker, which was a real regression bug in the earlier
            # `markevery=len(x)` version — that formula means "every len(x)-th
            # point starting at index 0", i.e. exactly one marker per series
            # whenever len(x) >= 2). For larger point counts, drop markers
            # entirely to avoid a wall of overlapping dots on a dense line.
            use_markers = style.get("marker") if len(x) <= 12 else None
            line, = ax.plot(x, y, style.get("linestyle", "-"), color=style.get("color", None),
                            label=s.get("name") or "", marker=use_markers,
                            markevery=1 if use_markers else None)
            if kind_hint == "line_scatter" and s.get("y_err") is not None:
                err_y = s.get("y_err")
                _require_same_len((s.get("name") or "") + ".y_err", x, err_y)
                ax.errorbar(x, y, yerr=err_y, fmt="none", ecolor=style.get("color", "0.3"), capsize=4)

    for hl in fig_spec.get("highlights") or []:
        ax.axvspan(hl.get("x0"), hl.get("x1"), alpha=0.15, color="orange",
                   label=hl.get("label") or f"[{hl.get('x0')}..{hl.get('x1')}]")

    for mk in fig_spec.get("markers") or []:
        ax.plot([mk.get("x")], [mk.get("y")], marker="x", color="k", markersize=8,
                label=mk.get("label") or f"({mk.get('x')}, {mk.get('y')})")

    _check_degeneracy_and_scale(
        series, fig_id, y_scale, footnotes, allow_constant=bool(fig_spec.get("allow_constant", False))
    )

    # Axis limits: include every finite data point across all series; never
    # silently crop. (NaN/Inf points are skipped by matplotlib itself.)
    all_x = [v for s in series for v in (s.get("points") or {}).get("x", [])]
    all_y = [v for s in series for v in (s.get("points") or {}).get("y", [])]
    _draw_thresholds(ax, fig_spec, all_x, all_y)
    _apply_scientific_axes_style(ax)
    # A background-band-only figure (kind='interval_highlight' with no data
    # series) still needs an x-axis range — derive it from the highlight bands
    # themselves, not from (nonexistent) data points.
    for hl in fig_spec.get("highlights") or []:
        for v in (hl.get("x0"), hl.get("x1")):
            if isinstance(v, (int, float)) and math.isfinite(v):
                all_x.append(v)
    finite_x = [v for v in all_x if isinstance(v, (int, float)) and math.isfinite(v)]
    finite_y = [v for v in all_y if isinstance(v, (int, float)) and math.isfinite(v)]
    if not finite_x and not finite_y:
        raise FigureError(
            f"figure '{fig_id}': no finite x or y data points across any series, and no "
            f"finite highlight range to anchor the axes to — nothing to draw; refusing "
            f"to render an empty/blank plot as if it were a result.")
    if finite_x:
        lo, hi = min(finite_x), max(finite_x)
        pad = (hi - lo) * 0.05 or 1.0
        ax.set_xlim(lo - pad, hi + pad)
    if finite_y:
        lo, hi = min(finite_y), max(finite_y)
        pad = (hi - lo) * 0.05 or 1.0
        ax.set_ylim(lo - pad, hi + pad)

    # Log-scale support: applied only to numeric axes (i.e. after the limits
    # above have already confirmed this axis is carrying real numeric data,
    # not a categorical heatmap's label list — those branches never reach this
    # point). A log axis with any non-positive data point is a real data
    # problem, not a presentation detail: matplotlib's default behavior is
    # to silently skip non-positive points, which would hide the problem — so
    # count them up front and footnote it, exactly like the NaN/Inf case.
    if x_scale == "log":
        ax.set_xscale("log")
        n_x_nonpos = _count_nonpositive(all_x)
        if n_x_nonpos:
            footnotes.append(
                f"x 轴为对数刻度，共 {n_x_nonpos} 个 x 值 <= 0，log 轴下无法绘制，"
                f"已按 matplotlib 默认行为处理（这些点被跳过/截断，视版本而定），"
                f"本脚本未擅自把它们截断成正值——此脚注即为该处理的唯一记录。")
    if y_scale == "log":
        ax.set_yscale("log")
        n_y_nonpos = _count_nonpositive(all_y)
        if n_y_nonpos:
            footnotes.append(
                f"y 轴为对数刻度，共 {n_y_nonpos} 个 y 值 <= 0，log 轴下无法绘制，"
                f"已按 matplotlib 默认行为处理（这些点被跳过/截断，视版本而定），"
                f"本脚本未擅自把它们截断成正值——此脚注即为该处理的唯一记录。")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    title = fig_spec.get("title")
    if title:
        import textwrap
        # Wrap long titles at a conservative budget so they never overflow the
        # figure's top edge; deterministic character budget, not content-adaptive.
        wrapped_title = textwrap.fill(title, width=38)
        ax.set_title(wrapped_title)
    else:
        ax.set_title("（无标题）")
    if any(s.get("name") for s in series) or fig_spec.get("highlights") or fig_spec.get("markers"):
        legend_pos = fig_spec.get("legend_position", "auto")
        if legend_pos == "outside" or (legend_pos == "auto" and len(series) >= 3):
            # Zero-occlusion rule: move legend to dedicated outside margin when >= 3 series
            ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0, frameon=True)
        else:
            ax.legend(loc=legend_pos if legend_pos != "auto" else "best")
    if n_nan_total or n_inf_total:
        footnotes.append(
            f"共 {n_nan_total} 个 NaN、{n_inf_total} 个 Inf 值（横跨所有系列）；"
            f"按 matplotlib 默认行为处理（跳过/截断），本脚本未擅自修补——"
            f"此脚注即为该处理的唯一记录。")
    if footnotes:
        # Footnotes must stay ON the canvas — never let a long note silently
        # run past the figure edge. Wrap at a fixed character budget, and if the
        # resulting multiline block still overflows the axes bottom (very long
        # note + small figure), shrink the font size deterministically until it
        # fits; this is a presentation-layer accommodation, not a data change.
        import textwrap
        def _fits_and_wrap(text, fontsize):
            # Approximate how many characters fit on one line of the axes at this
            # font size. The axes region is roughly figsize-width-inches * dpi
            # pixels wide minus margins; assume ~55%-70% of that width is
            # available to a footnote, and a CJK glyph at fontsize 7 is roughly
            # 7*0.9 dpi-ish pixels wide (heuristic, conservative).
            axes_w_px = fig.get_figwidth() * fig.dpi * 0.6
            chars_per_line = max(20, int(axes_w_px / max(fontsize * 0.55, 4)))
            return textwrap.fill(text, width=chars_per_line)

        fontsize = 7
        wrapped = "\n".join(_fits_and_wrap(t, fontsize) for t in footnotes)
        txt_obj = ax.text(0.01, 0.01, wrapped, transform=ax.transAxes, fontsize=fontsize,
                          va="bottom", ha="left", color="0.4")
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bb = txt_obj.get_window_extent(renderer)
        ax_bb = ax.get_window_extent(renderer)
        # Iteratively shrink the font (deterministic, not content-adapting) until
        # the footnote block no longer pokes above the axes area or runs past the
        # right edge. Bounded below at fontsize=5 so this loop always terminates.
        guard = 0
        while (bb.x1 > ax_bb.x1 + 1 or bb.y0 < ax_bb.y0 - 1) and fontsize > 5 and guard < 8:
            fontsize -= 1
            wrapped = "\n".join(_fits_and_wrap(t, fontsize) for t in footnotes)
            txt_obj.set_text(wrapped)
            txt_obj.set_fontsize(fontsize)
            fig.canvas.draw()
            bb = txt_obj.get_window_extent(renderer)
            guard += 1

    fig.tight_layout()
    return fig


def _draw_boxplot(fig_spec, fig_id):
    """kind='boxplot': a distribution-comparison figure — each series is one
    category (x-axis position) carrying a list of y values (NOT an x/y
    paired sequence, which is what the other 4 kinds use; this is a genuine
    'category x distribution' 2D structure that none of the existing kinds
    can express). matplotlib's native boxplot is used — no seaborn dependency
    is required; seaborn, if installed, is simply an optional nicer-looking
    restyle, not a hard requirement of this kind."""
    series = fig_spec.get("series") or []
    if not series:
        raise FigureError(f"figure '{fig_id}': kind 'boxplot' requires at least one series.")

    categories = []
    all_values = []
    n_nan_total = 0
    n_inf_total = 0
    n_nonpositive_if_log = 0
    for s in series:
        name = s.get("name")
        values = s.get("values")
        if not name or values is None:
            raise FigureError(
                f"figure '{fig_id}': boxplot series require both 'name' (the category label) "
                f"and 'values' (a list of y values for that category); got "
                f"name={name!r}, values={'present' if values is not None else 'missing'} — "
                f"boxplot is category->value-list, not x/y-paired points.")
        if not isinstance(values, (list, tuple)) or not all(
                isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            raise FigureError(
                f"figure '{fig_id}': boxplot series '{name}' .values must be a flat list of "
                f"numbers; refusing to draw (no silent string/None coercion).")
        if not values:
            raise FigureError(
                f"figure '{fig_id}': boxplot series '{name}' .values is an empty list; "
                f"refusing to draw 2 categories and silently pretend this one doesn't exist "
                f"— an empty category is a data error upstream, not a rendering detail "
                f"this script may paper over.")
        nn, ni = _finite_counts(list(values))
        n_nan_total += nn
        n_inf_total += ni
        categories.append(name)
        all_values.append(values)

    x_scale = _axis_scale(fig_spec, "x")
    y_scale = _axis_scale(fig_spec, "y")
    if x_scale != "linear":
        raise FigureError(
            f"figure '{fig_id}': boxplot x axis is a categorical category position "
            f"(1-indexed slot per series); 'log' (or any non-'linear' scale) is not "
            f"meaningful for it. Only the y axis supports scale='log'.")

    axes = fig_spec.get("axes") or {}
    xlabel = (axes.get("x") or {}).get("label") or ""
    ylabel = (axes.get("y") or {}).get("label") or ""

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    import matplotlib as _mpl
    _mpl_version = tuple(int(p) for p in _mpl.__version__.split(".")[:2])
    if _mpl_version >= (3, 9):
        # 'labels' was renamed to 'tick_labels' in matplotlib 3.9 (kept as a
        # deprecated alias through 3.11, removed after).
        bxp = ax.boxplot(all_values, tick_labels=categories, patch_artist=True)
    else:
        bxp = ax.boxplot(all_values, labels=categories, patch_artist=True)
    if y_scale == "log":
        ax.set_yscale("log")
        for values in all_values:
            n_nonpositive_if_log += sum(1 for v in values
                                        if isinstance(v, (int, float)) and not (math.isnan(v) or math.isinf(v)) and v <= 0)

    if n_nan_total or n_inf_total:
        footnotes = [f"共 {n_nan_total} 个 NaN、{n_inf_total} 个 Inf 值（横跨所有类别的取值）；"
                     f"已按 matplotlib 默认行为处理（这些值不会参与分位数计算），本脚本未擅自剔除——"
                     f"此脚注即为该处理的唯一记录。"]
    else:
        footnotes = []
    if y_scale == "log" and n_nonpositive_if_log:
        footnotes.append(
            f"y 轴为对数刻度，共 {n_nonpositive_if_log} 个取值 <= 0，log 轴下无法参与绘制，"
            f"已按 matplotlib 默认行为处理，本脚本未擅自把它们截断成正值——此脚注即为该处理的唯一记录。")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    title = fig_spec.get("title")
    if title:
        import textwrap
        ax.set_title(textwrap.fill(title, width=38))
    else:
        ax.set_title("（无标题）")

    if footnotes:
        # Same overflow-safe wrapping as _draw_1d (reuse the same helper-free
        # approach rather than extracting it, to keep this diff narrow).
        import textwrap as _textwrap
        def _fits_and_wrap(text, fontsize):
            axes_w_px = fig.get_figwidth() * fig.dpi * 0.6
            chars_per_line = max(20, int(axes_w_px / max(fontsize * 0.55, 4)))
            return _textwrap.fill(text, width=chars_per_line)
        fontsize = 7
        wrapped = "\n".join(_fits_and_wrap(t, fontsize) for t in footnotes)
        txt_obj = ax.text(0.01, 0.01, wrapped, transform=ax.transAxes, fontsize=fontsize,
                          va="bottom", ha="left", color="0.4")
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bb = txt_obj.get_window_extent(renderer)
        ax_bb = ax.get_window_extent(renderer)
        guard = 0
        while (bb.x1 > ax_bb.x1 + 1 or bb.y0 < ax_bb.y0 - 1) and fontsize > 5 and guard < 8:
            fontsize -= 1
            wrapped = "\n".join(_fits_and_wrap(t, fontsize) for t in footnotes)
            txt_obj.set_text(wrapped)
            txt_obj.set_fontsize(fontsize)
            fig.canvas.draw()
            bb = txt_obj.get_window_extent(renderer)
            guard += 1

    fig.tight_layout()
    return fig


def _draw_heatmap(fig_spec, fig_id):
    series = fig_spec.get("series") or []
    grid = None
    for s in series:
        if s.get("grid"):
            grid = s["grid"]
            break
    if not grid:
        raise FigureError(f"figure '{fig_id}': kind 'heatmap' requires one series carrying a 'grid' field.")
    xv = grid.get("x_values") or []
    yv = grid.get("y_values") or []
    vals = grid.get("values_2d") or []
    if not xv or not yv or not vals:
        raise FigureError(f"figure '{fig_id}': heatmap grid missing x_values/y_values/values_2d.")
    if len(vals) != len(yv) or any(len(row) != len(xv) for row in vals):
        raise FigureError(
            f"figure '{fig_id}': heatmap values_2d is {len(vals)} rows x "
            f"{(len(vals[0]) if vals else 0)} cols, but the convention is "
            f"values_2d[i][j] = value at (x_values[j], y_values[i]) — i.e. "
            f"rows must match y_values ({len(yv)}) and columns must match "
            f"x_values ({len(xv)}). Refusing to draw (no silent padding/transposition)."
        )
    x_scale = _axis_scale(fig_spec, "x")
    y_scale = _axis_scale(fig_spec, "y")
    for scale, axis_name in ((x_scale, "x"), (y_scale, "y")):
        if scale not in ("linear", "log"):
            raise FigureError(
                f"figure '{fig_id}': axes.{axis_name}.scale={scale!r} is not 'linear' or 'log'.")

    axes = fig_spec.get("axes") or {}
    xlabel = (axes.get("x") or {}).get("label") or "x"
    ylabel = (axes.get("y") or {}).get("label") or "y"
    zlabel = (axes.get("z") or {}).get("label") or ""

    import numpy as np
    import matplotlib.colors as mcolors
    arr = np.array([[v if isinstance(v, (int, float)) and math.isfinite(v) else np.nan for v in row] for row in vals], dtype=float)

    def _is_numeric(values):
        return all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values)

    x_numeric = _is_numeric(xv)
    y_numeric = _is_numeric(yv)

    fig, ax = plt.subplots(figsize=(7.4, 5.2), dpi=150)
    style = fig_spec.get("heatmap_style", "pcolormesh")

    # Colormap and Normalization determination
    explicit_cmap = fig_spec.get("cmap")
    is_diverging = bool(fig_spec.get("diverging") or fig_spec.get("cmap_type") == "diverging")
    finite_vals = arr[np.isfinite(arr)]
    has_finite = len(finite_vals) > 0
    vmin = float(np.min(finite_vals)) if has_finite else 0.0
    vmax = float(np.max(finite_vals)) if has_finite else 1.0

    if not explicit_cmap and (is_diverging or (vmin < -1e-6 and vmax > 1e-6)):
        cmap = "coolwarm"
        is_diverging = True
    elif explicit_cmap:
        cmap = explicit_cmap
    else:
        cmap = "viridis"

    # Norm handling (LogNorm vs TwoSlopeNorm vs Linear)
    z_scale = ((fig_spec.get("axes") or {}).get("z") or {}).get("scale", "linear")
    req_log = fig_spec.get("norm") == "log" or z_scale == "log"
    norm = None
    if req_log and has_finite:
        pos_vals = finite_vals[finite_vals > 0]
        if len(pos_vals) == 0:
            raise FigureError(
                f"figure '{fig_id}': norm='log' requested for heatmap, but all values are <= 0. "
                f"Logarithmic color scaling requires strictly positive data.")
        log_vmin = float(np.min(pos_vals))
        norm = mcolors.LogNorm(vmin=log_vmin, vmax=max(vmax, log_vmin * 10))
    elif is_diverging and has_finite and vmin < 0 < vmax:
        norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)

    if x_numeric and y_numeric:
        X, Y = np.meshgrid(xv, yv)
        if x_scale == "log":
            ax.set_xscale("log")
        if y_scale == "log":
            ax.set_yscale("log")
        if style == "contourf":
            levels = int(fig_spec.get("levels", 14))
            cs = ax.contourf(X, Y, arr, levels=levels, cmap=cmap, norm=norm)
            if fig_spec.get("contour_lines", True):
                clines = ax.contour(X, Y, arr, levels=levels, colors="white", alpha=0.35, linewidths=0.7, norm=norm)
                if fig_spec.get("contour_labels", True):
                    try:
                        ax.clabel(clines, inline=True, fontsize=7.5, fmt="%g")
                    except Exception:
                        pass
        else:
            im = ax.pcolormesh(X, Y, arr, cmap=cmap, norm=norm, shading="auto")
            cs = im
    else:
        # Categorical axis (e.g. feature names, country names, lat/lon index labels)
        if x_scale == "log" and not x_numeric:
            raise FigureError(
                f"figure '{fig_id}': axes.x.scale='log' is not meaningful for a categorical "
                f"x axis (x_values are non-numeric labels); 'log' scale requires numeric "
                f"x_values. Use scale='linear' (the default) for categorical axes.")
        if y_scale == "log" and not y_numeric:
            raise FigureError(
                f"figure '{fig_id}': axes.y.scale='log' is not meaningful for a categorical "
                f"y axis (y_values are non-numeric labels); 'log' scale requires numeric "
                f"y_values. Use scale='linear' (the default) for categorical axes.")
        if style == "contourf":
            raise FigureError(
                f"figure '{fig_id}': kind 'heatmap' with heatmap_style='contourf' requires "
                f"numeric x_values/y_values (contourf needs coordinates); got categorical "
                f"labels. Use 'pcolormesh' style for categorical axes.")
        im = ax.imshow(arr.T, cmap=cmap, norm=norm, origin="lower", aspect="auto")
        cs = im
        ax.set_xticks(range(len(xv)))
        ax.set_xticklabels([str(v) for v in xv], rotation=45, ha="right")
        ax.set_yticks(range(len(yv)))
        ax.set_yticklabels([str(v) for v in yv])

        # Cell value annotation (annot=True)
        if fig_spec.get("annot"):
            annot_fmt = fig_spec.get("annot_fmt", ".2f")
            cmap_obj = plt.get_cmap(cmap)
            norm_obj = norm or mcolors.Normalize(vmin=vmin, vmax=vmax)
            for j in range(len(yv)):
                for i in range(len(xv)):
                    val = arr[j][i]
                    if not math.isfinite(val):
                        continue
                    try:
                        t_str = f"{val:{annot_fmt}}"
                    except Exception:
                        t_str = str(val)
                    # Compute perceived luminance for text contrast
                    rgba = cmap_obj(norm_obj(val))
                    lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                    t_color = "#0f172a" if lum > 0.55 else "#f8fafc"
                    ax.text(i, j, t_str, ha="center", va="center", color=t_color, fontsize=8, fontweight="500")

    cbar = fig.colorbar(cs, ax=ax)
    if zlabel:
        cbar.set_label(zlabel)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    title = fig_spec.get("title")
    if title:
        import textwrap
        ax.set_title(textwrap.fill(title, width=38))
    else:
        ax.set_title("（无标题）")
    fig.tight_layout()
    return fig


def _draw_bar(fig_spec, fig_id):
    """kind='bar': grouped categorical comparison bar chart with value labels and thresholds."""
    series = fig_spec.get("series") or []
    categories = fig_spec.get("categories") or []
    if not series:
        raise FigureError(f"figure '{fig_id}': kind 'bar' requires at least one series.")
    if not categories and series[0].get("points"):
        categories = [str(x) for x in (series[0]["points"].get("x") or [])]
    if not categories:
        raise FigureError(f"figure '{fig_id}': kind 'bar' requires 'categories' (list of category names).")

    import numpy as np
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=150)
    x_idx = np.arange(len(categories))
    n_ser = len(series)
    width = min(0.75 / max(n_ser, 1), 0.38)
    palette = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
    all_y = [0.0]

    for i, s in enumerate(series):
        vals = s.get("values")
        if vals is None and s.get("points"):
            vals = s["points"].get("y")
        if not vals or len(vals) != len(categories):
            raise FigureError(
                f"figure '{fig_id}': bar series '{s.get('name')}' length does not match categories ({len(categories)})."
            )
        all_y.extend([v for v in vals if isinstance(v, (int, float)) and math.isfinite(v)])
        offset = (i - (n_ser - 1) / 2.0) * width
        bars = ax.bar(
            x_idx + offset,
            vals,
            width=width * 0.92,
            label=s.get("name") or f"系列 {i+1}",
            color=s.get("color") or palette[i % len(palette)],
            edgecolor="#1e293b",
            linewidth=0.6,
            zorder=3,
        )
        for rect, val in zip(bars, vals):
            if isinstance(val, (int, float)) and math.isfinite(val):
                ax.annotate(
                    f"{val:.2f}" if abs(val) < 100 else f"{val:.1f}",
                    xy=(rect.get_x() + rect.get_width() / 2.0, rect.get_height()),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                )

    _draw_thresholds(ax, fig_spec, [], all_y)
    _apply_scientific_axes_style(ax)
    ax.set_xticks(x_idx)
    ax.set_xticklabels([str(c) for c in categories])
    axes = fig_spec.get("axes") or {}
    ax.set_xlabel((axes.get("x") or {}).get("label") or "")
    ax.set_ylabel((axes.get("y") or {}).get("label") or "")
    if all_y:
        lo, hi = min(all_y), max(all_y)
        ax.set_ylim(min(0.0, lo * 1.1), hi * 1.16 if hi > 0 else 1.0)
    title = fig_spec.get("title") or "（无标题）"
    import textwrap
    ax.set_title(textwrap.fill(title, width=38))
    if n_ser > 1 or fig_spec.get("thresholds"):
        legend_pos = fig_spec.get("legend_position", "auto")
        if legend_pos == "outside" or (legend_pos == "auto" and n_ser >= 3):
            ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0, frameon=True)
        else:
            ax.legend(loc=legend_pos if legend_pos != "auto" else "best")
    fig.tight_layout()
    return fig


def _draw_3d_curve(fig_spec, fig_id):
    """kind='3d_curve': 3D spatial trajectories (orbital mechanics, 3D ballistics, particle beams)."""
    series = fig_spec.get("series") or []
    if not series:
        raise FigureError(f"figure '{fig_id}': kind '3d_curve' requires at least one series.")

    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    fig = plt.figure(figsize=(7.6, 5.8), dpi=150)
    ax = fig.add_subplot(111, projection="3d")

    axes = fig_spec.get("axes") or {}
    xlabel = (axes.get("x") or {}).get("label") or "x"
    ylabel = (axes.get("y") or {}).get("label") or "y"
    zlabel = (axes.get("z") or {}).get("label") or "z"

    all_z = []
    palette = ["#38bdf8", "#10b981", "#ef4444", "#f59e0b", "#a855f7", "#ec4899"]
    ground_proj = bool(fig_spec.get("ground_projection", False))

    for idx, s in enumerate(series):
        name = s.get("name") or f"轨迹 {idx+1}"
        pts = s.get("points") or {}
        x = pts.get("x") or []
        y = pts.get("y") or []
        z = pts.get("z") or []
        if not x or not y or not z:
            raise FigureError(f"figure '{fig_id}': series '{name}' in '3d_curve' requires non-empty x, y, and z.")
        _require_same_len(name, x, y)
        _require_same_len(name + ".z", x, z)

        color = s.get("color") or palette[idx % len(palette)]
        lw = float(s.get("linewidth") or 2.2)
        ax.plot(x, y, z, label=name, color=color, linewidth=lw, zorder=4)

        all_z.extend([val for val in z if isinstance(val, (int, float)) and math.isfinite(val)])

    # Optional ground projection on z_min plane for 3D depth perception
    if ground_proj and all_z:
        z_floor = float(min(all_z))
        for idx, s in enumerate(series):
            pts = s.get("points") or {}
            x = pts.get("x") or []
            y = pts.get("y") or []
            color = s.get("color") or palette[idx % len(palette)]
            ax.plot(x, y, [z_floor] * len(x), color=color, alpha=0.25, linewidth=1.2, linestyle="--", zorder=2)

    ax.set_xlabel(xlabel, labelpad=8)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.set_zlabel(zlabel, labelpad=8)

    # Configurable viewing angle (elev, azim)
    view = fig_spec.get("view") or {}
    elev = float(view.get("elev", 26.0))
    azim = float(view.get("azim", -60.0))
    ax.view_init(elev=elev, azim=azim)

    title = fig_spec.get("title") or "（无标题）"
    import textwrap
    ax.set_title(textwrap.fill(title, width=38), pad=14)

    # Zero-occlusion rule: external legend placement
    if any(s.get("name") for s in series):
        ax.legend(bbox_to_anchor=(1.04, 0.95), loc="upper left", borderaxespad=0, frameon=True)

    fig.tight_layout()
    return fig


def _draw_3d_surface(fig_spec, fig_id):
    """kind='3d_surface': 3D scalar potential surfaces, height fields, or energy landscapes z = f(x, y)."""
    series = fig_spec.get("series") or []
    grid = None
    for s in series:
        if s.get("grid"):
            grid = s["grid"]
            break
    if not grid:
        raise FigureError(f"figure '{fig_id}': kind '3d_surface' requires one series carrying a 'grid' field.")
    xv = grid.get("x_values") or []
    yv = grid.get("y_values") or []
    vals = grid.get("values_2d") or []
    if not xv or not yv or not vals:
        raise FigureError(f"figure '{fig_id}': 3d_surface grid missing x_values/y_values/values_2d.")
    if len(vals) != len(yv) or any(len(row) != len(xv) for row in vals):
        raise FigureError(
            f"figure '{fig_id}': 3d_surface values_2d must have {len(yv)} rows matching y_values "
            f"and {len(xv)} columns matching x_values."
        )

    import numpy as np
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    arr = np.array([[v if isinstance(v, (int, float)) and math.isfinite(v) else np.nan for v in row] for row in vals], dtype=float)

    X, Y = np.meshgrid(xv, yv)
    fig = plt.figure(figsize=(7.8, 5.8), dpi=150)
    ax = fig.add_subplot(111, projection="3d")

    axes = fig_spec.get("axes") or {}
    xlabel = (axes.get("x") or {}).get("label") or "x"
    ylabel = (axes.get("y") or {}).get("label") or "y"
    zlabel = (axes.get("z") or {}).get("label") or "z"

    cmap = fig_spec.get("cmap", "viridis")
    surf = ax.plot_surface(X, Y, arr, cmap=cmap, edgecolor="none", alpha=0.88, antialiased=True)

    # Optional bottom contour projection
    if fig_spec.get("bottom_contour", True):
        finite_vals = arr[np.isfinite(arr)]
        if len(finite_vals) > 0:
            z_offset = float(np.min(finite_vals))
            ax.contour(X, Y, arr, zdir="z", offset=z_offset, cmap=cmap, alpha=0.45, linewidths=0.8)

    ax.set_xlabel(xlabel, labelpad=8)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.set_zlabel(zlabel, labelpad=8)

    view = fig_spec.get("view") or {}
    elev = float(view.get("elev", 30.0))
    azim = float(view.get("azim", -55.0))
    ax.view_init(elev=elev, azim=azim)

    cbar = fig.colorbar(surf, ax=ax, shrink=0.65, aspect=14, pad=0.1)
    if zlabel:
        cbar.set_label(zlabel)

    title = fig_spec.get("title") or "（无标题）"
    import textwrap
    ax.set_title(textwrap.fill(title, width=38), pad=14)

    fig.tight_layout()
    return fig


def render_all(figures, out_dir, fmt):
    """Draw every figure in `figures`, independently."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    errors = []
    for fig_id, spec in figures.items():
        kind = spec.get("kind", "curve")
        try:
            if kind == "interactive":
                out = _render_interactive(spec, fig_id, out_dir)
                written.append(out)
                continue
            if kind == "interactive_live":
                out = _render_interactive_live(spec, fig_id, out_dir)
                written.append(out)
                continue
            if kind == "heatmap":
                fig = _draw_heatmap(spec, fig_id)
            elif kind == "boxplot":
                fig = _draw_boxplot(spec, fig_id)
            elif kind == "bar":
                fig = _draw_bar(spec, fig_id)
            elif kind == "3d_curve":
                fig = _draw_3d_curve(spec, fig_id)
            elif kind == "3d_surface":
                fig = _draw_3d_surface(spec, fig_id)
            else:
                fig = _draw_1d(spec, fig_id)
            out = os.path.join(out_dir, f"{fig_id}.{fmt}")
            fig.savefig(out)
            plt.close(fig)
            written.append(out)
        except FigureError as e:
            plt.close("all")
            errors.append(str(e))
    if errors:
        msg = "\n".join(errors)
        raise FigureError(
            f"{len(errors)} of {len(figures)} figure(s) failed to draw; "
            f"{len(written)} succeeded and were written despite this:\n{msg}\n"
            f"Fix the failing figures upstream and re-run; the successful ones above "
            f"are not invalidated by their siblings' errors."
        )
    return written


def _render_interactive(spec, fig_id, out_dir):
    """kind=='interactive' — an OPTIONAL, on-demand branch (not the default
    path; the six static kinds above stay matplotlib-only and are not touched
    by this). Renders a self-contained HTML fragment (Plotly, inline
    plotly.js, no external CDN) that Node 4 inlines directly instead of via
    a base64 <img>. See dev-notes/interactive_figure_design.md §2 for the
    exact schema (backend/layout_3d/switcher fields) and §1 for the hard
    boundary: this branch can only switch between ALREADY-COMPUTED series
    (no live re-solve of the underlying ODE/model — that is not what a
    static HTML fragment can do, and pretending it could would be the exact
    failure mode this project's 'no silent paper-over' rule forbids). If
    the user genuinely needs to drag a parameter and watch the curve
    re-draw in real time, use kind 'interactive_live' instead (the only
    case where that is achievable in a pure static export: when the
    underlying model is a cheap closed-form expression that can be mirrored
    in client-side JS — see _render_interactive_live's docstring for the
    exact boundary and the security notes on the JS sandbox).

    plotly is imported lazily here (not at module top-level) so a task that
    only ever uses the six static kinds never needs plotly installed at all.
    """
    try:
        import plotly.graph_objects as go
        import plotly.io
    except ModuleNotFoundError:
        raise FigureError(
            f"figure '{fig_id}': kind 'interactive' requires the 'plotly' package "
            f"(pip install plotly), which is not installed in this environment. "
            f"This is a hard dependency for this kind only — the six static kinds "
            f"(curve/scatter/error_bar/interval_highlight/heatmap/boxplot) do NOT "
            f"need plotly and still work without it; only 'interactive'/'interactive_live' "
            f"figures require it. Do not mark this figure as drawn: stop and either "
            f"(A) install plotly and re-run, or (B) drop this interactive figure "
            f"and fall back to a static kind for the same data, if the user's "
            f"tolerance allows a non-interactive presentation.")

    series = spec.get("series") or []
    if not series:
        raise FigureError(f"figure '{fig_id}': kind 'interactive' requires at least one series (pre-computed data points to display/switch between).")

    backend = spec.get("backend", "plotly")
    if backend != "plotly":
        raise FigureError(
            f"figure '{fig_id}': kind 'interactive' backend={backend!r} is not supported; "
            f"only 'plotly' is implemented (see dev-notes/interactive_figure_design.md §1 "
            f"for why Bokeh/others are not parallel-implemented now).")

    layout_3d = bool(spec.get("layout_3d", False))
    title = spec.get("title") or "（无标题）"

    fig = go.Figure()
    n_nan_total = 0
    n_inf_total = 0
    for s in series:
        name = s.get("name") or "(unnamed series)"
        points = s.get("points") or {}
        x = points.get("x") or []
        y = points.get("y") or []
        _require_same_len(name, x, y)
        nn, ni = _finite_counts(x + y)
        n_nan_total += nn
        n_inf_total += ni

        if layout_3d:
            z = s.get("z")
            if z is None:
                raise FigureError(
                    f"figure '{fig_id}': layout_3d=true but series '{name}' has no 'z' field "
                    f"(3D rendering requires x, y AND z per point, same-length). Refusing to "
                    f"draw a 2D-only series into a 3D layout — do not silently drop the z "
                    f"dimension; supply real z values upstream.")
            _require_same_len(name + ".z", x, z)
            nnz, niz = _finite_counts(z)
            n_nan_total += nnz
            n_inf_total += niz
            fig.add_scatter3d(x=x, y=y, z=z, mode="lines+markers", name=name)
        else:
            fig.add_scatter(x=x, y=y, mode="lines+markers", name=name)

    # Optional switcher: toggle visibility between the pre-computed series via
    # Updatemenu buttons (method='restyle', the dict-form that works on static
    # to_html export — verified directly; the Python-side `visible=[..]`
    # short-form documented in older plotly examples does NOT work on
    # plotly 7.x's updatemenu.button schema, confirmed by direct test).
    switcher = spec.get("switcher")
    if switcher and len(series) >= 2:
        buttons = []
        for i, s in enumerate(series):
            visible = [j == i for j in range(len(series))]
            buttons.append(dict(label=s.get("name") or f"series {i+1}", method="restyle",
                                args=[["visible"], visible]))
        menu = go.layout.Updatemenu(buttons=buttons)
        fig.layout.updatemenus = [menu]
        # All series start visible=False except the first, so the switcher has
        # a definite initial state rather than overlapping every line at once.
        for i, trace in enumerate(fig.data):
            trace.visible = (i == 0)

    fig.update_layout(title=title, height=560)

    html = plotly.io.to_html(fig, include_plotlyjs="inline")
    out = os.path.join(out_dir, f"{fig_id}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    if n_nan_total or n_inf_total:
        print(f"NOTE: figure '{fig_id}' (interactive) had {n_nan_total} NaN / "
              f"{n_inf_total} Inf value(s) across its series; Plotly's default "
              f"rendering skips/handles these — not silently replaced, same "
              f"policy as the static kinds.", file=sys.stderr)
    return out


def _render_interactive_live(spec, fig_id, out_dir):
    """kind=='interactive_live' — an OPTIONAL, on-demand branch that goes
    further than the plain 'interactive' kind: instead of just switching
    between pre-computed series, it renders a 2D curve y = f(x; p) where
    `p` is a set of user-adjustable parameters (sliders), and RE-COMPUTES
    f live in the browser as the user drags any slider — GeoGebra-style
    "drag a parameter, watch the curve re-draw in real time", achieved
    with NO server, NO external CDN, NO Python-side callback: the closed-
    form function body is mirrored as inline JavaScript, evaluated fresh
    on every slider 'input' event, and pushed into the existing Plotly
    trace via Plotly.restyle().

    Only sound for cheap per-point closed-form arithmetic (sum of rational/
    trig terms, O(n*modes) loop over a handful of modes, etc.) — NOT a
    substitute for re-solving a genuine numerical ODE/PDE when a parameter
    changes. If the figure's y really depends on the parameter through a
    heavy numerical model, use 'interactive' with several pre-computed
    parameter values and a switcher instead, and say so in the title/note.
    Silently presenting a slider as if it re-solved a heavy model would be
    exactly the 'silent paper-over' this project's rules forbid; the
    optional 'live_model_note' field exists to force that distinction to be
    written down explicitly rather than assumed.

    plotly is imported lazily here, same as in _render_interactive(): a
    task that never declares an 'interactive_live' figure still never needs
    plotly installed.

    Security note (kept deliberately narrow): the JavaScript function body
    is written by the analysis agent, not arbitrary user input, and is
    scoped to one function that can only read the fixed x grid, the
    declared constants, and the current slider values — no DOM access
    outside the one Plotly div, no fetch/XMLHttpRequest, no eval, no
    network. Keep the body small and arithmetic-only (+,-,*,/,Math.pow,
    Math.sqrt, Math.abs, simple loops); do not grow this into a general
    scriptable environment.
    """
    try:
        import plotly.graph_objects as go
        import plotly.io
    except ModuleNotFoundError:
        raise FigureError(
            f"figure '{fig_id}': kind 'interactive_live' requires the 'plotly' package "
            f"(pip install plotly), which is not installed in this environment. "
            f"Same dependency rule as the plain 'interactive' kind — the six static "
            f"kinds do NOT need plotly and are unaffected.")

    x_data = spec.get("x_data")
    if not x_data or "values" not in x_data:
        raise FigureError(f"figure '{fig_id}': kind 'interactive_live' requires 'x_data': "
                          f"{{'values': [...], 'label': '...'}} (the fixed grid of x sample points "
                          f"the live function is evaluated on).")
    x_values = x_data["values"]
    x_label = x_data.get("label") or "x"
    if not x_values:
        raise FigureError(f"figure '{fig_id}': kind 'interactive_live' x_data.values must be a non-empty list.")

    params = spec.get("params") or []
    if not params:
        raise FigureError(f"figure '{fig_id}': kind 'interactive_live' requires at least one entry in 'params' "
                          f"(each: name/label/min/max/step/initial).")
    for p in params:
        for field in ("name", "min", "max", "step", "initial"):
            if field not in p:
                raise FigureError(f"figure '{fig_id}': kind 'interactive_live' param missing required field '{field}'.")
        if not (p["min"] <= p["initial"] <= p["max"]):
            raise FigureError(
                f"figure '{fig_id}': kind 'interactive_live' param '{p['name']}' initial value {p['initial']} "
                f"is outside its slider range [{p['min']}, {p['max']}] — this would start the slider at a value "
                f"it cannot legally reach; fix the range or the initial value, do not clamp silently.")

    js_fn_body = spec.get("js_function_body")
    if not js_fn_body or not isinstance(js_fn_body, str):
        raise FigureError(
            f"figure '{fig_id}': kind 'interactive_live' requires 'js_function_body' — the BODY of a JS "
            f"function (not the full 'function(P){{...}}' wrapper, which the renderer adds around it) "
            f"that returns the new y-array given the current parameter object P, e.g. "
            f"'return x.map(function(fx){{ ... closed-form eval using P.zeta, P.E ... }})' — keep it "
            f"arithmetic-only and small; see the security note in this function's docstring.")

    y_label = spec.get("y_label") or "y"
    live_model_note = spec.get("live_model_note")
    if not live_model_note:
        print(f"WARNING: figure '{fig_id}' (kind 'interactive_live') has no 'live_model_note' field explicitly stating "
              f"that this slider re-computes a cheap closed-form expression client-side, NOT a live re-solve of the "
              f"underlying numerical model — add one sentence to the figure's note/title so a reader of the rendered "
              f"HTML does not mistake this for a heavier capability than it actually is. Not a hard error, but the "
              f"silent-assumption failure mode this project forbids.", file=sys.stderr)

    title = spec.get("title") or "（无标题）"

    fig = go.Figure()
    fig.add_scatter(x=x_values, y=[0.0] * len(x_values), mode="lines", name="live curve",
                    line=dict(width=2))
    fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label, height=480)

    html = plotly.io.to_html(fig, include_plotlyjs="inline")

    div_id = "live-root-" + re.sub(r"[^A-Za-z0-9_-]", "_", fig_id)
    html = re.sub(r'<div id="plot" ', '<div id="' + div_id + '" ', html, count=1)

    constants_json = spec.get("constants") or {}

    slider_defs_lines = []
    slider_rows = []
    for p in params:
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", p["name"])
        slider_defs_lines.append(
            "  {name:" + json.dumps(p["name"]) + ", label:" + json.dumps(p.get("label", p["name"]))
            + ", min:" + json.dumps(p["min"]) + ", max:" + json.dumps(p["max"])
            + ", step:" + json.dumps(p["step"]) + ", initial:" + json.dumps(p["initial"]) + "},")
        slider_rows.append(
            f'<label style="display:inline-block;margin:4px 0">{html_lib.escape(p.get("label", p["name"]))} '
            f'<span id="{div_id}-val-{safe}">{p["initial"]}</span></label>'
            f'<input id="{div_id}-slider-{safe}" type="range" min="{p["min"]}" max="{p["max"]}" step="{p["step"]}" value="{p["initial"]}"'
            f' style="width:260px;vertical-align:middle;margin-left:6px">')
    slider_defs = "\n".join(slider_defs_lines)
    slider_block = "<br>".join(slider_rows)

    js_slider_defs = "[" + ",\n".join(
        f"    {{name: {json.dumps(p['name'])}, label: {json.dumps(p.get('label', p['name']))}, min: {json.dumps(p['min'])}, "
        f"max: {json.dumps(p['max'])}, step: {json.dumps(p['step'])}, initial: {json.dumps(p['initial'])}}}"
        for p in params) + "\n"
    js_constants = json.dumps(constants_json)
    js_x_values = json.dumps(x_values)
    js_js_fn_body = js_fn_body
    js_div_id = div_id

    # --- Optional enhancements (all backward-compatible: absent => exactly the
    # previous behavior; nothing new is forced on existing specs). Each one is a
    # general interactive-figure UX pattern learned from the reference FEM file,
    # NOT FEM-domain-specific: (1) y_range_pin keeps the y-axis from thrashing
    # as Plotly re-auto-ranges on every slider drag (the reference file's
    # autoRange temporal-smoothing pattern, generalized); (2) a live "status"
    # strip (idle / up-to-date / error + reason), not just an error-only box —
    # mirrors the reference's running/done/reason tri-state visibility; (3)
    # verify_reference: an independently-derived reference value (or a JS
    # expression for one) shown live next to the curve — the reference file's
    # "cheap analytic model as order-of-magnitude cross-check" idea, generalized
    # to our closed-form case, so the reader can see the numeric sanity check
    # on-screen, not just as a build-time diff.
    y_range_pin = spec.get("y_range_pin")
    pin_lo = pin_hi = None
    if y_range_pin is not None:
        if (not isinstance(y_range_pin, (list, tuple))) or len(y_range_pin) != 2 or \
                not all(isinstance(v, (int, float)) and v == v for v in y_range_pin) or \
                not (y_range_pin[0] < y_range_pin[1]):
            raise FigureError(
                f"figure '{fig_id}': 'y_range_pin' must be a 2-element [lo, hi] "
                f"with lo < hi (finite numbers) — got {y_range_pin!r}.")
        pin_lo, pin_hi = y_range_pin
    has_pin = pin_lo is not None

    verify_reference_js = spec.get("verify_reference_js")
    verify_reference_value = spec.get("verify_reference_value")
    verify_reference_label = spec.get("verify_reference_label") or "独立参考值"
    has_verify = verify_reference_js is not None or verify_reference_value is not None
    if verify_reference_js is not None and not isinstance(verify_reference_js, str):
        raise FigureError(f"figure '{fig_id}': 'verify_reference_js' must be a string "
                          f"(a JS expression in P, like js_function_body, returning a single "
                          f"number — the BODY only, no 'function(P){{...}}' wrapper), "
                          f"got {type(verify_reference_js).__name__}.")

    status_div_id = div_id + "-status"
    verify_div_id = div_id + "-verify"

    pin_js_lines = ""
    if has_pin:
        pin_js_lines = (
            f"  var PIN_LO = {json.dumps(pin_lo)};\n"
            f"  var PIN_HI = {json.dumps(pin_hi)};\n"
        )
    verify_fn_body = verify_reference_js if verify_reference_js is not None else "return 0;"
    verify_js_value = json.dumps(verify_reference_value) if verify_reference_value is not None else "null"
    verify_label_js = json.dumps(verify_reference_label + " = ")

    script_template = """
<script>
(function(){
  var root = document.getElementById('""" + js_div_id + """');
  var X = """ + js_x_values + """;
  var PARAMS = [""" + js_slider_defs + """ ];
  var CONSTANTS = """ + js_constants + """;
""" + pin_js_lines + """
  var VERIFY_VALUE = """ + verify_js_value + """;
  var sliderEls = {}, labelEls = {};
  PARAMS.forEach(function(p){
    var safeName = String(p.name).replace(/[^A-Za-z0-9_-]/g, '_');
    sliderEls[p.name] = document.getElementById('""" + js_div_id + """-slider-' + safeName);
    labelEls[p.name] = document.getElementById('""" + js_div_id + """-val-' + safeName);
  });
  function currentParams(){
    var P = CONSTANTS ? Object.assign({}, CONSTANTS) : {};
    PARAMS.forEach(function(p){ P[p.name] = parseFloat(sliderEls[p.name].value); });
    return P;
  }
  // The agent-authored closed-form body: recompute y for every x in X given
  // the current parameter object P. Scoped sandbox: it can only use X,
  // PARAMS, P, CONSTANTS, Math, JSON — no DOM access, no fetch, no eval,
  // no network.
  var LIVE_FN = function(P){
""" + js_js_fn_body + """
  };
  var VERIFY_FN = null;
""" + (f"  if ({json.dumps(bool(verify_reference_js))}) {{ VERIFY_FN = function(P){{\n{verify_fn_body}\n  }}; }}\n" if has_verify else "") + """
  var statusEl = document.getElementById('""" + status_div_id + """');
  var verifyEl = document.getElementById('""" + verify_div_id + """');
  function setStatus(msg, ok) {
    if (!statusEl) return;
    statusEl.textContent = msg;
    statusEl.style.color = ok ? '#3c9a55' : '#ff5470';
  }
  function refresh(){
    var P = currentParams();
    PARAMS.forEach(function(p){ labelEls[p.name].textContent = parseFloat(sliderEls[p.name].value).toFixed(4); });
    var ynew;
    try {
      ynew = LIVE_FN(P);
      if (!Array.isArray(ynew) || ynew.length !== X.length) {
        throw new Error('js_function_body must return an array of the same length as X (got '
          + (Array.isArray(ynew) ? ynew.length : typeof ynew) + ', expected ' + X.length + ').');
      }
      for (var i = 0; i < ynew.length; i++) {
        if (typeof ynew[i] !== 'number' || !isFinite(ynew[i])) {
          throw new Error('js_function_body returned a non-finite y value (NaN/Inf) at x index ' + i
            + '; check the formula for a division by zero or log(<=0) at the current parameter values.');
        }
      }
    } catch(e) {
      // Do not silently paper over a JS error in the live function body —
      // surface it visibly next to the sliders, matching this project's
      // "never silently skip a broken piece of output" rule.
      setStatus('实时重算出错（js_function_body 本身写错了，或参数越界导致公式出现 NaN/Inf，不是滑块控件坏了）: ' + e.message, false);
      return;
    }
    setStatus('正常：曲线已按当前参数实时重算（闭式表达式重新求值，不是重新解方程）', true);
    var restyle = {y: [ynew]};
""" + ("    if (typeof PIN_LO !== 'undefined') { Plotly.relayout(root, {yaxis: {range: [PIN_LO, PIN_HI]}}); }\n" if has_pin else "") + """
    Plotly.restyle(root, restyle, [0]);
    if (verifyEl) {
      var refVal = null;
      if (VERIFY_FN) { try { refVal = VERIFY_FN(P); } catch (e2) { verifyEl.textContent = '参考值计算出错: ' + e2.message; verifyEl.style.color = '#ff5470'; return; } }
      else if (VERIFY_VALUE !== null) { refVal = VERIFY_VALUE; }
      if (refVal === null || !isFinite(refVal)) { verifyEl.textContent = ''; return; }
      var ysum = 0, ycnt = 0;
      for (var j = 0; j < ynew.length; j++) { ysum += ynew[j]; ycnt++; }
      var ymean = ycnt ? ysum / ycnt : 0;
      var dev = ymean - refVal;
      var rel = refVal !== 0 ? Math.abs(dev / refVal) * 100 : null;
      verifyEl.textContent = """ + verify_label_js + """ + refVal +
        "，当前闭式结果网格均值偏差 = " + dev.toFixed(4) + (rel === null ? "" : " (" + rel.toFixed(2) + "%)");
      verifyEl.style.color = Math.abs(dev) < 1e-3 ? '#3c9a55' : '#d97706';
    }
  }
  PARAMS.forEach(function(p){ sliderEls[p.name].addEventListener('input', refresh); });
  refresh();
})();
</script>
"""

    controls_block = (
        '<div class="interactive-live-controls" style="padding:8px 16px;font-family:sans-serif;font-size:13px">'
        '<div style="font-weight:600;margin-bottom:6px">拖动滑块，实时改变曲线'
        '（纯浏览器端对闭式表达式重新求值，不是重新解方程；参数范围与精度由上游声明）</div>'
        + slider_block
        + f'<div id="{status_div_id}" style="font-size:12px;margin-top:4px;color:#666"></div>'
    )
    if has_verify:
        controls_block += f'<div id="{verify_div_id}" style="font-size:12px;margin-top:2px;color:#666"></div>'
    controls_block += "</div>"

    inject = controls_block + "\n" + script_template

    html = html.rstrip()
    if html.endswith("</div>"):
        html = html[:-6] + inject + "</div>"
    else:
        html = html + inject

    out = os.path.join(out_dir, f"{fig_id}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render numerical_artifacts.figures into one image file per figure (Node 2.7 optional step; output feeds Node 4's --figures-dir).")
    ap.add_argument("--state", required=True, help="problem_state_<slug>.json (only numerical_artifacts.figures is read)")
    ap.add_argument("--out-dir", required=True, help="Directory to write <figure_id>.<fmt> files into")
    ap.add_argument("--format", default="png", choices=["png", "svg"], help="Output image format (default png)")
    args = ap.parse_args(argv)

    with open(args.state, "r", encoding="utf-8-sig") as f:
        state = json.load(f)
    figures = (state.get("numerical_artifacts") or {}).get("figures")
    if not figures:
        print("no numerical_artifacts.figures present (or empty) — nothing to draw; this is a valid, explicitly-handled case, not an error.")
        return 0
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            written = render_all(figures, args.out_dir, args.format)
        glyph_missing = [w for w in caught if "missing from font" in str(w.message) or "Glyph" in str(w.message)]
        if glyph_missing:
            print(f"NOTE: {len(glyph_missing)} glyph/missing-font warning(s) were raised while drawing; "
                  f"the figures were still written, but some text (likely CJK) may render as missing-glyph boxes. "
                  f"See _configure_cjk_font() above for the fix (install a CJK-capable font). "
                  f"First warning: {glyph_missing[0].message}")
    except FigureError as e:
        print(f"FIGURE ERROR (will not silently skip): {e}", file=sys.stderr)
        return 1
    print(f"wrote {len(written)} figure(s) to {args.out_dir}:")
    for p in written:
        print(" -", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
