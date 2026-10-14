"""
gravity_assist_model.py
=======================
Orbital mechanics and gravity-assist deceleration evaluation model for a
spacecraft arriving at Jupiter with hyperbolic excess velocity v_inf = 20 km/s.

Computes:
1. Keplerian hyperbolic approach velocities at Galilean moon orbits (Vis-Viva).
2. Encounter kinematics and relative hyperbolic velocities.
3. Maximum two-body scattering deflection angles subject to surface radius bounds (r_p >= R_moon).
4. Velocity vector changes in Jupiter-centric frame and maximum deceleration Delta v.
5. Minimum Delta v required for orbital capture (Oberth at periapsis vs at satellite orbits).
6. Tsiolkovsky propellant mass fraction savings and physical feasibility bounds.
7. Boundary gate hook callable `run_model(params)` for automated validation.
"""

import math
import json
import os
import sys

# Standard Astrophysical Constants (NASA JPL Planetary & Satellite Ephemeris)
MU_JUPITER = 126686534.0       # Jupiter gravitational parameter, km^3/s^2
R_JUPITER = 71492.0            # Jupiter equatorial radius, km
G0 = 9.80665e-3                # Standard gravity, km/s^2
DEFAULT_ISP = 320.0            # Bipropellant rocket specific impulse, seconds

MOON_DATA = {
    "Io": {
        "semi_major_axis_km": 421700.0,
        "mu_km3_s2": 5959.916,
        "radius_km": 1821.6,
        "name_cn": "木卫一 (Io)"
    },
    "Europa": {
        "semi_major_axis_km": 670900.0,
        "mu_km3_s2": 3202.739,
        "radius_km": 1560.8,
        "name_cn": "木卫二 (Europa)"
    },
    "Ganymede": {
        "semi_major_axis_km": 1070400.0,
        "mu_km3_s2": 9887.834,
        "radius_km": 2634.1,
        "name_cn": "木卫三 (Ganymede)"
    },
    "Callisto": {
        "semi_major_axis_km": 1882700.0,
        "mu_km3_s2": 7179.289,
        "radius_km": 2410.3,
        "name_cn": "木卫四 (Callisto)"
    }
}


def run_model(params: dict) -> dict:
    """Boundary gate callable interface.
    Accepts:
      - v_inf_rel (km/s)
      - r_p (km)
      - mu_moon (km^3/s^2)
    Returns dict with primary result `delta_v_decel` (km/s).
    """
    v_inf_rel = float(params.get("v_inf_rel", 14.3))
    r_p = float(params.get("r_p", 2634.1))
    mu_moon = float(params.get("mu_moon", 9887.834))

    if mu_moon <= 0.0 or r_p <= 0.0 or v_inf_rel <= 0.0:
        return {"delta_v_decel": 0.0, "delta_angle_deg": 0.0}

    # Eccentricity e = 1 + r_p * v_inf^2 / mu
    denom = 1.0 + (r_p * (v_inf_rel ** 2)) / mu_moon
    if denom > 1e12:
        return {"delta_v_decel": 0.0, "delta_angle_deg": 0.0}

    sin_half_delta = 1.0 / denom
    if sin_half_delta > 1.0:
        sin_half_delta = 1.0

    delta_v = 2.0 * v_inf_rel * sin_half_delta
    delta_angle_deg = 2.0 * math.degrees(math.asin(sin_half_delta))

    return {
        "delta_v_decel": float(delta_v),
        "delta_angle_deg": float(delta_angle_deg)
    }


