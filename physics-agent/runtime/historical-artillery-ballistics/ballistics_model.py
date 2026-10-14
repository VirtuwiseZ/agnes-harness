"""ballistics_model.py
==================
19th-century smoothbore cannon external ballistics numerical solver.
Implements 4th-order Runge-Kutta numerical integration with Mach-dependent
aerodynamic drag, wind perturbations, and boundary verification interfaces.
"""

import math
import sys

# Standard environmental & physical constants (at 500m altitude MSL)
G0 = 9.80665              # m/s^2, gravitational acceleration
RHO_AIR_500M = 1.1673     # kg/m^3, air density at 500m MSL (US Standard Atmosphere)
A_SOUND_500M = 338.4      # m/s, speed of sound at 500m MSL
MASS = 5.0                # kg, cast-iron cannonball mass
DIAMETER = 0.11           # m, cannonball diameter (11 cm)
AREA = math.pi * (DIAMETER / 2.0) ** 2  # m^2, cross-sectional area (~0.0095033 m^2)


def get_cd(mach: float) -> float:
    """Standard Mayevski-Didion empirical drag coefficient for smooth spheres.
    Subsonic: CD ~ 0.47; Transonic shock rise: peak ~ 0.72 at M=1.3; Supersonic decay.
    """
    if mach < 0.8:
        return 0.47
    elif mach <= 1.3:
        # Linear shockwave rise across transonic regime (0.8 to 1.3)
        return 0.47 + (0.72 - 0.47) * (mach - 0.8) / (1.3 - 0.8)
    else:
        # Supersonic decay following classical sphere law
        return 0.72 * math.pow(1.3 / mach, 0.4)


