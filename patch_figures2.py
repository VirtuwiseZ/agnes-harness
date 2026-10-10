p = r"E:\agh-test\run2_figures.py"
raw = open(p, encoding="utf-8").read()

# Insert a helper _tight_colormesh right before def fig2a_saving_surface_head_on():
helper = '''def _tight_colormesh(ax, grid, r_factors, moon_names, title_text, out_name):
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
    cbar.set_label("Saving fraction (%) vs. direct-capture burn\\n(self-normalized to this panel's own data range)")
    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, out_name)
    plt.savefig(out_path, dpi=150)
    plt.close("all")
    return out_path


'''
anchor = "def fig2a_saving_surface_head_on():"
assert anchor in raw
raw = raw.replace(anchor, helper + anchor, 1)

# Replace fig2a's body (from `fig, ax = plt.subplots` line through `return path`
# in fig2a) with a _tight_colormesh call. Easiest: replace the whole original
# fig2a/fig2b function bodies with new compact versions.
old2a = '''    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="RdYlGn",
                   extent=[np.log10(r_factors[0]), np.log10(r_factors[-1]), 0.5, 4.5])
    ax.set_yticks([1, 2, 3, 4], MOON_NAMES)
    ax.set_xlabel("log10(perigee factor r_p/R_moon)")
    ax.set_ylabel("Moon")
    ax.set_title(f"Run #2, F2a: Propellant-saving fraction (% vs. direct insertion) for the HEAD-ON case,\\n"
                 f"as a 2D surface over (moon, perigee factor). Target orbit = {orbit} "
                 f"(a={M.CAPTURE_ORBITS[orbit]['a_m']/1e6:.0f}e6 m). Green=helps, red=costs propellant.\\n"
                 f"Every cell is expected to be RED (negative saving) - this heatmap makes the 'no exception anywhere' "
                 f"verdict visible at a glance, not buried under 4 near-flat lines.", fontsize=9)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Saving fraction (%) vs. direct-capture burn")
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "F2a_saving_surface_head_on.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path'''
new2a = '''    p = _tight_colormesh(
        None, grid, r_factors, MOON_NAMES,
        f"Run #2, F2a: Propellant-saving fraction (% vs. direct insertion) for the HEAD-ON case, 2D surface over (moon, perigee factor),\\n"
        f"target orbit = {orbit} (a={M.CAPTURE_ORBITS[orbit]['a_m']/1e6:.0f}e6 m). Colorbar is SELF-NORMALIZED to this panel's own\\n"
        f"data range (tiny, all-negative band) so the per-moon structure is visible as distinct darkening, not a uniform blob.\\n"
        f"Every cell is negative (costs a tiny amount of propellant vs. a direct burn) - the 'no exception anywhere' verdict.",
        "F2a_saving_surface_head_on.png")
    return p'''
# _tight_colormesh's `ax` param: we pass a fresh fig/ax; adjust signature call:
new2a = new2a.replace("None, grid", """fig, ax = plt.subplots(figsize=(9.0, 3.2))
    _tight_colormesh(ax, grid""").replace("None,", "", 1)
# Simpler: just rewrite the call cleanly
new2a = '''    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    p = _tight_colormesh(ax, grid, r_factors, MOON_NAMES,
        f"Run #2, F2a: Propellant-saving fraction (% vs. direct insertion) for the HEAD-ON case, 2D surface over (moon, perigee factor),\\n"
        f"target orbit = {orbit} (a={M.CAPTURE_ORBITS[orbit]['a_m']/1e6:.0f}e6 m). Colorbar is SELF-NORMALIZED to this panel's own\\n"
        f"data range (a tiny, all-negative band) so the per-moon structure is visible as distinct darkening, not a uniform blob.\\n"
        f"Every cell is negative (costs a tiny amount of propellant vs. a direct burn) - the 'no exception anywhere' verdict.",
        "F2a_saving_surface_head_on.png")
    return p'''
assert old2a in raw, "fig2a body anchor not found"
raw = raw.replace(old2a, new2a, 1)

old2b = '''    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="RdYlGn",
                   extent=[np.log10(r_factors[0]), np.log10(r_factors[-1]), 0.5, 4.5])
    ax.set_yticks([1, 2, 3, 4], MOON_NAMES)
    ax.set_xlabel("log10(perigee factor r_p/R_moon)")
    ax.set_ylabel("Moon")
    ax.set_title(f"Run #2, F2b: Propellant-saving fraction (%) vs. direct insertion, OVERTAKING control case,\\n"
                 f"2D surface over (moon, perigee factor), same target orbit as F2a. Expected to look\\n"
                 f"Different from F2a: modest, mostly-negative savings (a small speed LOSS, not the\\n"
                 f"classic large speed-UP, because at v_inf=20 km/s the spacecraft is faster than all 4 moons).",
                 fontsize=9)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Saving fraction (%) vs. direct-capture burn")
    fig.tight_layout()
    path = os.path.join(OUT_DIR, "F2b_saving_surface_overtaking.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path'''
new2b = '''    fig, ax = plt.subplots(figsize=(9.0, 3.2))
    p = _tight_colormesh(ax, grid, r_factors, MOON_NAMES,
        f"Run #2, F2b: Propellant-saving fraction (%) vs. direct insertion, OVERTAKING control case, 2D surface over (moon, perigee factor),\\n"
        f"same target orbit as F2a. Expected to look DIFFERENT from F2a: modest, mostly-POSITIVE savings for the 3 moons\\n"
        f"slower than the spacecraft (Europa/Ganymede/Callisto, a small net speed LOSS -> slightly less propellant needed),\\n"
        f"Io (faster-or-similar relative case) behaving differently; colorbar again self-normalized to this panel's own band.",
        "F2b_saving_surface_overtaking.png")
    return p'''
assert old2b in raw, "fig2b body anchor not found"
raw = raw.replace(old2b, new2b, 1)

open(p, "w", encoding="utf-8").write(raw)
print("rewrote F2a/F2b with self-normalized colormesh + a shared helper")
