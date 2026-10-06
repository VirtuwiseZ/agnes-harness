#!/usr/bin/env python3
"""verify trace2 (ability-test run 02) export completeness.
Mirrors the PASS criteria used for walkthrough 1:
- all seq values form an unbroken 1..N sequence
- exactly one session/start at seq 1
- tool/call count == tool/result count
- every tool/call toolUseId has a matching tool/result toolUseId
"""
import json, sys, collections

path = r"E:\agnes-harness\dev-notes\self-tests\02\test2-trace-events\events.jsonl"
events = []
seqs = []
type_counts = collections.Counter()
call_ids = []
result_ids = []
with open(path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        events.append(ev)
        seqs.append(ev.get("seq"))
        t = ev.get("type", "")
        type_counts[t] += 1
        if t == "tool/call":
            call_ids.append((ev.get("data", {}).get("toolUseId"), ev.get("data", {}).get("name")))
        elif t == "tool/result":
            result_ids.append((ev.get("data", {}).get("toolUseId"), ev.get("data", {}).get("name")))

print(f"total events: {len(events)}")
print(f"seq range: {min(seqs)}..{max(seqs)}")
gaps = [i for i in range(1, max(seqs)+1) if i not in set(seqs)]
print(f"seq gaps: {gaps[:10]}{'...' if len(gaps)>10 else ''} (count={len(gaps)})")
dupes = [s for s,c in collections.Counter(seqs).items() if c>1]
print(f"duplicate seq: {dupes[:10]} (count={len(dupes)})")

starts = [e for e in events if e.get("type")=="session/start"]
print(f"session/start count: {len(starts)}")
for e in starts:
    print(f"  seq={e.get('seq')} key={e.get('data',{}).get('key')}")

print(f"tool/call count: {len(call_ids)}")
print(f"tool/result count: {len(result_ids)}")
call_id_set = {c[0] for c in call_ids if c[0]}
result_id_set = {r[0] for r in result_ids if r[0]}
matched = call_id_set & result_id_set
unmatched_call = call_id_set - result_id_set
unmatched_result = result_id_set - call_id_set
print(f"matched pairs: {len(matched)}")
print(f"call without result: {len(unmatched_call)}")
if unmatched_call:
    for c in sorted(unmatched_call):
        name = next((n for cid,n in call_ids if cid==c), "?")
        print(f"  {c} ({name})")
print(f"result without call: {len(unmatched_result)}")
if unmatched_result:
    for r in sorted(unmatched_result):
        name = next((n for rid,n in result_ids if rid==r), "?")
        print(f"  {r} ({name})")

tool_name_counts = collections.Counter(n for _,n in call_ids if n)
print("\ntool/call by name:")
for name, c in tool_name_counts.most_common():
    print(f"  {name}: {c}")

# §5 check: any tool/call touching dev-notes/
print("\n§5 dev-notes/ reference check:")
dev_notes_hits = []
for ev in events:
    if ev.get("type") in ("tool/call", "tool/result"):
        blob = json.dumps(ev.get("data", {}), ensure_ascii=False)
        if "dev-notes" in blob:
            dev_notes_hits.append((ev.get("seq"), ev.get("type"), ev.get("data",{}).get("name")))
print(f"  hits: {len(dev_notes_hits)}")
for h in dev_notes_hits[:20]:
    print(f"   seq={h[0]} type={h[1]} tool={h[2]}")

# artifact_id cross-check placeholder
print("\ndone")
