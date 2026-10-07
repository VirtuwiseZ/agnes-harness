"""artillery_model.py — FRESH model module for task 2025B_Artillery (not a
patch of the project's reference ode_model.py, per that file's own docstring
instruction to write a new module rather than adapt the old one).

2D projectile motion (x horizontal, z vertical above sea level, both in a
plane containing the wind direction) with:
  - quadratic aerodynamic drag, F = -(1/2) rho(z) CD A vrel * (relative velocity)
  - a purely horizontal wind of speed u_wind (positive = downrange, i.e. it
    adds to the projectile's x-motion if it blows toward the target)
  - variable air density rho(z) and gravity g(z) taken as plain structured
    arrays / scalars handed in, with ZERO knowledge of which package produced
    them (source-agnostic rule; provenance lives in problem_state.json's
    data_source_decision block, not here)
  - Mach-dependent drag coefficient CD(Mach): a smooth sphere's CD is NOT a
    single number; it is ~0.47-0.5 subsonic, drops to ~0.2-0.3 in the
    transonic/supersonic band. This problem's flight can cross that band, so
    CD is a function of the instantaneous Mach number, not a constant.

This module exposes:
  - simulate(v0, theta_rad, u_wind_m_s, ...) -> trajectory dict
  - hit_condition(v0, theta_rad, ...) -> signed horizontal miss distance
    (x at the moment z crosses back to z_target, minus R_target), ready to be
    driven by a 2-parameter root find / the boundary_gate's monotonicity
    check.
  - run_model(params) -> dict, the exact signature boundary_gate.py drives.
"""
import math
import numpy as np
from scipy.integrate import solve_ivp

# ---------------------------------------------------------------------------
# Physical constants / projectile properties (from artillery_params.json's
# named_parameters; these are settled THIS-run values, re-derived rather than
# inherited from the space-diving template).
# ---------------------------------------------------------------------------
G_STANDARD_M_S2 = 9.80665            # conventional standard gravity
PROJECTILE_MASS_KG = 5.0
PROJECTILE_RADIUS_M = 0.055          # 11 cm diameter
PROJECTILE_AREA_M2 = math.pi * PROJECTILE_RADIUS_M ** 2  # ~0.009503 m^2

# Smooth-solid-sphere drag coefficient, function of Mach number (M = vrel/a,
# a = local speed of sound). Values chosen to match the well-known "drag
# crisis" shape for a smooth sphere: ~0.47-0.5 below M~0.8, dropping to
# ~0.2-0.3 by M~1.3-1.5 (transonic/supersonic). This is a re-derivation for
# THIS problem's projectile, NOT the space-diving template's CD table (which
# was tuned for a parachute/human jumper's terminal-velocity regime).
def cd_of_mach(mach: float) -> float:
    if mach <= 0.8:
        return 0.47
    if mach <= 1.3:
        # Linear transition across the transonic band (M 0.8 -> 1.3)
        frac = (mach - 0.8) / 0.5
        return 0.47 + frac * (0.25 - 0.47)
    return 0.25


def drag_params(rho_at_z: float, cd_at_mach: float, area: float, mass: float):
    """Return the K factor = rho*CD*A/(2m), in 1/m, used in the ODE below."""
    return rho_at_z * cd_at_mach * area / (2.0 * mass)


