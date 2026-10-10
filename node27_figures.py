import sys, json, math
sys.path.insert(0, r"E:\agh-test")
import jovian_flyby_model as M

STATE = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby.json"

def rpf(moon, orbit, f):
    o = M.run_model({"moon": moon, "target_orbit": orbit, "r_p_factor": f})
    return o["v_out_jupiter_frame_m_s"] / 1e3, o["primary_result"] * 100, o["delta_deg"]

rpfs = [0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]

def series(moon, orbit):
    xs, ys, dts = [], [], []
    for f in rpfs:
        v, s, d = rpf(moon, orbit, f)
        xs.append(f); ys.append(v); dts.append(d)
    return xs, ys, dts

st = json.load(open(STATE, encoding="utf-8"))
figures = {}

# Figure 1: v_out (Jupiter frame, km/s) vs perigee factor, all 4 moons, io-scale orbit
xs, ys_by_moon = {}, {}
for moon in M.MOONS:
    xs_m, ys_m, _ = series(moon, "io_scale")
    ys_by_moon[moon] = list(zip(xs_m, ys_m))
series_list = [{"name": f"{m} (v_out, km/s)", "role": "simulation",
                "points": {"x": [p[0] for p in ys_by_moon[m]], "y": [p[1] for p in ys_by_moon[m]]}}
               for m in M.MOONS]
series_list.append({"name": "no assist (v_inf = 20 km/s)", "role": "theory",
                    "points": {"x": [rpfs[0], rpfs[-1]], "y": [20.0, 20.0]}})
figures["vout_vs_rp"] = {
    "kind": "curve",
    "title": "Jupiter-frame exit speed vs perigee factor r_p/(R_moon)\n(all four Galilean moons, skimming-or-farther flyby, io-scale target orbit)",
    "axes": {"x": {"label": "r_p / R_moon  (perigee, in moon radii)"},
             "y": {"label": "v_out (km/s), Jupiter frame"}},
    "series": series_list,
}

# Figure 2: propellant saving % vs perigee factor (log x-axis), gainymede + callisto
xs_g, ys_g, _ = series("ganymede", "io_scale")
xs_c, ys_c, _ = series("callisto", "io_scale")
figures["saving_vs_rp"] = {
    "kind": "curve",
    "title": "Propellant saving (%) vs perigee factor - always negative\n(the moon assist never saves propellant at v_inf = 20 km/s)",
    "axes": {"x": {"label": "r_p / R_moon (log scale)", "scale": "log"},
             "y": {"label": "Propellant saving vs direct insertion burn (%)"}},
    "series": [
        {"name": "ganymede assist", "role": "simulation",
         "points": {"x": xs_g, "y": ys_g}},
        {"name": "callisto assist", "role": "simulation",
         "points": {"x": xs_c, "y": ys_c}},
        {"name": "0% (no effect)", "role": "theory",
         "points": {"x": [rpfs[0], rpfs[-1]], "y": [0.0, 0.0]}},
    ],
}

# Figure 3: turning angle (deg) vs perigee factor, log x-axis - shows how small delta stays
figures["delta_vs_rp"] = {
    "kind": "curve",
    "title": "Hyperbolic turning angle vs perigee factor\n(even skimming a moon's surface, delta < 1 deg - far too small to matter)",
    "axes": {"x": {"label": "r_p / R_moon (log scale)", "scale": "log"},
             "y": {"label": "Turning angle delta (deg)"}},
    "series": [
        {"name": "ganymede", "role": "simulation",
         "points": {"x": list(map(lambda f: f, rpfs)), "y": [rpf("ganymede","io_scale",f)[2] for f in rpfs]}},
        {"name": "callisto", "role": "simulation",
         "points": {"x": list(rpfs), "y": [rpf("callisto","io_scale",f)[2] for f in rpfs]}},
    ],
}

st["numerical_artifacts"]["figures"] = figures
json.dump(st, open(STATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("figures spec written:", list(figures.keys()))
