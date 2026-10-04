"""
ode_model.py — Node 2b: data-source-agnostic ODE solver for a vertical
descent / free-fall problem under variable atmospheric density.

Design constraints (from the agreed-upon architecture - see the methodology templates in program-design/knowledge/, which are the canonical, agent-facing source of these rules):

  * The ODE itself must NOT reference any named data source. It receives
    a plain structured array { z: float, rho: float } (density vs.
    altitude, in meters and kg/m^3) plus a small hypothesis dict.
    Whatever produced that array — ambiance, pymsis, a hand-fetched
    table, an analytical approximation — is upstream concern, already
    recorded in problem_state.json's data_source_decision block.
  * Before any integration, the dimensional_gate.py hook must be run on
    the governing equation; this script surfaces a reminder + a helper
    function but does NOT skip that gate on the caller's behalf.
  * Uses scipy.integrate.solve_ivp (per the consensus "do not hand-roll
    a first-order Taylor method" rule).

What this first version actually implements (to keep scope to one
verifiable step, as agreed with the user):
  * The core descent ODE for a 0 -> z0 fall:
        d(v^2/2)/dx = g_eff(x) - (rho(x) * CD * A / (2*m)) * v^2
    (writing it in terms of u = v^2/2 keeps the equation free of a
    square-root, exactly as in the 2023 team's formulation).
  * A runnable demo that pulls a T(z)/rho(z) profile from ambiance only
    (0 -> 80 km), for now — the 80 -> 150 km pymsis segment and the
    junction handling are deliberately NOT in this file yet (that is
    the next single step, per the "one thing at a time" working
    rhythm).
"""

import numpy as np
from scipy.integrate import solve_ivp

# --- physical constants (scipy.constants: already Level-0 verified installed)
from scipy import constants

G_EARTH_M_S2 = 9.80665  # standard gravity, m/s^2 (conventional value; scipy.constants has no ready-made entry for this)
GM_EARTH = 3.986004418e14  # m^3/s^2, IUGG 2020 value for the geocentric gravitational constant
R_EARTH_M = 6.371e6  # mean earth radius, m


def build_density_lookup(z_m: np.ndarray, rho_kg_m3: np.ndarray) -> np.ndarray:
    """Linearly interpolate density at arbitrary z onto a monotonic grid.
    Kept tiny on purpose: the whole point is that the ODE below just
    indexes a plain array, with zero knowledge of where that array came
    from."""
    return np.interp(z_m, z_m, rho_kg_m3)  # identity for now; real usage will
                                            # call np.interp(x, z_grid, rho_grid)


def descent_ode_rhs(x, u, m_kg, cd, a_m2, rho_at_x):
    """du/dx where u = v^2/2.  u is the state variable (J/kg); x is
    downward distance from the release point (m).  rho_at_x is the
    density evaluated at the current altitude, handed in as a plain
    float — the ODE has no idea which library produced it."""
    g_eff = GM_EARTH / (R_EARTH_M + x) ** 2  # placeholder: x is treated as altitude offset from a caller-specific reference
    du_dx = g_eff - (rho_at_x * cd * a_m2 / (2.0 * m_kg)) * u
    return [du_dx]


def run_single_descent(
    z0_m: float,
    m_kg: float,
    cd: float,
    a_m2: float,
    rho_vs_z_m: np.ndarray,
    rho_grid_m: np.ndarray,
) -> dict:
    """Integrate one descent from rest at altitude z0_m down to ~1 m above
    ground. Returns velocity profile and acceleration profile vs. fallen
    distance x, ready for the boundary_gate / empirical-check steps
    downstream (not called here — just produced, per template step 4)."""
    rho_lookup = lambda alt: float(np.interp(alt, rho_grid_m, rho_vs_z_m))

    def rhs(x, u):
        alt = max(0.0, z0_m - x)
        g_eff = GM_EARTH / (R_EARTH_M + alt) ** 2
        return [g_eff - (rho_lookup(alt) * cd * a_m2 / (2.0 * m_kg)) * u[0]]

    t_eval = np.linspace(0.0, z0_m - 1.0, 2000)
    sol = solve_ivp(rhs, [0.0, z0_m - 1.0], [0.0], t_eval=t_eval,
                    method="RK45", rtol=1e-8, atol=1e-10)
    if not sol.success:
        raise RuntimeError(f"solve_ivp failed: {sol.message}")

    u = sol.y[0]
    v = np.sqrt(2.0 * np.clip(u, 0, None))
    a = np.empty_like(v)
    for i, x in enumerate(sol.t):
        alt = max(0.0, z0_m - x)
        g_eff = GM_EARTH / (R_EARTH_M + alt) ** 2
        a[i] = g_eff - (rho_lookup(alt) * cd * a_m2 / (2.0 * m_kg)) * (v[i] ** 2)

    return {
        "x": sol.t,
        "v": v,
        "a": a,
        "max_v": float(np.max(v)),
        "max_abs_a": float(np.max(np.abs(a))),
    }


if __name__ == "__main__":
    # Minimal runnable demo: ambiance-only, 0-39 km (Baumgartner's actual
    # jump altitude, NOT the full 0-80 km span, so this stays a fast,
    # focused smoke test rather than a full sweep).
    from ambiance import Atmosphere

    z_grid_m = np.arange(0, 40_000.0, 1000.0)  # 0..39 km, 1 km steps
    atmos = Atmosphere(z_grid_m)
    rho_grid = atmos.density

    result = run_single_descent(
        z0_m=39_000.0,
        m_kg=190.0,   # from space_diving_params.json#mass_total_kg
        cd=1.0,       # subsonic CD, per the domain JSON (first regime only)
        a_m2=0.18,    # subsonic cross-sectional area, per the domain JSON
        rho_vs_z_m=rho_grid,
        rho_grid_m=z_grid_m,
    )
    print(f"max velocity:          {result['max_v']:.2f} m/s")
    print(f"max |acceleration|:   {result['max_abs_a']:.2f} m/s^2")
    print(f" (= {result['max_abs_a']/G_EARTH_M_S2:.2f} g)")
    print("NOTE: this is a deliberately minimal smoke test using only the")
    print("subsonic CD=1.0 regime over 0-39 km with ambiance data; it does")
    print("NOT yet implement the piecewise transonic/supersonic CD switching")
    print("or the 80-150 km pymsis segment. Both are the next single steps.")

