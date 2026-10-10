import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

STATE = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby.json"
st = json.load(open(STATE, encoding="utf-8"))
st["stage"] = "done"
st["report"]["traceability"]["node4_html"] = "program-design/runtime/report_2013A_jupiter_flyby.html (trace: trace_capture_converted_f4d970e3.jsonl)"

audit_log.append_record(STATE, "node4_html_rendered", {
    "html": "program-design/runtime/report_2013A_jupiter_flyby.html",
    "trace": "program-design/runtime/trace_capture_converted_f4d970e3.jsonl",
    "session_key": st["session_key"],
    "figures_dir": "program-design/runtime/figures_2013A_jupiter_flyby (3 figures inlined)"
})
json.dump(st, open(STATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("done. stage:", st["stage"])
