import json, os, glob

base = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# --- trace ---
events = [
    ("session/start", {"key": "synthetic-1", "preset": "standard-windows"}),
    ("user/message", {"content": [{"type": "text", "text": "synthetic sample prompt"}]}),
    ("turn/start", {"turn": 1}),
    ("tool/call", {"toolUseId": "t0", "name": "write",
                   "args": {"path": "program-design/runtime/problem_state_sample.json",
                            "content": "{\"task\": {\"problem_id\": \"space-diving\"}}"},
                   "ordinal": 0}),
    ("tool/result", {"toolUseId": "t0", "content": [{"type": "text", "text": "written"}], "isError": False}),
    ("tool/call", {"toolUseId": "t1", "name": "web_fetch",
                   "args": {"url": "https://example.wikipedia.org/atmosphere"}, "ordinal": 1}),
    ("tool/result", {"toolUseId": "t1",
                     "content": [{"type": "text", "text": "WEB_BLOCKED_URL"}], "isError": True}),
    ("tool/call", {"toolUseId": "t2", "name": "shell",
                   "args": {"command": "python ode_model.py"}, "ordinal": 2}),
    ("tool/result", {"toolUseId": "t2", "content": [{"type": "text", "text": "ok"}], "isError": False}),
    ("turn/end", {"turn": 1}),
]

with open(os.path.join(base, "sample_trace_synthetic.json"), "w", encoding="utf-8") as f:
    for i, (typ, data) in enumerate(events, start=1):
        f.write(json.dumps({"seq": i, "ts": "2026-10-05T00:00:%02d.000Z" % i,
                            "id": "syn-%03d" % i, "type": typ, "lane": "main", "v": 1,
                            "actor": {"id": "system", "org": "local", "role": "system"},
                            "origin": "system", "trust": "trusted", "data": data},
                           ensure_ascii=False) + "\n")

# --- state ---
state = {
    "schema_version": 1,
    "task": {"problem_id": "space-diving-synthetic", "description": "synthetic sample"},
    "stage": "node_2b_modeling",
    "audit_logs": [
        {"source": "agent-direct", "artifact_id": "syn-node1-spec-0001", "args": {"note": "spec written"}},
        {"source": "agent-direct", "artifact_id": "syn-datasrc-0002", "args": {"note": "US Standard Atmosphere 1976"}},
    ],
    "anomalies": [{"type": "data_source_unavailable", "note": "Level 1 blocked, Level 3 fallback"}],
    "verification": {"benchmark_source": None, "comparison_result": None, "max_relative_error": None},
    "report": {"conclusion": "pending", "traceability": {}},
}
with open(os.path.join(base, "sample_state_synthetic.json"), "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

# --- clean up any leftover sample2 files from earlier failed attempts ---
for p in glob.glob(os.path.join(base, "*sample2*")):
    os.remove(p)

print("ok")
