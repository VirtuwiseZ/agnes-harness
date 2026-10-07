"""One-off Node 1 audit log entry writer. Run once, then deleted; later entries
use the audit_log.py CLI or a similar small helper script with proper absolute
paths. (Windows/PowerShell 5.1 quoting makes inline-quoted JSON args awkward;
a small script file with a plain string avoids that problem.)"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "program-design", "hooks"))
import audit_log

state = os.path.join(HERE, "program-design", "runtime", "problem_state_2025B_artillery.json")
state = os.path.abspath(state)
print("state =", state)

audit_log.append_record(
    state_path=state,
    source="node_1_task_spec",
    args={
        "problem_id": "2025B_Artillery",
        "note": "Task spec written: target = (v_muzzle, theta) hit pair for the 1200 m / both-ends-500 m case, plus a hand-computable estimation method generalized across 1000-1500 m range, varied altitudes, varied wind. Hard cap: v_muzzle <= 450 m/s (the era's stated 'up to' limit).",
    },
)
audit_log.append_record(
    state_path=state,
    source="node_1_internal_prior",
    args={
        "note": "internal_prior sketch recorded in problem_state.json's dedicated field: private intuition-only estimate, NOT evidence. Dominant regime expected to be ballistic (drag is a correction, not a regime-defining force like in the space-diving template) because v~300-450 m/s subsonic-to-supersonic but projectile mass (5 kg) is large relative to drag over ~1 km scale; expected order of magnitude: angle ~30-55 deg, required v likely well under the 450 m/s cap for the 1200 m case (vacuum range R=v^2 sin2t/g, so v~sqrt(R*g/sin2t) ~ 150-170 m/s even at modest t, so 450 m/s cap is a generous headroom, not the binding constraint for this specific case). Divergence check vs Node 2b's verified number is required later.",
    },
)
print("done")
