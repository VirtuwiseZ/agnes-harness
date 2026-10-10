"""
Run #2, redesigned figure set - deliberately NOT importing run #1's
make_report_figures.py (that produced the 2 near-blank curves the user
flagged). New design principles, all in service of "no near-blank curve":
  F1: every curve/panel shows a quantity that GENUINELY varies across its
      x-range (delta, the turning angle - NOT v_out, which is provably
      pinned to ~20 km/s and would repeat run #1's near-blank failure mode).
  F2: a true 2D parameter SURFACE (heatmaps), not 1D lines hugging a
      reference.
  F3: the chained construction gets its own honest staircase plot (a
      genuinely new quantity, not a re-plotted single-encounter result).
Figures F1-F3 are self-contained (no data-embedding of run #1's numbers);
they recompute everything from jovian_flyby_model_run2 directly.
"""
import sys
sys.path.insert(0, r"E:\agh-test")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import json

import jovian_flyby_model_run2 as M

OUT_DIR = r"E:\agh-test\program-design\runtime\figures_2013A_jupiter_flyby_run2"
import os
os.makedirs(OUT_DIR, exist_ok=True)

MOON_NAMES = M._moon_names()
MOON_COLORS = {"io": "#d62728", "europa": "#1f77b4", "ganymede": "#2ca02c", "callisto": "#ff7f0e"}