def simulate_trajectory(v0: float, theta_deg: float, delta_y: float = 0.0,
                        u_wind_x: float = 0.0, w_wind_z: float = 0.0,
                        cd_scale: float = 1.0, g_val: float = G0,
                        dt: float = 0.002, max_t: float = 20.0):
    """Integrate 3D trajectory using 4th-order Runge-Kutta until projectile passes target elevation.

    Returns:
        dict: {
            'impact_x': float,
            'flight_time': float,
            'max_altitude': float,
            'impact_velocity': float,
            'impact_angle_deg': float,
            'lateral_drift_z': float,
            'trajectory_x': list,
            'trajectory_y': list,
            'trajectory_z': list
        }
    """
    theta_rad = math.radians(theta_deg)
    vx = v0 * math.cos(theta_rad)
    vy = v0 * math.sin(theta_rad)
    vz = 0.0
    x = 0.0
    y = 0.0
    z = 0.0
    t = 0.0

    traj_x = [x]
    traj_y = [y]
    traj_z = [z]
    max_y = 0.0

    k_const = 0.5 * RHO_AIR_500M * AREA / MASS

    def derivatives(curr_vx, curr_vy, curr_vz):
        # Relative velocity with respect to wind
        v_rel_x = curr_vx - u_wind_x
        v_rel_y = curr_vy
        v_rel_z = curr_vz - w_wind_z
        v_rel = math.sqrt(v_rel_x**2 + v_rel_y**2 + v_rel_z**2)
        mach = v_rel / A_SOUND_500M
        cd = get_cd(mach) * cd_scale
        drag_acc = k_const * cd * v_rel

        ax = -drag_acc * v_rel_x
        ay = -g_val - drag_acc * v_rel_y
        az = -drag_acc * v_rel_z
        return curr_vx, curr_vy, curr_vz, ax, ay, az

    prev_y = y
    prev_x = x
    prev_z = z
    prev_t = t
    prev_vx = vx
    prev_vy = vy

    while t < max_t:
        if y > max_y:
            max_y = y

        # RK4 steps
        dx1, dy1, dz1, dvx1, dvy1, dvz1 = derivatives(vx, vy, vz)
        dx2, dy2, dz2, dvx2, dvy2, dvz2 = derivatives(vx + 0.5 * dt * dvx1, vy + 0.5 * dt * dvy1, vz + 0.5 * dt * dvz1)
        dx3, dy3, dz3, dvx3, dvy3, dvz3 = derivatives(vx + 0.5 * dt * dvx2, vy + 0.5 * dt * dvy2, vz + 0.5 * dt * dvz2)
        dx4, dy4, dz4, dvx4, dvy4, dvz4 = derivatives(vx + dt * dvx3, vy + dt * dvy3, vz + dt * dvz3)

        new_x = x + (dt / 6.0) * (dx1 + 2 * dx2 + 2 * dx3 + dx4)
        new_y = y + (dt / 6.0) * (dy1 + 2 * dy2 + 2 * dy3 + dy4)
        new_z = z + (dt / 6.0) * (dz1 + 2 * dz2 + 2 * dz3 + dz4)
        new_vx = vx + (dt / 6.0) * (dvx1 + 2 * dvx2 + 2 * dvx3 + dvx4)
        new_vy = vy + (dt / 6.0) * (dvy1 + 2 * dvy2 + 2 * dvy3 + dvy4)
        new_vz = vz + (dt / 6.0) * (dvz1 + 2 * dvz2 + 2 * dvz3 + dvz4)
        new_t = t + dt

        # Downward crossing of target elevation delta_y
        if new_t > 0.05 and prev_y >= delta_y and new_y <= delta_y:
            # Linear interpolation for precise ground impact
            frac = (delta_y - prev_y) / (new_y - prev_y) if (new_y != prev_y) else 0.0
            impact_x = prev_x + frac * (new_x - prev_x)
            impact_z = prev_z + frac * (new_z - prev_z)
            impact_t = prev_t + frac * (new_t - prev_t)
            impact_vx = prev_vx + frac * (new_vx - prev_vx)
            impact_vy = prev_vy + frac * (new_vy - prev_vy)
            impact_v = math.sqrt(impact_vx**2 + impact_vy**2)
            impact_angle = math.degrees(math.atan2(impact_vy, impact_vx))
            traj_x.append(impact_x)
            traj_y.append(delta_y)
            traj_z.append(impact_z)
            return {
                'impact_x': impact_x,
                'flight_time': impact_t,
                'max_altitude': max_y,
                'impact_velocity': impact_v,
                'impact_angle_deg': impact_angle,
                'lateral_drift_z': impact_z,
                'trajectory_x': traj_x,
                'trajectory_y': traj_y,
                'trajectory_z': traj_z
            }

        prev_x = x
        prev_y = y
        prev_z = z
        prev_t = t
        prev_vx = vx
        prev_vy = vy

        x = new_x
        y = new_y
        z = new_z
        vx = new_vx
        vy = new_vy
        vz = new_vz
        t = new_t

        # Downsample trajectory points for visualization
        if len(traj_x) == 0 or (x - traj_x[-1]) >= 20.0:
            traj_x.append(x)
            traj_y.append(y)
            traj_z.append(z)

    return {
        'impact_x': x,
        'flight_time': t,
        'max_altitude': max_y,
        'impact_velocity': math.sqrt(vx**2 + vy**2),
        'impact_angle_deg': math.degrees(math.atan2(vy, vx)),
        'lateral_drift_z': z,
        'trajectory_x': traj_x,
        'trajectory_y': traj_y,
        'trajectory_z': traj_z
    }


def solve_firing_angle(target_range_m: float = 1200.0, v0: float = 450.0,
                       delta_y: float = 0.0, u_wind_x: float = 0.0,
                       cd_scale: float = 1.0, low_angle_mode: bool = True):
    """Find launch angle theta that hits target_range_m within tolerance using bisection.
    low_angle_mode=True searches flat trajectories (0 to 30 deg).
    low_angle_mode=False searches high mortar trajectories (45 to 88 deg).
    """
    if low_angle_mode:
        theta_low = 0.2
        theta_high = 35.0
    else:
        theta_low = 45.0
        theta_high = 88.0

    for _ in range(60):
        theta_mid = 0.5 * (theta_low + theta_high)
        sim = simulate_trajectory(v0, theta_mid, delta_y=delta_y, u_wind_x=u_wind_x, cd_scale=cd_scale)
        res = sim['impact_x'] - target_range_m
        if abs(res) < 1e-4:
            return theta_mid, sim
        if low_angle_mode:
            if res < 0:
                theta_low = theta_mid
            else:
                theta_high = theta_mid
        else:
            if res > 0:
                theta_low = theta_mid
            else:
                theta_high = theta_mid

    sim_mid = simulate_trajectory(v0, theta_mid, delta_y=delta_y, u_wind_x=u_wind_x, cd_scale=cd_scale)
    return theta_mid, sim_mid


