"""Node 2.7 (optional) — render numerical-artifact figures for a report.

Reads ONLY `problem_state.json`'s `numerical_artifacts.figures` (the domain-
neutral sub-schema documented in program-design/problem_state_schema.md
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
    python program-design/hooks/make_report_figures.py \
        --state program-design/runtime/problem_state_<task-slug>.json \
        --out-dir program-design/runtime/figures_<task-slug> \
        [--format png|svg]
"""
import argparse
import json
import math
import os
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

    # Axis limits: include every finite data point across all series; never
    # silently crop. (NaN/Inf points are skipped by matplotlib itself.)
    all_x = [v for s in series for v in (s.get("points") or {}).get("x", [])]
    all_y = [v for s in series for v in (s.get("points") or {}).get("y", [])]
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
        ax.legend()
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
    arr = np.array([[v if isinstance(v, (int, float)) and math.isfinite(v) else np.nan for v in row] for row in vals], dtype=float)

    def _is_numeric(values):
        return all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values)

    x_numeric = _is_numeric(xv)
    y_numeric = _is_numeric(yv)

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    style = fig_spec.get("heatmap_style", "pcolormesh")

    if x_numeric and y_numeric:
        X, Y = np.meshgrid(xv, yv)
        if x_scale == "log":
            ax.set_xscale("log")
        if y_scale == "log":
            ax.set_yscale("log")
        if style == "contourf":
            cs = ax.contourf(X, Y, arr, levels=12, cmap="viridis")
        else:
            im = ax.pcolormesh(X, Y, arr, cmap="viridis")
            cs = im
    else:
        # Categorical axis (e.g. feature names, country names, lat/lon index
        # labels): pcolormesh/meshgrid assume numeric coords and crash on
        # string labels. Use imshow with the matrix directly, and put the
        # category labels on the ticks. (Also handles the mixed case of one
        # categorical + one numeric axis.)
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
        im = ax.imshow(arr.T, cmap="viridis", origin="lower", aspect="auto")
        cs = im
        ax.set_xticks(range(len(xv)))
        ax.set_xticklabels([str(v) for v in xv], rotation=45, ha="right")
        ax.set_yticks(range(len(yv)))
        ax.set_yticklabels([str(v) for v in yv])
        # imshow indexes rows top-to-bottom by default; origin='lower' flips it
        # so that y_values[0] sits at the bottom, matching the numeric-axis
        # convention used elsewhere in this script.

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


def render_all(figures, out_dir, fmt):
    """Draw every figure in `figures`, independently. A malformed figure raises
    FigureError that is collected (not raised immediately) so one bad figure
    cannot silently skip the rest of the batch — good figures in the same
    `numerical_artifacts.figures` dict still get written; all errors are
    reported together at the end and the caller decides (exit 1) whether the
    overall run counts as successful. This is deliberate: "one typo in one
    figure's y_err length" must not be the reason the other four, correct,
    figures for the same task never get drawn at all."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    errors = []
    for fig_id, spec in figures.items():
        kind = spec.get("kind", "curve")
        try:
            if kind == "heatmap":
                fig = _draw_heatmap(spec, fig_id)
            elif kind == "boxplot":
                fig = _draw_boxplot(spec, fig_id)
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
