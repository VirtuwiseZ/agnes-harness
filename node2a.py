import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby.json"
with open(state, "r", encoding="utf-8") as f:
    st = json.load(f)

# --- Node 2a: mechanism-match check (written, per protocol) ---
routing = st["knowledge_routing"]
routing["matched_template"] = "DERIVED (no existing template in program-design/knowledge/ covers a two-body hyperbolic flyby/gravity-assist mechanism; the only present ODE template, atmosphere-drag-ode.md, is built around atmospheric drag force - a fundamentally different mechanism from momentum exchange with a moving planet/moon - and was explicitly checked and rejected for this problem, see below)"
routing["param_json"] = "program-design/knowledge/jupiter_flyby/jupiter_flyby_params.json"
routing["routing_decision_audit"] = {
    "templates_considered": [
        {
            "template": "program-design/knowledge/atmosphere-drag-ode.md",
            "mechanism_this_template_is_built_around": "continuous dissipative drag force F_drag = (1/2)*rho(z)*CD*A*v^2 acting on a body descending through a spatially-varying atmosphere, integrated as an ODE over altitude - energy is irreversibly lost to the medium",
            "mechanism_this_problem_instantiates": "impulsive, conservative momentum exchange between a test-mass spacecraft and a single gravitating body (the moon) during a flyby - a two-body Kepler encounter with no atmosphere, no dissipation; energy in the moon's own frame is exactly conserved, and the observed Jupiter-frame energy change is purely a kinematic-frame effect (velocity vector rotation). This is the standard 'gravity assist / Oberth-effect-free slingshot' mechanism, which is mechanically categorically different from drag-based descent: no medium, no CD/A coefficients, no altitude-varying density field, no ODE over altitude - instead a closed-form hyperbolic-encounter kinematics + one vis-viva energy comparison.",
            "verdict": "NOT A MATCH - rejected. Using it here would be the classic '张冠李戴' (mismatched-template) failure mode the protocol warns against: same broad topic ('slowing something down') but a different physical mechanism (dissipative vs. impulsive-conservative). No assumptions from that template are inherited into this run."
        },
        {
            "template": "(derived fresh this run) two-body hyperbolic gravity-assist mechanism template",
            "mechanism": "Closed-form Rutherford/hyperbolic encounter: (1) moon-frame approach speed = relative speed at infinity of the hyperbola; (2) turning angle delta = 2*asin(1/e) where e = 1 + r_p*v_inf_rel^2/mu_m; (3) Jupiter-frame exit velocity = vector sum of moon's orbital velocity + rotated exit velocity of magnitude v_inf_rel; (4) minimize |exit| by maximizing the anti-alignment of the rotated leg with -v_moon (head-on geometry, perigee placed ahead of the moon's motion); (5) check whether reduced v_out still supports a bound Jovian orbit at a chosen perijove (vis-viva); (6) compare the single-burn capture delta-v with and without the assist (Tsolkovsky for propellant fraction).",
            "steps": [
                "S1: compute per-moon v_orb = sqrt(mu_j/a_m), v_esc_moon_surface = sqrt(2*mu_m/R_m)",
                "S2: for a chosen perigee r_p (= R_m, the tightest safe flyby), compute hyperbolic eccentricity e and turning angle delta",
                "S3: Jupiter-frame minimal exit speed v_out_min = |v_moon| - |v_rel_out| if fully anti-aligned, else sqrt(v_moon^2 + v_rel^2 - 2*v_moon*v_rel*cos(delta/2)) (geometric derivation, verified numerically too)",
                "S4: bound-orbit test: is v_out_min^2 + 2*mu_j/r_perijove_target < 0?",
                "S5: capture delta-v comparison (direct burn vs. burn after assist) at fixed target orbit",
                "S6: propellant-mass fraction via Tsiolkovsky, Isp baseline 450 s, for a representative spacecraft"
            ],
            "failure_rollback_triggers": [
                "if S3's minimal v_out exceeds v_inf itself (would mean the 'assist' increased speed) -> sign/geometry error, roll back to S2's angle convention",
                "if S4 fails for every moon (no bound orbit even at r_p=R_m) -> the assumption that a single flyby suffices must be re-examined (chained flybys), not silently patched",
                "if e < 1 in S2 -> r_p too large for a hyperbolic encounter at this v_inf; use a smaller r_p or flag as an ellipse (not a flyby)"
            ],
            "verdict": "This derived template is what this run actually uses. All steps S1-S6 are implemented in a fresh module (not imported from atmosphere-drag-ode.md's example)."
        }
    ]
}

st["stage"] = "node_2a_routing"

with open(state, "w", encoding="utf-8") as f:
    json.dump(st, f, indent=2, ensure_ascii=False)

out = audit_log.append_record(state, "node2a_template_routing", {
    "action": "mechanism-match check: rejected atmosphere-drag-ode.md (wrong mechanism, documented), derived a fresh two-body hyperbolic gravity-assist template; recorded full step list + failure-rollback triggers",
    "template_derived_in_place_of": "atmosphere-drag-ode.md (rejected)"
})
print("recorded:", out["artifact_id"])

# write-back verification
with open(state, "r", encoding="utf-8") as f:
    st2 = json.load(f)
print("stage now:", st2["stage"])
print("knowledge_routing.matched_template set:", st2["knowledge_routing"]["matched_template"] is not None)
print("audit count:", len(st2["audit_logs"]))
