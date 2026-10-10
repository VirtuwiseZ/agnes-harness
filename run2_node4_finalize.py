import sys, json
sys.path.insert(0, r"E:\agh-test\program-design\hooks")
import audit_log

state = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
st = json.load(open(state, encoding="utf-8"))
st["stage"] = "done"
st["report"]["traceability"]["node4_html"] = "program-design/runtime/report_2013A_jupiter_flyby_run2.html (4 figures inlined as data: URIs, verified by re-render + count check)"

audit_log.append_record(state, "run2_node4_html_rendered", {
    "html": "program-design/runtime/report_2013A_jupiter_flyby_run2.html",
    "trace": "program-design/runtime/trace_capture_converted_f4d970e3.jsonl",
    "session_key": st["session_key"],
    "figures_dir": "program-design/runtime/figures_2013A_jupiter_flyby_run2 (4 figures, all inlined)"
})
json.dump(st, open(state, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("run #2 stage: done")