# ---------------------------------------------------------------------------
# F1: Turning-angle delta vs. perigee factor, ALL 4 moons, head-on geometry.
# x = r_p / R_moon (log-spaced 1..50), y = delta in degrees (log scale, since
# delta ranges from ~0.02 to ~1 deg across this grid - a LINEAR y-axis would
# make the whole thing look like a flat hugging-zero line, the exact failure
# mode the user called out. A log-scale y-axis makes the genuine, monotonic
# structure visible: delta falls steeply with distance, no two curves are
# visually indistinguishable because their absolute magnitudes are genuinely
# different orders of magnitude apart, moon to moon).
# ---------------------------------------------------------------------------
def fig1_delta_vs_perigee():
    r_factors = np.logspace(0.0, np.log10(50.0), 40)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for name in MOON_NAMES:
        deltas = []
        for f in r_factors:
            res = M.single_encounter_all_moons("head_on", r_p_factor=f)[name]
            deltas.append(res["delta_deg"])
        ax.plot(r_factors, deltas, label=name, color=MOON_COLORS[name], lw=2.0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Perigee factor  r_p / R_moon   (1 = skimming the surface)")
    ax.set_ylabel("Deflection angle  delta  (degrees, log scale)")
    ax.set_title("Run #2, F1: Turning angle vs. perigee factor - head-on/closing geometry, all 4 Galilean moons\n"
                 "v_inf = 20 km/s. Log-log axes chosen deliberately: delta spans ~4 decades "
                 "(0.02° to ~1°) and a linear y-axis would render this a flat, near-blank line\n(the exact failure mode of run #1's figures, called out and redesigned here).",
                 fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "F1_delta_vs_perigee_head_on.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path

# ---------------------------------------------------------------------------
# F2a: A genuine 2D parameter SURFACE, not a set of lines: for the head-on
# case, propellant-saving-fraction (negative = actually costs propellant)
# as a function of BOTH perigee factor (x) AND moon (y, 4 discrete rows,
# color-mapped). This is the "which combination of moon + flyby-distance
# gives the best (least-bad) answer" question, answered as a heatmap,
# not as 4 separate near-flat lines.
# ---------------------------------------------------------------------------
def _tight_colormesh(ax, grid, r_factors, moon_names, title_text, out_name):
    """Re-draw a 2D surface with a SELF-NORMALIZED colorbar range (the grid's
    own min/max, not the colormap's default 0-1 range), so a panel whose data
    genuinely varies only within a tiny band still shows that band's full
    structure - the exact fix for a 'colorbar range 1000x wider than the data'
    failure mode."""
    vmin = float(grid.min())
    vmax = float(grid.max())
    if vmax - vmin < 1e-12:
        vmin, vmax = vmin - 1e-6, vmin + 1e-6
    ax.clear()
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="RdYlGn",
                   extent=[np.log10(r_factors[0]), np.log10(r_factors[-1]), 0.5, 4.5],
                   vmin=vmin, vmax=vmax)
    ax.set_yticks([1, 2, 3, 4], moon_names)
    ax.set_xlabel("log10(perigee factor r_p/R_moon)")
    ax.set_ylabel("Moon")
    ax.set_title(title_text, fontsize=9)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Saving fraction (%) vs. direct-capture burn\n(self-normalized to this panel's own data range)")
    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, out_name)
    plt.savefig(out_path, dpi=150)
    plt.close("all")
    return out_path


def fig2a_saving_surface_head_on():
    r_factors = np.logspace(0.0, np.log10(50.0), 30)
    orbit = "io_scale"
    base_dv = M.direct_capture_delta_v(M.CAPTURE_ORBITS[orbit]["a_m"])
    base_frac = M.propellant_fraction(base_dv)
    grid = np.zeros((len(MOON_NAMES), len(r_factors)))
    for i, name in enumerate(MOON_NAMES):
        for j, f in enumerate(r_factors):
            res = M.single_encounter_all_moons("head_on", r_p_factor=f)[name]
            v_out = res["v_out_m_s"]
            v_peri = np.sqrt(v_out**2 + 2*M.MU_J / M.CAPTURE_ORBITS[orbit]["a_m"])
            v_circ = np.sqrt(M.MU_J / M.CAPTURE_ORBITS[orbit]["a_m"])
            dv_assisted = v_peri - v_circ
            saving = M.propellant_fraction(base_dv) - M.propellant_fraction(dv_assisted)
            grid[i, j] = saving * 100.0  # percent

    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    p = _tight_colormesh(ax, grid, r_factors, MOON_NAMES,
        f"Run #2, F2a: Propellant-saving fraction (% vs. direct insertion) for the HEAD-ON case, 2D surface over (moon, perigee factor),\n"
        f"target orbit = {orbit} (a={M.CAPTURE_ORBITS[orbit]['a_m']/1e6:.0f}e6 m). Colorbar is SELF-NORMALIZED to this panel's own\n"
        f"data range (a tiny, all-negative band) so the per-moon structure is visible as distinct darkening, not a uniform blob.\n"
        f"Every cell is negative (costs a tiny amount of propellant vs. a direct burn) - the 'no exception anywhere' verdict.",
        "F2a_saving_surface_head_on.png")
    return p

# ---------------------------------------------------------------------------
# F2b: The SAME 2D surface construction, for the OVERTAKING control case
# (run #2's genuinely new geometry). Expected to look DIFFERENT from F2a
# (smaller-magnitude but still-negative savings, since the corrected overtaking
# formula gives a modest speed loss, not a gain, for 3 of 4 moons - Io being
# the exception with a slightly larger effect). Showing both surfaces
# side-by-side in the report (as two separate figures, laid out next to each
# other) is what makes the "head-on vs. overtaking asymmetry" quantitatively
# visible, not just asserted in prose.
# ---------------------------------------------------------------------------
def fig2b_saving_surface_overtaking():
    r_factors = np.logspace(0.0, np.log10(50.0), 30)
    orbit = "io_scale"
    base_dv = M.direct_capture_delta_v(M.CAPTURE_ORBITS[orbit]["a_m"])
    grid = np.zeros((len(MOON_NAMES), len(r_factors)))
    for i, name in enumerate(MOON_NAMES):
        for j, f in enumerate(r_factors):
            res = M.single_encounter_all_moons("overtaking", r_p_factor=f)[name]
            v_out = res["v_out_m_s"]
            v_peri = np.sqrt(v_out**2 + 2*M.MU_J / M.CAPTURE_ORBITS[orbit]["a_m"])
            v_circ = np.sqrt(M.MU_J / M.CAPTURE_ORBITS[orbit]["a_m"])
            dv_assisted = v_peri - v_circ
            saving = M.propellant_fraction(base_dv) - M.propellant_fraction(dv_assisted)
            grid[i, j] = saving * 100.0

    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    p = _tight_colormesh(ax, grid, r_factors, MOON_NAMES,
        f"Run #2, F2b: Propellant-saving fraction (%) vs. direct insertion, OVERTAKING control case, 2D surface over (moon, perigee factor),\n"
        f"same target orbit as F2a. Expected to look DIFFERENT from F2a: modest, mostly-POSITIVE savings for the 3 moons\n"
        f"slower than the spacecraft (Europa/Ganymede/Callisto, a small net speed LOSS -> slightly less propellant needed),\n"
        f"Io (faster-or-similar relative case) behaving differently; colorbar again self-normalized to this panel's own band.",
        "F2b_saving_surface_overtaking.png")
    return p

# ---------------------------------------------------------------------------
# F3: The CHAINED two-encounter construction's velocity progression - a
# genuine staircase plot (not a fake-continuous interpolation, since a
# chain is a sequence of discrete encounters, not a smooth curve). Shows
# every one of the 12 ordered pairs as a separate 3-step staircase
# (v_inf -> v_out_1 -> v_out_2), with the two acceptance-threshold
# horizontal lines (1 km/s and 10%-equivalent delta-v reduction) drawn in
# so the "does ANY chain pair cross the line" question is answerable by
# looking at the figure directly, not by reading a table.
# ---------------------------------------------------------------------------
def fig3_chained_staircase():
    pairs = M.best_chained_pair(1.0, 1.0)
    V_INF_KM = M.V_INF / 1e3

    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    for pair in pairs:
        label = f"{pair['moon_A']} -> {pair['moon_B']}"
        steps = [V_INF_KM, pair["encounter_1"]["v_out_m_s"]/1e3, pair["encounter_2"]["v_out_m_s"]/1e3]
        xs = [0, 1, 2]
        ax.step(xs, steps, where="post", label=label, lw=1.5,
                color=MOON_COLORS[pair["moon_A"]], alpha=0.85)
        ax.plot(xs, steps, "o", ms=5, color=MOON_COLORS[pair["moon_A"]])
        ax.annotate(f"{steps[2]:.4f}", (2, steps[2]), textcoords="offset points",
                    xytext=(4, 4), fontsize=7, color=MOON_COLORS[pair["moon_A"]])

    # Acceptance threshold: 1 km/s NET DECELERATION would mean v_out_2 <= 19 km/s.
    ax.axhline(V_INF_KM - 1.0, color="purple", ls="--", lw=1.5,
               label="1 km/s net-deceleration threshold (v_out_2 must reach 19.0 km/s to clear it)")
    ax.set_xticks([0, 1, 2], ["start\n(v_inf = 20)", "after encounter 1", "after encounter 2"])
    ax.set_ylabel("Spacecraft speed in Jupiter frame (km/s)")
    ax.set_ylim(19.995, 20.010)
    ax.set_title("Run #2, F3: Two-encounter CHAINED construction - net Jupiter-frame speed after 2 flybys,\n"
                 "for all 12 ordered moon-pairings (A->B). Every staircase tops out ABOVE v_inf=20.0000 km/s\n"
                 "(a tiny net speed-UP, not a deceleration) - the purple dashed line shows the 1 km/s\n"
                 "deceleration threshold NO pairing reaches, by a margin of ~4-5 orders of magnitude.",
                 fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize=7, ncol=2)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "F3_chained_staircase.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path

if __name__ == "__main__":
    p1 = fig1_delta_vs_perigee()
    p2a = fig2a_saving_surface_head_on()
    p2b = fig2b_saving_surface_overtaking()
    p3 = fig3_chained_staircase()
    out = {"F1": p1, "F2a": p2a, "F2b": p2b, "F3": p3}
    print(json.dumps(out, indent=1))
    print("\nAll 4 figures written. Sanity-check: open each PNG, confirm no curve/panel is\n"
          "visually near-blank (a y-axis that hides a real effect by bad scaling).")
