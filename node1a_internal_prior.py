"""Writes the internal_prior field into problem_state_2025B_artillery.json
(Node 1a rule: private intuition-only sketch, never shown to user or cited
in the report; only permitted later use is a divergence check against Node 2b's
verified result)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
state_path = os.path.join(HERE, "program-design", "runtime", "problem_state_2025B_artillery.json")

with open(state_path, "r", encoding="utf-8") as f:
    state = json.load(f)

state["internal_prior"] = {
    "_note": "Private Node-1a intuition sketch ONLY. Not evidence. Never cited in the report or shown to the user. The only permitted later use is a conscious divergence check against Node 2b's gate-verified result, logged as an internal_prior_divergence audit record if it is large.",
    "sketch": (
        "Regime: ballistic-dominated, not drag-dominated. v_muzzle of a few hundred m/s "
        "with a 5 kg solid sphere means drag is a correction to a vacuum-ballistic "
        "trajectory over ~1.2 km of flight, not the defining physics of the whole path "
        "(contrast: the space-diving template is drag-dominated end-to-end). "
        "Order of magnitude from the vacuum range formula R = v^2 sin(2t)/g: for R=1200 m "
        "and g=9.8 m/s^2, v^2 = 1200*9.8/sin(2t); at t=30 deg (sin60=0.866), "
        "v ~ 116 m/s; at t=45 deg, v ~ 108 m/s; so the required v is roughly 110-130 m/s "
        "range, well under the 450 m/s cap even before drag is added, so drag likely "
        "pushes the true required v up by maybe 10-30% (a few tens of m/s), landing "
        "around ~130-170 m/s with t somewhere around 35-50 deg. The 450 m/s cap is "
        "therefore headroom, not the binding constraint, for the 1200 m case specifically. "
        "Wind is a secondary perturbation: a headwind simply shifts the required v/angle "
        "pair, not the regime."
    ),
}

with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print("internal_prior written")