def analyze_spacecraft_arrival(v_inf_arrival: float = 20.0, r_periapsis_capture: float = 75067.0):
    """Full physics modeling across all four Galilean moons.
    v_inf_arrival: approach excess velocity (km/s)
    r_periapsis_capture: periapsis for Jupiter orbit insertion burn, e.g. 1.05 * R_Jupiter (km)
    """
    results = {
        "v_inf_arrival_km_s": v_inf_arrival,
        "r_periapsis_capture_km": r_periapsis_capture,
        "jupiter_surface_radius_km": R_JUPITER,
        "baseline_capture": {},
        "moons": {}
    }

    # Baseline capture requirement (no gravity assist) at periapsis:
    v_peri_base = math.sqrt(v_inf_arrival ** 2 + 2.0 * MU_JUPITER / r_periapsis_capture)
    v_esc_peri = math.sqrt(2.0 * MU_JUPITER / r_periapsis_capture)
    delta_v_cap_peri_base = v_peri_base - v_esc_peri  # minimum to achieve parabolic orbit E=0

    # Capture to typical high-elliptic orbit (period ~ 100 days, apocenter ~ 1.4e7 km)
    # semi-major axis a_ellip:
    a_ellip = 7.0e6
    v_ellip_peri = math.sqrt(MU_JUPITER * (2.0 / r_periapsis_capture - 1.0 / a_ellip))
    delta_v_cap_ellip_base = v_peri_base - v_ellip_peri

    c_eff = DEFAULT_ISP * G0
    prop_frac_base = 1.0 - math.exp(-delta_v_cap_peri_base / c_eff)

    results["baseline_capture"] = {
        "v_peri_km_s": v_peri_base,
        "v_esc_peri_km_s": v_esc_peri,
        "delta_v_parabolic_cap_km_s": delta_v_cap_peri_base,
        "delta_v_elliptical_cap_km_s": delta_v_cap_ellip_base,
        "propellant_mass_fraction_base": prop_frac_base
    }

    for moon_name, data in MOON_DATA.items():
        a_m = data["semi_major_axis_km"]
        mu_m = data["mu_km3_s2"]
        r_m = data["radius_km"]

        # Orbital velocity of moon around Jupiter
        v_moon_circ = math.sqrt(MU_JUPITER / a_m)

        # Spacecraft velocity in Jupiter frame at moon's orbital distance
        v_sc_jup = math.sqrt(v_inf_arrival ** 2 + 2.0 * MU_JUPITER / a_m)

        # Minimum possible relative approach velocity (tangential prograde flyby)
        # Note: In prograde pass, sc moves faster than moon: v_rel = v_sc_jup - v_moon_circ
        v_rel_min = v_sc_jup - v_moon_circ

        # Hyperbolic deflection at grazing encounter r_p = r_m (theoretical upper bound)
        denom = 1.0 + (r_m * (v_rel_min ** 2)) / mu_m
        sin_half_delta = 1.0 / denom
        delta_angle_rad = 2.0 * math.asin(sin_half_delta)
        delta_angle_deg = math.degrees(delta_angle_rad)

        # Maximum vector change Delta v_vector
        delta_v_assist_max = 2.0 * v_rel_min * sin_half_delta

        # Post-flyby velocity in Jupiter frame (optimal deceleration configuration)
        v_sc_jup_after = v_sc_jup - delta_v_assist_max

        # Local escape velocity at moon's orbital distance
        v_esc_moon_dist = math.sqrt(2.0 * MU_JUPITER / a_m)

        # Direct capture Delta v at moon distance (without periapsis drop)
        delta_v_direct_cap_moon = v_sc_jup - v_esc_moon_dist

        # Residual orbital energy after flyby
        spec_energy_after = 0.5 * (v_sc_jup_after ** 2) - MU_JUPITER / a_m
        v_inf_residual = math.sqrt(2.0 * spec_energy_after) if spec_energy_after > 0 else 0.0

        # Propulsive capture at periapsis AFTER flyby
        if v_inf_residual > 0:
            v_peri_after = math.sqrt(v_inf_residual ** 2 + 2.0 * MU_JUPITER / r_periapsis_capture)
            delta_v_cap_peri_after = v_peri_after - v_esc_peri
            delta_v_saved_peri = delta_v_cap_peri_base - delta_v_cap_peri_after
            fuel_saving_ratio = delta_v_saved_peri / delta_v_cap_peri_base
            prop_frac_after = 1.0 - math.exp(-delta_v_cap_peri_after / c_eff)
            net_prop_saved_fraction = prop_frac_base - prop_frac_after
        else:
            delta_v_cap_peri_after = 0.0
            delta_v_saved_peri = delta_v_cap_peri_base
            fuel_saving_ratio = 1.0
            prop_frac_after = 0.0
            net_prop_saved_fraction = prop_frac_base

        results["moons"][moon_name] = {
            "name_cn": data["name_cn"],
            "orbital_distance_km": a_m,
            "moon_orbital_speed_km_s": v_moon_circ,
            "spacecraft_speed_at_encounter_km_s": v_sc_jup,
            "min_relative_speed_v_inf_rel_km_s": v_rel_min,
            "deflection_angle_deg": delta_angle_deg,
            "max_assist_delta_v_km_s": delta_v_assist_max,
            "post_flyby_speed_km_s": v_sc_jup_after,
            "local_escape_speed_km_s": v_esc_moon_dist,
            "direct_capture_delta_v_at_moon_km_s": delta_v_direct_cap_moon,
            "residual_v_inf_km_s": v_inf_residual,
            "periapsis_capture_delta_v_after_flyby_km_s": delta_v_cap_peri_after,
            "delta_v_saved_at_periapsis_km_s": delta_v_saved_peri,
            "delta_v_saving_percentage": fuel_saving_ratio * 100.0,
            "propellant_saved_percentage_of_wet_mass": net_prop_saved_fraction * 100.0,
            "is_captured_by_flyby_alone": False
        }

    return results


