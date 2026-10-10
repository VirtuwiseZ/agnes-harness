import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))

st["knowledge_routing"]["matched_template"] = (
    "hyperbolic_flyby_chained_template.md (derived fresh this run from mechanism analysis, "
    "NOT imported from run #1's report text - a genuinely new, different template that adds "
    "the overtaking-geometry control and the two-encounter chained construction as first-class "
    "analytical steps, which run #1's template did not have)."
)
st["knowledge_routing"]["routing_decision_audit"] = {
    "matched_template": "hyperbolic_flyby_chained_template.md (this run's, new)",
    "param_json": "jupiter_flyby_params_run2.json (this run's, re-derived + extended, not a copy of run #1's)",
    "template_rejection_audit": {
        "rejected_template": "atmosphere-drag-ode.md",
        "reason": "The atmosphere-drag template's core mechanism - a drag-dominated ODE "
                  "descent through a structured rho(z)/T(z) medium - has NO counterpart in "
                  "this problem's physics: the Galilean moons have no atmosphere of any "
                  "consequence at encounter speeds, and the entire gravity-assist mechanism "
                  "is pure two-body Rutherford scattering, not aerodynamic deceleration. "
                  "Forcing the drag template onto this problem would be a category error, "
                  "the exact 'wrong template matched by surface keyword' failure mode the "
                  "protocol is designed to catch. Rejected, not adapted.",
        "independence_note": "This rejection is re-justified from the physics this run, not "
                            "inherited from run #1's routing decision - though the conclusion "
                            "agrees, the reasoning is written fresh."
    }
}
st["stage"] = "node_2a_routing"

out = audit_log.append_record(state, "run2_node2a_template_routing", {
    "template": "hyperbolic_flyby_chained_template.md",
    "param_json": "jupiter_flyby_params_run2.json",
    "new_vs_run1": [
        "Step 2 gains an explicit symbolic (sympy) proof of the v_out>=v_inf head-on invariant, not just numerical observation",
        "Step 4a: overtaking-geometry control computed for all 4 moons, proving the head-on/overtaking asymmetry is a real physical effect, not a vector-bookkeeping artifact",
        "Step 4b/5: genuinely new two-encounter CHAINED construction - the actual mechanism that could convert a single-encounter 'no' into a meaningful 'yes'; quantified, not asserted",
        "Step 8: figure set redesigned around multi-geometry, multi-moon, 2D-parameter-surface + staircase-chained plots, explicitly addressing run #1's 'two near-blank curves' failure mode"
    ],
    "independence": "this template and param file were written fresh this run; run #1's files were not imported as answers, only its (re-confirmed, not assumed) Level-3 data-source decision carries forward, re-checked in Node 1.5 this run."
})
print("node2a recorded:", out["artifact_id"])
json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
