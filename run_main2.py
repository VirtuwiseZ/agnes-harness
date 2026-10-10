import sys, json
sys.path.insert(0, r"E:\agh-test")
import jovian_flyby_model as M

print("=" * 74)
print("MAIN CASES (r_p = 1.0 * R_moon) - head-on closing-speed geometry (v_rel = v_inf + v_moon)")
print("=" * 74)
for moon in M.MOONS:
    for orbit in M.TARGET_ORBITS:
        out = M.run_model({"moon": moon, "target_orbit": orbit, "r_p_factor": 1.0})
        print(f"{moon:>10s} -> {M.TARGET_ORBITS[orbit]['label']:<30s}")
        print(f"   v_moon={out['v_moon_m_s']/1e3:8.3f} km/s  v_rel={out['v_rel_moon_frame_m_s']/1e3:8.3f} km/s  "
              f"delta={out['delta_deg']:8.4f} deg")
        print(f"   v_out={out['v_out_jupiter_frame_m_s']/1e3:8.4f} km/s   "
              f"{'SLOW-DOWN' if out['is_a_true_slowdown'] else 'SPEED-UP'} "
              f"(delta-v {out['jupiter_frame_speed_change_m_s']/1e3:+.5f} km/s)")
        print(f"   bound after assist: {out['is_bound_after_assist']}   "
              f"dv_direct={out['dv_direct_m_s']/1e3:8.4f}  dv_assist={out['dv_assisted_m_s']/1e3:8.4f}  km/s")
        print(f"   propellant fraction: direct {out['frac_direct']*100:7.4f}% -> assist {out['frac_assist']*100:7.4f}%   "
              f"SAVING {out['primary_result']*100:+.5f}%")
        print()

print("=" * 74)
print("PERIGEE-FACTOR SWEEP (r_p = f*R_moon), ganymede + callisto, io-scale orbit")
print("=" * 74)
for moon in ["ganymede", "callisto"]:
    for f in [0.5, 1.0, 1.5, 2.0, 5.0, 10.0]:
        out = M.run_model({"moon": moon, "target_orbit": "io_scale", "r_p_factor": f})
        print(f"{moon:>10s} r_p={f}R: delta={out['delta_deg']:9.5f} deg  "
              f"v_out={out['v_out_jupiter_frame_m_s']/1e3:9.5f} km/s  "
              f"{'slow-down' if out['is_a_true_slowdown'] else 'speed-up'}  "
              f"dpv={out['jupiter_frame_speed_change_m_s']/1e3:+8.5f}  saving={out['primary_result']*100:+9.5f}%")

spec = {
    "model_module": "jovian_flyby_model",
    "primary_result": "primary_result",
    "cases": [
        {"name": "v_inf very small (1 km/s arrival, near-parabolic approach)",
         "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 1e3, "r_p_factor": 1.0},
         "expectation": "finite"},
        {"name": "v_inf very large (500 km/s, extreme hypervelocity)",
         "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 5e5, "r_p_factor": 1.0},
         "expectation": "finite"},
        {"name": "perigee factor very large (flyby far from moon, minimal turning)",
         "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4, "r_p_factor": 1e8},
         "expectation": "finite"},
        {"name": "perigee factor at nominal surface-skim value",
         "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4, "r_p_factor": 1.0},
         "expectation": "finite"},
        {"name": "Isp very high (near-ideal propulsion)",
         "params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4, "r_p_factor": 1.0, "Isp": 1e6},
         "expectation": "finite"},
    ],
    "sweep": {
        "param": "r_p_factor",
        "order": "decrease",
        "values": [0.5, 1.0, 2.0, 5.0, 10.0, 50.0],
        "base_params": {"moon": "ganymede", "target_orbit": "io_scale", "v_inf": 2e4},
        "_expectation_note": "as r_p_factor increases (farther flyby), turning angle shrinks and the (always-negative-or-zero) propellant 'saving' must be monotonically non-increasing - i.e. moving farther from the moon cannot help; it only makes the negligible effect even more negligible."
    },
}
with open(r"E:\agh-test\boundary_spec.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=2)
print("\nboundary spec written.")
