import sys
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
sys.path.insert(0, r"E:\agh-test")
import json, math

import jovian_flyby_model as M

# --- main-case run for each moon x target orbit ---
print("=" * 70)
print("MAIN CASES (r_p = 1.0 * R_moon, skimming the surface)")
print("=" * 70)
results = {}
for moon in M.MOONS:
    for orbit in M.TARGET_ORBITS:
        out = M.run_model({"moon": moon, "target_orbit": orbit, "r_p_factor": 1.0})
        results[(moon, orbit)] = out
        print(f"{moon:>10s} -> {M.TARGET_ORBITS[orbit]['label']:<30s}")
        print(f"   v_moon={out['v_moon_m_s']/1e3:.3f} km/s  delta={out['delta_deg']:.1f} deg  "
              f"v_out={out['v_out_jupiter_frame_m_s']/1e3:.3f} km/s  "
              f"(max possible decel {out['v_delta_max_possible_m_s']/1e3:.3f} km/s)")
        print(f"   bound after assist: {out['is_bound_after_assist']}   "
              f"dv_direct={out['dv_direct_m_s']/1e3:.3f} km/s   dv_assist={out['dv_assisted_m_s']/1e3:.3f} km/s")
        print(f"   propellant fraction: direct {out['frac_direct']*100:.2f}%  -> assist {out['frac_assist']*100:.2f}%   "
              f"SAVING {out['primary_result']*100:.2f}%")

# --- sensitivity: r_p factor sweep for the best moon ---
print("\n" + "=" * 70)
print("PERIGEE-FACTOR SWEEP (r_p = f * R_moon) for ganymede/callisto, io-scale orbit")
print("=" * 70)
for moon in ["ganymede", "callisto"]:
    for f in [1.0, 1.5, 2.0, 5.0, 10.0]:
        out = M.run_model({"moon": moon, "target_orbit": "io_scale", "r_p_factor": f})
        print(f"{moon:>10s} r_p={f}R: delta={out['delta_deg']:6.1f} deg  "
              f"v_out={out['v_out_jupiter_frame_m_s']/1e3:7.3f} km/s  saving={out['primary_result']*100:6.2f}%")

# --- boundary gate spec ---
spec = {
    "model_module": "jovian_flyby_model",
    "primary_result": "primary_result",
    "cases": [
        {
            "name": "v_inf -> very small (approach speed ~0, sub-orbital-speed arrival)",
            "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 100.0, "r_p_factor": 1.0},
            "expectation": "finite"
        },
        {
            "name": "v_inf -> very large (hypervelocity, 1000 km/s)",
            "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 1e6, "r_p_factor": 1.0},
            "expectation": "finite"
        },
        {
            "name": "perigee factor -> very large (flyby far from the moon, barely any turning)",
            "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4, "r_p_factor": 1e6},
            "expectation": "finite"
        },
        {
            "name": "perigee factor -> 1 (surface skim, the nominal case)",
            "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4, "r_p_factor": 1.0},
            "expectation": "finite"
        },
        {
            "name": "Isp -> very high (near-ideal propulsion), sanity check on propellant fraction",
            "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4, "r_p_factor": 1.0, "Isp": 1e6},
            "expectation": "finite"
        },
    ],
    "sweep": {
        "param": "r_p_factor",
        "order": "decrease",
        "values": [1.0, 2.0, 5.0, 10.0, 50.0, 100.0],
        "base_params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4},
        "_expectation_note": "as perigee factor increases (flyby farther from the moon), turning angle shrinks, so the achievable deceleration shrinks and the propellant saving must monotonically DECREASE with r_p_factor."
    },
}
with open(r"E:\agh-test\boundary_spec.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2)
print("\nboundary spec written to E:\\agh-test\\boundary_spec.json")
