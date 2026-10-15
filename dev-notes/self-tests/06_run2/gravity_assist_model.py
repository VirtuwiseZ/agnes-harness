"""
gravity_assist_model.py
=======================
木星卫星引力辅助减速与入轨推进剂节省评估模型
采用双体拼合圆锥曲线 (Patched Conics) 理论与天体力学开普勒双曲弹性散射动力学。

核心物理过程：
1. 航天器以双曲多余速度 v_inf 抵近木星系统，沿双曲轨道向木星运动；
2. 航天器在卫星轨道半径 r_m 处的速度为 v_sc = sqrt(v_inf^2 + 2*mu_J / r_m)；
3. 卫星以速度 v_m = sqrt(mu_J / r_m) 绕木星做圆周运动；
4. 航天器相对卫星的相遇相对速度 v_rel 满足矢量三角形关系，在顺行追赶相遇时达到极小值 v_rel = v_sc - v_m；
5. 航天器掠过卫星表面（最近距 r_p >= R_m），在卫星参考系中产生最大偏转角 sin(delta/2) = 1 / (1 + r_p * v_rel^2 / mu_m)；
6. 卫星引力散射产生的最大速度矢量改变量大小为 Delta_v = 2 * v_rel * sin(delta/2)；
7. 由天体力学能量守恒与 Tisserand 关系，航天器相对木星比能的最大可能削减量为 Delta_E_max = 2 * v_m * v_rel * sin(delta/2)；
8. 计算飞掠后轨道是否闭合（E_post = 0.5 * v_inf^2 - Delta_E_max < 0）；
9. 与纯推进系统在近木点及卫星高度进行轨道捕获所需 Delta_v 进行对比，结合齐奥尔科夫斯基公式计算推进剂节省比例。
"""

import math
import sys

# 权威标准物理与天体常数 (NASA JPL Solar System Dynamics)
MU_JUPITER = 126686534.0  # km^3/s^2
R_JUPITER = 71492.0       # km

GALILEAN_MOONS = {
    "Io": {
        "mu": 5959.9,
        "radius": 1821.6,
        "orbit_r": 421700.0
    },
    "Europa": {
        "mu": 3202.7,
        "radius": 1560.8,
        "orbit_r": 670900.0
    },
    "Ganymede": {
        "mu": 9887.8,
        "radius": 2634.1,
        "orbit_r": 1070400.0
    },
    "Callisto": {
        "mu": 7179.3,
        "radius": 2410.3,
        "orbit_r": 1882700.0
    }
}


