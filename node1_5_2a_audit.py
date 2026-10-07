"""Audit-log entries for Node 1.5 (ambiance availability sample) + Node 2a
(template-mechanism match check, logged as routing_decision_audit)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "program-design", "hooks"))
import audit_log

state = os.path.abspath(os.path.join(HERE, "program-design", "runtime", "problem_state_2025B_artillery.json"))

audit_log.append_record(
    state_path=state,
    source="ambiance_atmosphere_level0_sample",
    args={
        "z_m": [0, 500, 3000],
        "sample_values": {
            "0_m": {"T_K": 288.15, "rho_kg_m3": 1.225, "speed_of_sound_m_s": 340.29, "P_Pa": 101325.0},
            "500_m": {"T_K": 284.9, "rho_kg_m3": 1.16727, "speed_of_sound_m_s": 338.37, "P_Pa": 95461.0},
            "3000_m": {"T_K": 268.66, "rho_kg_m3": 0.90925, "speed_of_sound_m_s": 328.58, "P_Pa": 70121.0},
        },
        "note": "Live Level-0 import + sample call, confirming ambiance is installed, in-span for this problem (500 m target/launch altitude), and returns finite, physically sensible values. This is the 'exercised, not just imported' artifact data-source-routing.md Step 4 requires.",
    },
)

# --- Node 2a: template adaptation check, written as a routing_decision_audit entry
with open(state, "r", encoding="utf-8") as f:
    import json
    state_obj = json.load(f)

template_adaptation = {
    "matched_template": "program-design/knowledge/atmosphere-drag-ode.md",
    "param_json": "program-design/knowledge/artillery/artillery_params.json",
    "mechanism_match_check": {
        "template_built_around": "drag-dominated, 1D VERTICAL descent (space dive): the drag term g(z) - (rho(z)*CD*A/(2m))*v^2 is the defining force for the whole path, CD is regime-split across subsonic/transonic/supersonic (Mach-threshold switching), and the atmosphere's variable rho(z) must be integrated over the full vertical path end-to-end. Time-to-impact / velocity-profile shape is the headline quantity.",
        "this_problem_instantiates": "ballistic projectile MOTION, 2D (horizontal + vertical), fired at an angle, NOT a vertical drop from rest. Drag here is a CORRECTION to a vacuum-parabolic trajectory over ~1-1.5 km of flight, not the dominant force of the path. There is no 'impact velocity profile vs fallen distance' to optimize the way the template does; the target is a HIT CONDITION (x=R at z=z_target), solved for two free parameters (v0, theta).",
        "line_by_line_assumption_audit": [
            "VARIABLE-ALTITUDE RHO(Z) ODE INTEGRATION: PARTIALLY APPLIES - the trajectory's apex likely exceeds 500 m (needs checking), so a modest variable-rho(z) is warranted, but over a much narrower altitude band than the template's 0-150 km span; this problem's altitude span is a few km, not hundreds.",
            "CD REGIME SPLITTING (subsonic/transonic/supersonic, with Mach-threshold switching like the template's step 2): INHERITED-BUT-NEEDS-RE-EXAMINATION - the projectile's Mach number at these altitudes (sound speed ~338-340 m/s at 0-500 m) is v0/340, which for v0 ~ 110-450 m/s is ~0.3 to ~1.3 - the flight can cross the transonic band partway through its path. This is analogous to the template's regime-split idea in PRINCIPLE, but the specific thresholds/CD values in the template (0.8/1.25, CD 1.0/5.0/1.2) are for a human-jumper's parachute/terminal regime, NOT for a solid steel cannonball - they must be re-derived for a smooth sphere, not reused.",
            "VERTICAL-1D-OVER-DISTANCE (template's dv/dx with x = fallen distance): DOES NOT DIRECTLY APPLY - this problem is 2D with independent x(t), z(t) motion, not a 1D ODE in fallen distance; the template's ODE structure must be re-expressed as two coupled ODEs in t (x', z', or equivalently x as independent variable with dx/dt = v_x), not reused verbatim.",
            "SWEPT-EXTREMUM / MONOTONICITY BOUNDARY CHECKS (template's step 4-5, checking a max/min of some profile vs an input parameter): THE MECHANISM TRANSFERS (check a boundary limit like CD->0 giving vacuum range, or v->0 giving zero range), but the specific 'maximum safe altitude' quantity being optimized in the template has NO counterpart here - this problem's target is a discrete hit condition, not an extremum over a sweep.",
        ],
        "conclusion": "Template matches at the GENERAL PHYSICS domain (a projectile through a variable-density atmosphere, with drag as a force term and a CD/A coupling coefficient) and its STRUCTURE (gate first, then ODE, then boundary + independent verification) transfers well. But its specific ODE form (1D-in-fallen-distance), its CD regime values, and its 'max safe altitude' optimization target are inherited-from-the-example and MUST NOT be reused without re-derivation for this problem's 2D hit-condition structure and solid-sphere CD values.",
    },
}

state_obj["knowledge_routing"] = template_adaptation

with open(state, "w", encoding="utf-8") as f:
    json.dump(state_obj, f, indent=2, ensure_ascii=False)

audit_log.append_record(
    state_path=state,
    source="node_2a_template_adaptation_check",
    args={
        "matched_template": template_adaptation["matched_template"],
        "key_findings": [
            "1D-in-fallen-distance ODE form does NOT directly apply; re-expressed as 2D (x,z) vs t",
            "CD regime values (0.8/1.25, 1.0/5.0/1.2) are inherited from the space-diving example and are NOT valid for a solid cannonball - re-derived for a smooth sphere",
            "Template's 'maximum safe altitude' optimization target has no counterpart in this problem's discrete hit-condition structure; boundary/monotonicity check structure still transfers, applied to a different quantity (hit distance vs v or theta)",
        ],
    },
)
print("Node 1.5 + Node 2a audit entries written")
