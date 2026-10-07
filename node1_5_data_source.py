"""Node 1.5 data-source routing decision writer for 2025B_Artillery."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
state_path = os.path.join(HERE, "program-design", "runtime", "problem_state_2025B_artillery.json")

with open(state_path, "r", encoding="utf-8") as f:
    state = json.load(f)

state["data_source_decision"] = {
    "modeling_input_source": {
        "name": "ambiance (US Standard Atmosphere 1976-based), Python package",
        "access_method": "Level 0 - locally installed Python package (live import + sample call confirmed in this run)",
        "span_covered": "0-6 km (covers 500 m launch/target altitude + generous trajectory-apex margin; ambiance's stated validity extends far above this, so no out-of-span caveat needed for this problem)",
        "precision": "rho(z) ~0.5% relative (standard-atmosphere table resolution), sound_speed(z) to check Mach regime",
        "quantity_provided": "T(z), rho(z), speed_of_sound(z), P(z) as structured numpy arrays; consumed by the ODE code ONLY as plain arrays, never by package name (source-agnostic rule)",
    },
    "verification_baseline": {
        "name": "Uniform-density (constant rho) quadratic-drag closed-form / perturbation textbook result for projectile range — genuinely independent of any T(z)/rho(z) source, since it uses a single constant density (not a spatially-varying atmosphere table).",
        "independent_of": True,
        "citation": "Standard projectile-motion-with-quadratic-drag results (textbook-level, e.g. range formula with drag as a fraction of the vacuum range). Chosen SPECIFICALLY because the modeling input (ambiance's variable rho(z)) would otherwise be the natural 'real data' to validate against — using that same source to validate the model would violate the independence rule. A uniform-rho analytical result uses no such source at all, so independence holds trivially.",
    },
    "rationale": "Level 0 (ambiance) chosen over Level 1 (live atmospheric API) and Level 2 (published static table) because: (1) it is already installed and live-tested in THIS environment, not merely documented; (2) the required altitude span (a few km, centered on 500 m) is comfortably inside ambiance's stated validity, so no out-of-span fallthrough to a higher level is needed; (3) no network dependency at all. The verification baseline is deliberately a DIFFERENT, source-independent analytical object (uniform-density drag formula) so that 'model vs. baseline' is not 'atmosphere table vs. the same atmosphere table recomputed' — that would be circular validation.",
    "availability_check": {
        "ok": True,
        "sample_values_at_z_m": {
            "0": {"T_K": 288.15, "rho_kg_m3": 1.225, "speed_of_sound_m_s": 340.29, "P_Pa": 101325.0},
            "500": {"T_K": 284.9, "rho_kg_m3": 1.16727, "speed_of_sound_m_s": 338.37, "P_Pa": 95461.0},
            "3000": {"T_K": 268.66, "rho_kg_m3": 0.90925, "speed_of_sound_m_s": 328.58, "P_Pa": 70121.0},
        },
        "note": "Live call in this run (see audit_logs artifact for node_1_5_availability_check). No fallback needed; no human-intervention branch (Step 5a) triggered."
    },
    "manual_fetch_guide": None,
    "user_choice": None,
    "note": "Only Node 1.5 writes this; downstream data-source fallbacks must surface as an anomaly, not by editing this in place."
}

with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print("data_source_decision written")