def calculate_flyby_dynamics(v_inf=20.0, moon_name="Ganymede", flyby_alt_km=0.0, mu_J=MU_JUPITER, mu_m=None):
    """
    计算特定参数下单次飞掠的最大减速动力学
    """
    moon = GALILEAN_MOONS[moon_name]
    r_m = moon["orbit_r"]
    R_m = moon["radius"]
    mu_moon = mu_m if mu_m is not None else moon["mu"]
    r_p = R_m + max(0.0, flyby_alt_km)

    # 1. 航天器到达卫星轨道处的速度 (木星参考系)
    v_sc = math.sqrt(v_inf**2 + 2.0 * mu_J / r_m)
    # 2. 卫星公转速度
    v_m = math.sqrt(mu_J / r_m)
    # 3. 卫星局部逃逸速度
    v_esc_J_at_rm = math.sqrt(2.0 * mu_J / r_m)

    # 4. 最小相对速度 (顺行相遇几何)
    v_rel = v_sc - v_m

    # 5. 偏转角
    if mu_moon <= 0.0 or r_p <= 0.0 or v_rel <= 0.0:
        sin_half_delta = 0.0
        delta_rad = 0.0
    else:
        denom = 1.0 + (r_p * v_rel**2) / mu_moon
        sin_half_delta = 1.0 / denom
        delta_rad = 2.0 * math.asin(min(1.0, sin_half_delta))

    # 6. 最大速度矢量变化量大小 (卫星系/木星系相同)
    delta_v_flyby_max = 2.0 * v_rel * sin_half_delta

    # 7. 航天器相对木星比能变化 (最大可能降能)
    # E_in = 0.5 * v_inf^2
    # Delta_E_max = v_m * Delta_v_flyby_max
    e_in = 0.5 * v_inf**2
    delta_e_max = v_m * delta_v_flyby_max
    e_post = e_in - delta_e_max

    is_captured = (e_post < 0.0)
    v_inf_post = math.sqrt(2.0 * e_post) if e_post > 0.0 else 0.0

    # 8. 轨道捕获所需 Delta_v (纯推进基准)
    # 场景 A: 在卫星轨道高度进行切向制动捕获 (v -> v_esc_J_at_rm)
    delta_v_capture_at_moon = v_sc - v_esc_J_at_rm

    # 场景 B: 航天器在木星表面云顶 (近木点 r_p = R_J) 进行最优奥伯特机动捕获
    v_peri_J = math.sqrt(v_inf**2 + 2.0 * mu_J / R_JUPITER)
    v_esc_J_surf = math.sqrt(2.0 * mu_J / R_JUPITER)
    delta_v_capture_at_surf = v_peri_J - v_esc_J_surf

    # 9. 推进剂节省计算 (齐奥尔科夫斯基方程)
    # 假定双组元高性能发动机 c_e = 3.04 km/s (I_sp = 310 s)
    c_e = 3.04
    # 捕获所需质量比 m_f / m_0 = exp(-Delta_v / c_e)
    # 推进剂消耗分数 (m_0 - m_f) / m_0 = 1 - exp(-Delta_v / c_e)
    prop_frac_moon_pure = 1.0 - math.exp(-delta_v_capture_at_moon / c_e)
    # 若飞掠能够减去 delta_v_flyby_max，剩余所需推进制动
    delta_v_rem_moon = max(0.0, delta_v_capture_at_moon - delta_v_flyby_max)
    prop_frac_moon_assisted = 1.0 - math.exp(-delta_v_rem_moon / c_e)
    fuel_saving_pct_moon = (prop_frac_moon_pure - prop_frac_moon_assisted) / prop_frac_moon_pure * 100.0

    prop_frac_surf_pure = 1.0 - math.exp(-delta_v_capture_at_surf / c_e)
    # 若在近木点制动前在卫星处先减速了 delta_v_flyby_max（能量降低等效），计算近木点速度降低
    v_peri_assisted = math.sqrt(2.0 * e_post + 2.0 * mu_J / R_JUPITER)
    delta_v_surf_assisted = max(0.0, v_peri_assisted - v_esc_J_surf)
    prop_frac_surf_assisted = 1.0 - math.exp(-delta_v_surf_assisted / c_e)
    fuel_saving_pct_surf = (prop_frac_surf_pure - prop_frac_surf_assisted) / prop_frac_surf_pure * 100.0

    return {
        "v_inf_arrival_km_s": v_inf,
        "moon_name": moon_name,
        "flyby_altitude_km": flyby_alt_km,
        "v_sc_at_moon_km_s": v_sc,
        "v_moon_orbit_km_s": v_m,
        "v_rel_km_s": v_rel,
        "deflection_deg": math.degrees(delta_rad),
        "delta_v_flyby_max_km_s": delta_v_flyby_max,
        "e_in_km2_s2": e_in,
        "delta_e_max_km2_s2": delta_e_max,
        "e_post_km2_s2": e_post,
        "is_captured": is_captured,
        "v_inf_post_km_s": v_inf_post,
        "delta_v_capture_at_moon_km_s": delta_v_capture_at_moon,
        "delta_v_capture_at_surf_km_s": delta_v_capture_at_surf,
        "fuel_saving_pct_moon": fuel_saving_pct_moon,
        "fuel_saving_pct_surf": fuel_saving_pct_surf
    }


def run_model(params: dict) -> dict:
    """
    规范接口：供 boundary_gate 与自动化工作流调用
    """
    v_inf = float(params.get("v_inf", 20.0))
    moon_name = str(params.get("target_moon", "Ganymede"))
    flyby_alt = float(params.get("flyby_altitude_km", 0.0))
    mu_m = params.get("mu_m", None)
    if mu_m is not None:
        mu_m = float(mu_m)

    res = calculate_flyby_dynamics(
        v_inf=v_inf,
        moon_name=moon_name,
        flyby_alt_km=flyby_alt,
        mu_m=mu_m
    )
    # primary_result 命名为 delta_v_flyby_max
    return {
        "delta_v_flyby_max": res["delta_v_flyby_max_km_s"],
        "delta_e_max": res["delta_e_max_km2_s2"],
        "e_post": res["e_post_km2_s2"],
        "is_captured": 1.0 if res["is_captured"] else 0.0,
        "details": res
    }


if __name__ == "__main__":
    # 快速自检打印
    print("=== 木星四颗伽利略卫星引力减速能力全面对比 (v_inf = 20 km/s) ===")
    for m in ["Io", "Europa", "Ganymede", "Callisto"]:
        r = calculate_flyby_dynamics(v_inf=20.0, moon_name=m, flyby_alt_km=0.0)
        print(f"[{m:8s}] 飞掠最大 Delta_v: {r['delta_v_flyby_max_km_s']:.4f} km/s | "
              f"能量削减: {r['delta_e_max_km2_s2']:.2f} km^2/s^2 | "
              f"飞掠后 v_inf: {r['v_inf_post_km_s']:.2f} km/s | "
              f"是否捕获: {r['is_captured']}")