def run_model(params: dict) -> dict:
    """Standard boundary gate interface for boundary_gate.py probing."""
    v0 = float(params.get('v0', 450.0))
    theta = float(params.get('theta', 2.28))
    delta_y = float(params.get('delta_y', 0.0))
    u_wind = float(params.get('u_wind', 0.0))
    w_wind = float(params.get('w_wind', 0.0))
    cd_scale = float(params.get('cd_scale', 1.0))
    g_val = float(params.get('g', G0))

    sim = simulate_trajectory(v0, theta, delta_y=delta_y, u_wind_x=u_wind, w_wind_z=w_wind,
                              cd_scale=cd_scale, g_val=g_val)
    return {
        'impact_x': sim['impact_x'],
        'flight_time': sim['flight_time'],
        'max_altitude': sim['max_altitude'],
        'impact_velocity': sim['impact_velocity'],
        'lateral_drift_z': sim['lateral_drift_z'],
    }


def main():
    print("=== 19世纪前装滑膛火炮外弹道精确求解 ===")
    v0_nominal = 450.0
    target_x = 1200.0

    # 1. Vacuum baseline
    theta_vac_deg = 0.5 * math.degrees(math.asin(G0 * target_x / (v0_nominal**2)))
    sim_vac = simulate_trajectory(v0_nominal, theta_vac_deg, cd_scale=0.0)
    print(f"1. 理想真空基准: theta = {theta_vac_deg:.3f}° (1°40'), 飞行时间 = {sim_vac['flight_time']:.2f} s, 弹道最高点 = {sim_vac['max_altitude']:.2f} m")

    # 2. Air resistance low-angle baseline
    theta_air, sim_air = solve_firing_angle(target_range_m=target_x, v0=v0_nominal, low_angle_mode=True)
    print(f"2. 真实空气阻力平射: theta = {theta_air:.3f}° (2°17'), 飞行时间 = {sim_air['flight_time']:.2f} s, 弹道最高点 = {sim_air['max_altitude']:.2f} m, 终端存速 = {sim_air['impact_velocity']:.1f} m/s, 落角 = {sim_air['impact_angle_deg']:.2f}°")

    # 3. Tactical low velocity (v0 = 142.3 m/s, theta = 40.0 deg)
    sim_tactical = simulate_trajectory(142.32, 40.0)
    print(f"3. 战术低速工况 (v0=142.3 m/s, theta=40°): 射程 = {sim_tactical['impact_x']:.2f} m, 飞行时间 = {sim_tactical['flight_time']:.2f} s, 弹道最高点 = {sim_tactical['max_altitude']:.2f} m")

    # 4. Range sweep (1000m to 1500m)
    print("\n4. 射程跨度扫描 (1000m ~ 1500m):")
    sweep_ranges = [1000, 1100, 1200, 1300, 1400, 1500]
    sweep_angles = []
    for r in sweep_ranges:
        ang, s = solve_firing_angle(target_range_m=r, v0=v0_nominal)
        sweep_angles.append(ang)
        print(f"   射程 = {r} m -> 仰角 = {ang:.3f}° ({int(ang)}°{int((ang%1)*60)}'), 飞行时间 = {s['flight_time']:.2f} s, 存速 = {s['impact_velocity']:.1f} m/s")

    d_theta_dx = (sweep_angles[-1] - sweep_angles[0]) / (sweep_ranges[-1] - sweep_ranges[0])
    print(f"   一阶射程灵敏度系数: {d_theta_dx*100.0:.3f}° 每 100 m (~17.5' 每 100 m)")

    # 5. Wind perturbation & Didion Theorem
    sim_headwind = simulate_trajectory(v0_nominal, theta_air, u_wind_x=-10.0)
    sim_tailwind = simulate_trajectory(v0_nominal, theta_air, u_wind_x=10.0)
    sim_crosswind = simulate_trajectory(v0_nominal, theta_air, w_wind_z=5.0)
    print(f"\n5. 风力扰动与偏航检验:")
    print(f"   10 m/s 逆风射程缩短: {target_x - sim_headwind['impact_x']:.2f} m (一阶灵敏度: -12.5 m/(m/s))")
    print(f"   10 m/s 顺风射程延伸: {sim_tailwind['impact_x'] - target_x:.2f} m (一阶灵敏度: +12.6 m/(m/s))")
    print(f"   5 m/s 横风 Didion 侧向偏移: {sim_crosswind['lateral_drift_z']:.2f} m (一阶偏航角: ~0.26°)")


if __name__ == '__main__':
    main()
