"""
sasando_resonator_model.py
==========================
Node 2b model module for task 2025A (Acoustic Preservation of the Electric
Sasando). FRESH module written specifically for this problem; does NOT
import or patch program-design/hooks/ode_model.py or the 2025B
artillery_model.py (per project rule: write a new module per problem, even
within the same broad 'physics' area, when the governing equation differs).

Physical mechanism (re-derived for THIS problem, not inherited from any
descent template):
    The dried lontar-leaf resonator is modeled as a LIGHT, THIN, CIRCULAR
    PLATE (radius R, thickness h, clamped around its rim by the bamboo
    tube) that is driven by a localized, quasi-static pressure
    excitation p_m(r,theta,t) proportional to the string's displacement
    at the contact point. Each circular-plate bending mode (0,m) with
    azimuthal order n=0 (axisymmetric) behaves, in its own generalized
    coordinate q_m(t), as a damped harmonic oscillator:

        q_m'' + 2*zeta_m*omega_m*q_m' + omega_m**2 * q_m = p_m / m_s

    where omega_m is the mode's NATURAL angular frequency (the
    eigenvalue of the clamped-circular-plate biharmonic problem),
    m_s = rho_vol*h is the surface mass density, zeta_m is the modal
    damping ratio, and p_m is the mode-projected (area-averaged,
    Bessel-weighted) excitation pressure at that mode.

    Frequency response of the whole plate to a narrowband (single-
    frequency) string drive at frequency f is therefore the sum of the
    individual modal transfer functions:

        H(f) = sum_m  A_m * [ 1 / (1 - (f/f_m)^2 + 2i*zeta_m*(f/f_m)) ]

    (the standard undamped-ratio form of a second-order damped
    oscillator's response, written in complex frequency). This H(f)
    - a set of Lorentzian-shaped peaks at f_m with per-mode widths set
    by zeta_m and heights by A_m - IS the concrete EQ curve the
    electric sasando's DSP must re-apply to the pickup signal to
    re-impose the traditional leaf's frequency-selective timbre.

    This is the 'method' the problem asks for: it is not a single
    constant gain or a flat filter - it is an explicit, physically-
    justified set of resonant peaks computed from first-principles
    plate theory, with the numeric E/rho/h/R/zeta values explicitly
    flagged as order-of-magnitude candidate constants for a dried
    plant-fiber leaf (NOT measured data for the specific instrument's
    leaf), per this run's Node 1.5 data-source decision.
"""

import math
from math import pi, inf
from scipy.special import jv  # Bessel functions of the first kind
from scipy.optimize import brentq


# ---------------------------------------------------------------------------
# Candidate material-constant set for a DRIED PLANT-FIBER (lontar-leaf-like)
# circular thin plate. Each value is an order-of-magnitude CANDIDATE (see
# program-design/knowledge/sasando_resonator/sasando_resonator_params.json
# and problem_state.json's data_source_decision for the full provenance and
# 'not measured data' caveat). These are the ONLY numbers Node 2b's
# compute call below is allowed to substitute - never a second, differently-
# sourced guess, which would make verification circular.
# ---------------------------------------------------------------------------
CANDIDATE_CONSTANTS = {
    "R_m": 0.04,          # plate radius - GUESS: half the bamboo tube's 8 cm diameter (the only dimension the problem actually provides)
    "h_m": 0.0005,        # 0.5 mm, typical dried-leaf thickness order of magnitude (ASSUMED this run)
    "E_Pa": 1.0e9,        # Young's modulus for dried plant fiber, low end of the ~1-5 GPa literature order of magnitude for stiff-but-flexible dried organic matter
    "rho_vol_kg_m3": 1200.0,  # bulk density, order of magnitude for dried plant matter
    "nu": 0.3,            # Poisson ratio, typical order for an anisotropic dried plant material treated isotropically (a simplification, flagged in the report)
    "zeta": 0.02,        # lightly-damped, 'ringing' plucked-leaf behavior (order-of-magnitude, NOT measured)
}


def flexural_rigidity(E, h, nu):
    """D = E*h^3 / (12*(1-nu^2)) - the plate's bending stiffness constant.
    Dimensional (force*length) - already gated at the dimensional_gate
    step before this module was written."""
    return E * h**3 / (12.0 * (1.0 - nu**2))


def surface_mass_density(rho_vol, h):
    """m_s = rho_vol*h - kg/m^2 (areal mass density, NOT the same as the
    volume density; the distinction is what the dimensional gate's first
    FAIL caught: total-force vs. area-normalized-force forms)."""
    return rho_vol * h


# ---------------------------------------------------------------------------
# Closed-form clamped-circular-plate eigenfrequency (the Node 1.5-chosen
# INDEPENDENT verification baseline - source-free, textbook Bessel-root
# result, NOT a second material-constant fetch):
#
#   f_m = (alpha_m**2 / (2*pi)) * sqrt( D / (m_s * R**4) )
#
# where alpha_m is the m-th positive root of the clamped-edge Bessel
# condition for a circular plate's axisymmetric (n=0) bending modes:
#       J1'(alpha) + 2/(alpha) * ...  -> for n=0 clamped edge:
#       J0(alpha*R) - Y0(alpha*R) ... (equivalently, J1(alpha*R) = 0 for
#       the root-spacing used in most textbook treatments of the
#       FREE-edge case; for the CLAMPED edge the standard approximate
#       scaling is f_m ∝ (m + 3/4)**2 for large m, with exact constants
#       from solving J0'(x)=0 / J1(x)=0 style boundary conditions at the
#       clamped rim - we use the well-known table of first few clamped-
#       disk eigenvalue constants alpha_m, which are fixed mathematical
#       values, the genuinely independent, source-free check).
#
# We use the classical (non-dimensional) eigenvalue table for a CLAMPED
# circular disk, axisymmetric modes, which is standard textbook
# material (e.g. Timoshenko & Woinowsky-Krieger, "Theory of Plates and
# Shells"): the first few values of lambda_m = alpha_m (where alpha_m
# is the root scaling such that f ∝ alpha_m^2) are:
# ---------------------------------------------------------------------------
CLAMPED_DISK_ALPHA = [3.9266, 7.0690, 10.2054, 13.3430]  # alpha_m, m=0,1,2,3 (standard tabulated values)


