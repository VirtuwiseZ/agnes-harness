import sys
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby.json"

out = audit_log.append_record(state, "node1_task_spec", {
    "problem_id": "2013A",
    "action": "created task state file + jupiter_flyby_params.json + internal prior; session key recorded from runtime context",
    "session_key": "f4d970e3-39c4-4bc2-a6bf-10f24cb6f6cf",
})
print("recorded:", out["artifact_id"])

# quick write-back verification read
import json
with open(state, "r", encoding="utf-8") as f:
    st = json.load(f)
print("audit_logs len:", len(st["audit_logs"]),
      "session_key:", st["session_key"],
      "stage:", st["stage"])
print("last log source:", st["audit_logs"][-1]["source"])
