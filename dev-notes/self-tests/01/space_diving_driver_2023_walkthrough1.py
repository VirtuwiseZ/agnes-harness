"""Ad-hoc driver for the space-diving ODE model, source-agnostic per protocol.

Consumes the structured rho(z)/T(z) array produced upstream (Node 1.5) and the
domain hypothesis dict from space_diving_params.json + problem_state.json's
hypothesis_layer. Never references any named data source.
"""
import json
import math

import numpy as np
from scipy.integrate import solve_ivp

GM_EARTH = 3.986004418e14
R_EARTH = 6.371e6


def sound_speed(profile_T, z_grid_m, alt_m):
    """Local speed of sound from temperature profile (isothermal-ish local value)."""
    T = float(np.interp(alt_m, z_grid_m, profile_T))
    return math.sqrt(1.4 * 831.447 * T / 28.964)


def build_rhs(m_kg, profile_rho, profile_T, z_grid_m, z0_m, cd_tbl):
    def rhs(x, u):
        alt = max(0.0, z0_m - x[0])
        rho = float(np.interp(alt, z_grid_m, profile_rho))
        v = math.sqrt(max(u[0] * 2.0, 0.0))
        a_sound = sound_speed(profile_T, z_grid_m, alt)
        M = v / a_sound
        if M >= 1.2:
            cd, area = cd_tbl[2]
        elif M > 0.8:
            cd, area = cd_tbl[1]
        else:
            cd, area = cd_tbl[0]
        g_eff = GM_EARTH / (R_EARTH + alt) ** 2
        du_dx = g_eff - (rho * cd * area / (2.0 * m_kg)) * u[0]
        return [du_dx]
    return rhs


def run_single_descent(z0_m, m_kg, profile_rho, profile_T, z_grid_m, cd_tbl, n=1500):
    """Integrate from rest at z0 down to 1 m above ground.

    cd_tbl = [(cd_sub, A_sub), (cd_trans, A_sup), (cd_sup, A_sup)] keyed to
    Mach bands M<=0.8, 0.8<M<1.2, M>=1.2.
    """
    rhs = build_rhs(m_kg, profile_rho, profile_T, z_grid_m, z0_m, cd_tbl)
    x_eval = np.linspace(0.0, z0_m - 1.0, n)
    sol = solve_ivp(rhs, [0.0, z0_m - 1.0], [0.0], t_eval=x_eval,
                    method="RK45", rtol=1e-8, atol=1e-12)
    if not sol.success:
        raise RuntimeError(f"solve_ivp failed: {sol.message}")

    u = sol.y[0]
    v = np.sqrt(2.0 * np.clip(u, 0, None))

    def rho_at(alt):
        return float(np.interp(alt, z_grid_m, profile_rho))

    def a_at(alt, v_local):
        g_eff = GM_EARTH / (R_EARTH + alt) ** 2
        a_snd = sound_speed(profile_T, z_grid_m, alt)
        M = v_local / a_snd
        cd, area = cd_tbl[0]
        if M > 0.8:
            cd, area = cd_tbl[1]
        if M >= 1.2:
            cd, area = cd_tbl[2]
        return g_eff - (rho_at(alt) * cd * area / (2.0 * m_kg)) * v_local ** 2

    a = np.array([a_at(max(0.0, z0_m - xi), vi) for xi, vi in zip(sol.t, v)])

    # G-force time series: dt approx from altitude change / v (guard v->0)
    dt = np.empty_like(v)
    alt = z0_m - sol.t
    for i in range(len(v) - 1):
        dz = abs(alt[i] - alt[i + 1])
        v_mean = 0.5 * (v[i] + v[i + 1])
        dt[i] = (dz / v_mean) if v_mean > 1e-3 else 0.0
    dt[-1] = 0.0

    return {
        "x": sol.t, "alt": alt, "v": v, "a": a, "dt": dt,
        "max_v": float(np.max(v)),
        "max_abs_a": float(np.max(np.abs(a))),
        "max_Mach": float(np.max(v) / min(sound_speed(profile_T, z_grid_m, 0.0),
                                           sound_speed(profile_T, z_grid_m, alt.min()))),
    }


def sustained_g_exceeds(a_profile, dt_profile, G=5.0, Gtol=5.0):
    """Seconds during which |a|/g0 > G, using the per-row time bins."""
    g0 = 9.80665
    over = np.abs(a_profile) / g0 > G
    t = dt_profile[over].sum()
    return t, over.sum()


def peak_g_short(a_profile, G=10.0, tol_s=0.1, dt_profile=None):
    g0 = 9.80665
    return float(np.max(np.abs(a_profile)) / g0)


if __name__ == "__main__":
    state = json.load(open(r"E:\agnes-harness\program-design\runtime\problem_state_space_diving.json"))
    # The profile arrays are expected in numerical_artifacts, populated by Node 1.5
    art = state["numerical_artifacts"].get("atmosphere_profile", {})
    if not art:
        raise SystemExit("No atmosphere profile found in problem_state numerical_artifacts; run Node 1.5 first.")
    z_grid = np.asarray(art["z_m"], dtype=float)
    rho_grid = np.asarray(art["rho_kg_m3"], dtype=float)
    T_grid = np.asarray(art["T_K"], dtype=float)

    cd_tbl = [
        (1.0, 0.18),   # subsonic
        (5.0, 0.2),    # transonic
        (5.0, 0.2),    # supersonic band uses A_sup; CD sup set equal here pending adaptation
    ]
    res = run_single_descent(
        z0_m=39_000.0, m_kg=190.0,
        profile_rho=rho_grid, profile_T=T_grid, z_grid_m=z_grid, cd_tbl=cd_tbl,
    )
    print(json.dumps({
        "z0_km": 39.0,
        "max_v_m_s": res["max_v"],
        "max_abs_a_m_s2": res["max_abs_a"],
        "max_abs_a_g": res["max_abs_a"] / 9.80665,
        "max_Mach": res["max_Mach"],
    }, indent=2))