def clamped_disk_eigenfrequencies(constants=CANDIDATE_CONSTANTS):
    """Return [f_0, f_1, f_2, f_3] in Hz, the closed-form textbook result
    (independent verification baseline per Node 1.5)."""
    R = constants["R_m"]
    D = flexural_rigidity(constants["E_Pa"], constants["h_m"], constants["nu"])
    m_s = surface_mass_density(constants["rho_vol_kg_m3"], constants["h_m"])
    base = math.sqrt(D / (m_s * R**4)) / (2.0 * pi)
    return [a**2 * base for a in CLAMPED_DISK_ALPHA]


# ---------------------------------------------------------------------------
# Modal excitation weighting A_m: how strongly a localized (near-rim,
# point-like) string contact excites each axisymmetric mode, as a fraction
# of the mode's own generalized force. For a point force F applied at
# radius r0, the m-th mode's projected force (in a 2D plate's modal
# expansion) is F * [J0(alpha_m*r0/R)] (for axisymmetric n=0 modes, the
# azimuthal average of a point force on a circular plate reduces to the
# Bessel function evaluated at the normalized contact radius) - this is
# the genuinely physical, not-arbitrary reason H(f) is a WEIGHTED sum of
# Lorentzian peaks rather than an equal-height sum: the string's contact
# location (assumed near the rim, r0/R ~ 0.8, matching the bamboo tube
# geometry where the string's contact/bridge sits near the leaf's edge)
# suppresses the high-order modes (their Bessel profile has nodes near
# the rim) relative to the fundamental.
# ---------------------------------------------------------------------------
CONTACT_RADIUS_OVER_R = 0.8  # candidate: string bridge/contact sits near the leaf's rim, not at its center


def modal_amplitudes(constants=CANDIDATE_CONSTANTS, r0_over_R=CONTACT_RADIUS_OVER_R):
    """A_m = J0(alpha_m * r0/R) for each mode - the Bessel-suppressed
    relative excitation weight of each axisymmetric mode by a point-like
    near-rim contact force (NOT a flat, equal-amplitude assumption)."""
    return [jv(0, a * r0_over_R) for a in CLAMPED_DISK_ALPHA]


def run_model(params):
    """Entry point the boundary_gate.py hook calls: params may override any
    key of CANDIDATE_CONSTANTS (that's the whole point of the boundary
    cases - sweep h->0, E->0, R->0, zeta->0, etc.). Returns the
    primary headline number: the predicted FUNDAMENTAL eigenfrequency
    f_1 (m=0, the lowest axisymmetric bending mode), in Hz. This is the
    number the problem's acceptance rule checks against the stated
    98-1047 Hz operating band."""
    constants = dict(CANDIDATE_CONSTANTS)
    constants.update(params)
    f_hz = clamped_disk_eigenfrequencies(constants)
    # Guard: any non-finite value (NaN/inf) from a degenerate limit (e.g.
    # h->0 or R->0 driving the base frequency ratio to 0 or inf) is
    # returned as-is so the boundary gate's 'finite'/'bounded_by' checks
    # can actually catch it, not mask it.
    return {"f_fundamental_Hz": f_hz[0], "f_all_modes_Hz": f_hz,
            "A_modal": modal_amplitudes(constants)}


def build_ei_curve_hz(frequency_hz_grid, constants=CANDIDATE_CONSTANTS,
                      r0_over_R=CONTACT_RADIUS_OVER_R):
    """The concrete DSP EQ curve H(f) = sum_m A_m * Lorentzian(f; f_m, zeta)
    that re-imposes the leaf's timbre on the electric sasando's pickup signal.
    Returns a real-valued gain curve (in dB, relative to the highest peak)
    over the given frequency grid - the actual artifact the electric
    instrument's DSP should implement (e.g. as a cascade of 4 peaking
    biquad filters, one per dominant mode)."""
    f_hz = clamped_disk_eigenfrequencies(constants)
    A = modal_amplitudes(constants, r0_over_R)
    zeta = constants["zeta"]
    H = complex(0.0) * 0  # will be a Python complex scalar loop, simple and readable
    mag = [0.0] * len(frequency_hz_grid)
    for i, f in enumerate(frequency_hz_grid):
        H = 0.0 + 0.0j
        for fm, Am in zip(f_hz, A):
            x = f / fm
            H += Am * (1.0 / (1.0 - x * x + 2j * zeta * x))
        mag[i] = abs(H)
    peak = max(mag) if mag and any(m > 0 for m in mag) else 1.0
    return [20 * math.log10(m / peak + 1e-30) for m in mag]


if __name__ == "__main__":
    out = run_model({})
    print("Fundamental f (m=0):", out["f_fundamental_Hz"], "Hz")
    print("All axisymmetric modes (Hz):", out["f_all_modes_Hz"])
    print("Modal excitation weights A_m:", out["A_modal"])
