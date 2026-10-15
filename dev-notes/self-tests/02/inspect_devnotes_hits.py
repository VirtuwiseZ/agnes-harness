#!/usr/bin/env python3
import json, sys, os

path = r"E:\agnes-harness\dev-notes\self-tests\02\test2-trace-events\events.jsonl"
targets = [45, 292, 2561, 2612, 2616, 2697, 2714]
by_seq = {}
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        if ev.get("seq") in targets:
            by_seq[ev["seq"]] = ev

outpath = r"E:\agnes-harness\dev-notes\self-tests\02\devnotes_hits_dump.txt"
with open(outpath, "w", encoding="utf-8") as out:
    for seq in targets:
        ev = by_seq.get(seq)
        if not ev:
            out.write(f"\n=== seq={seq} NOT FOUND ===\n")
            continue
        out.write(f"\n=== seq={seq} type={ev.get('type')} name={ev.get('data',{}).get('name')} ===\n")
        out.write(json.dumps(ev.get("data", {}), ensure_ascii=False, indent=2)[:4000])
        out.write("\n")
print("written", outpath)