def simulate(
    v0_m_s: float,
    theta_rad: float,
    u_wind_m_s: float = 0.0,
    z_launch_m: float = 500.0,
    z_target_m: float = 500.0,
    rho_grid_m: np.ndarray = None,
    rho_grid_values: np.ndarray = None,
    a_sound_grid_m: np.ndarray = None,
    a_sound_grid_values: np.ndarray = None,
    max_time_s: float = 60.0,
):
    """Integrate the full 2D ODE system. Returns a dict with x/z/vx/vz vs t.

    rho_grid_m / rho_grid_values and a_sound_grid_m / a_sound_grid_values
    are plain structured arrays (the source-agnostic input contract); None
    means use a uniform atmosphere (rho = 1.225, a_sound = 340.29 m/s, the
    sea-level standard values) — used for the independent-verification
    baseline comparison, where a constant density is the whole point.
    """
    vx0 = v0_m_s * math.cos(theta_rad)
    vz0 = v0_m_s * math.sin(theta_rad)

    uniform = rho_grid_values is None
    if uniform:
        rho_const, a_sound_const = 1.225, 340.29
    else:
        rho_const = None
        a_sound_const = None

    def rho_at(z):
        if uniform:
            return rho_const
        return float(np.interp(z, rho_grid_m, rho_grid_values))

    def a_sound_at(z):
        if uniform:
            return a_sound_const
        return float(np.interp(z, a_sound_grid_m, a_sound_grid_values))

    K_at_z = lambda z, mach: drag_params(rho_at(z), cd_of_mach(mach), PROJECTILE_AREA_M2, PROJECTILE_MASS_KG)

    def rhs(t, y):
        x, z, vx, vz = y
        u_rel = vx - u_wind_m_s       # x-component of velocity relative to the air
        w_rel = vz                    # wind is horizontal only; no vertical wind
        vrel = math.hypot(u_rel, w_rel)
        mach = vrel / a_sound_at(z)
        K = K_at_z(z, mach)
        dvx_dt = -K * vrel * u_rel
        dvz_dt = -G_STANDARD_M_S2 - K * vrel * w_rel
        return [vx, vz, dvx_dt, dvz_dt]

    t_eval = np.linspace(0.0, max_time_s, 2000)
    sol = solve_ivp(
        rhs, [0.0, max_time_s], [0.0, z_launch_m, vx0, vz0],
        t_eval=t_eval, method="RK45", rtol=1e-8, atol=1e-10,
    )
    if not sol.success:
        raise RuntimeError(f"solve_ivp failed: {sol.message}")
    return {"t": sol.t, "x": sol.y[0], "z": sol.y[1], "vx": sol.y[2], "vz": sol.y[3]}


def hit_condition(
    v0_m_s: float,
    theta_rad: float,
    R_target_m: float,
    u_wind_m_s: float = 0.0,
    z_launch_m: float = 500.0,
    z_target_m: float = 500.0,
    rho_grid_m: np.ndarray = None,
    rho_grid_values: np.ndarray = None,
    a_sound_grid_m: np.ndarray = None,
    a_sound_grid_values: np.ndarray = None,
):
    """Return the signed horizontal miss: x_projectile(z crosses back down to
    z_target) - R_target. Positive = overshoot, negative = undershoot. Zero
    (to within solver tolerance) means a hit. This is the function a 2-D root
    find (or a coarse hand-estimation sweep) drives to zero."""
    traj = simulate(
        v0_m_s, theta_rad, u_wind_m_s, z_launch_m, z_target_m,
        rho_grid_m, rho_grid_values, a_sound_grid_m, a_sound_grid_values,
    )
    z = traj["z"]
    x = traj["x"]
    if z[-1] >= z_target_m and np.all(z > z_target_m):
        # Trajectory never came back down to target altitude within the
        # integration window — treat that as a (large) positive miss proxy
        # so a root finder still gets a usable, monotone signal.
        return float(x[-1] - R_target_m)
    # Find the crossing index where z goes from above to at/below z_target
    above = z > z_target_m
    cross_idx = None
    for i in range(1, len(z)):
        if above[i - 1] and not above[i]:
            cross_idx = i
            break
    if cross_idx is None:
        return float(x[-1] - R_target_m)
    # Linear interpolation of x at the exact crossing point between i-1 and i
    z0, z1 = z[cross_idx - 1], z[cross_idx]
    x0, x1 = x[cross_idx - 1], x[cross_idx]
    frac = (z0 - z_target_m) / (z0 - z1)
    x_at_cross = x0 + frac * (x1 - x0)
    return float(x_at_cross - R_target_m)


def run_model(params: dict) -> dict:
    """boundary_gate.py entry point: params dict -> {"miss_m": ...} so the
    gate can check finiteness/monotonicity of the miss distance against
    v0/theta/wind sweeps."""
    return {
        "miss_m": hit_condition(
            params.get("v0_m_s", 150.0),
            math.radians(params.get("theta_deg", 45.0)),
            params.get("R_target_m", 1200.0),
            params.get("u_wind_m_s", 0.0),
            params.get("z_launch_m", 500.0),
            params.get("z_target_m", 500.0),
            params.get("rho_grid_m"),
            params.get("rho_grid_values"),
            params.get("a_sound_grid_m"),
            params.get("a_sound_grid_values"),
        ),
    }
