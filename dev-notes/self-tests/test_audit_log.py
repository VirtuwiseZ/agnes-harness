"""Self-test for audit_log.py — not a dependency of the hook itself, just a
developer check that append/verify + tamper-detection actually work."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import audit_log  # noqa: E402

STATE = "_audit_selftest_state.json"


def run():
    if os.path.exists(STATE):
        os.remove(STATE)
    for i in range(3):
        out = audit_log.append_record(STATE, source=f"tool_{i}", args={"n": i})
        print("appended", out["artifact_id"][:12])

    verify = audit_log.verify_chain(STATE)
    print("intact verify:", verify["verdict"])
    assert verify["verdict"] == "PASS"

    # Simulate out-of-band tampering: mutate one record's args, then re-verify.
    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)
    state["audit_logs"][1]["args"]["n"] = 999  # unauthorized mutation
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    verify2 = audit_log.verify_chain(STATE)
    print("tampered verify:", verify2["verdict"])
    for rec in verify2["records"]:
        print(" ", rec)
    assert verify2["verdict"] == "FAIL"
    assert not verify2["records"][1]["ok"]

    os.remove(STATE)
    print("all audit_log self-tests passed")


if __name__ == "__main__":
    run()
