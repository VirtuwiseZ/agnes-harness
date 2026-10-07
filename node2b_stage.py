"""Stage transition node_1_spec -> node_2a_routing (already effectively at
node_2a via the knowledge_routing write), now -> node_2b_modeling after the
template adaptation check is recorded. Updates stage + audit log."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
state_path = os.path.join(HERE, "program-design", "runtime", "problem_state_2025B_artillery.json")

with open(state_path, "r", encoding="utf-8") as f:
    state = json.load(f)

state["stage"] = "node_2b_modeling"

with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

import sys
sys.path.insert(0, os.path.join(HERE, "program-design", "hooks"))
import audit_log
audit_log.append_record(
    state_path=state_path,
    source="stage_transition",
    args={"from": "node_2a_routing", "to": "node_2b_modeling",
          "reason": "Template adaptation check recorded; governance pipeline advancing to modeling/verification phase."},
)
print("stage -> node_2b_modeling")