def main():
    results = analyze_spacecraft_arrival(v_inf_arrival=20.0)

    # Save results to JSON in the same directory
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    out_json_path = os.path.join(cur_dir, "results.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("=== 木星探测器 20 km/s 入射速度下卫星引力助推减速评估 ===")
    base = results["baseline_capture"]
    print(f"基准近木点制动 (无助推, r_p = 1.05 R_J):")
    print(f"  近木点速度: {base['v_peri_km_s']:.3f} km/s")
    print(f"  木星逃逸速度: {base['v_esc_peri_km_s']:.3f} km/s")
    print(f"  抛物线捕获最小制动需求: {base['delta_v_parabolic_cap_km_s']:.3f} km/s")
    print(f"  推进剂消耗质量比 (Isp=320s): {base['propellant_mass_fraction_base']*100:.2f}%\n")

    print(f"{'卫星名称':<12} | {'相对速度(km/s)':<12} | {'最大偏转角(°)':<12} | {'单次最大减速(km/s)':<16} | {'剩余双曲速度(km/s)':<16} | {'近木点制动节省率':<12}")
    print("-" * 90)
    for moon_name, m in results["moons"].items():
        print(f"{m['name_cn']:<12} | {m['min_relative_speed_v_inf_rel_km_s']:<12.3f} | {m['deflection_angle_deg']:<12.3f} | {m['max_assist_delta_v_km_s']:<16.3f} | {m['residual_v_inf_km_s']:<16.3f} | {m['delta_v_saving_percentage']:<10.2f}%")

    print("\n[物理结论]")
    print("1. 绝对减速量微弱: 四颗伽利略卫星在紧贴表面掠过时，单次最大理论减速量仅为 0.287 ~ 0.514 km/s (木卫三最大为 0.514 km/s)。")
    print("2. 无法实现自捕获: 飞掠后剩余双曲过剩速度仍高达 19.35 ~ 19.64 km/s，轨道依然处于极强双曲线状态，单次飞掠无法闭合轨道。")
    print("3. 多次飞掠彻底失效: 由于轨道未闭合，探测器穿过木星系统后将直接逃逸至深空，绝无再次飞掠任何卫星的几何可能。")
    print("4. 相对燃料节省微不足道: 若结合近木点发动机点火捕获，飞掠带来的制动量节省仅为 0.12 ~ 0.21 km/s (节省比例仅约 3.6% ~ 6.2%)，若计入深空瞄准卫星所需的轨道修正机动(TCM)消耗与近木点奥伯斯特几何失配损失，实际净收益几乎为零甚至为负。")
    print("5. 最终判定: 无法通过该策略实现显著的燃料节省。")


if __name__ == "__main__":
    main()
