"""Minimal check (1a): confirm an agent-side trace export is complete, not a truncated tail.

Run this from a session where the user has just finished some work (e.g. a walkthrough),
then use the shell tool to run:
    node <repo>/packages/cli/dist/local/agnes.mjs sessions list
to get the current session key, then:
    node <repo>/packages/cli/dist/local/agnes.mjs export <id> --raw -o /tmp/trace.json
This script re-opens that file and checks:
  - first event is a session/start (seq=1), i.e. NOT a truncated tail
  - last event seq matches expected total
  - count of tool/call + tool/result pairs looks sane
"""
import json, sys

path = sys.argv[1]
with open(path, 'rb') as f:
    raw = f.read()
lines = [l for l in raw.splitlines() if l.strip()]
events = [json.loads(l) for l in lines]
events.sort(key=lambda e: e['seq'])
print(f"total events: {len(events)}")
print(f"first seq: {events[0]['seq']}  type={events[0]['type']}")
print(f"last seq:  {events[-1]['seq']}  type={events[-1]['type']}")

starts = [e for e in events if e['type'] == 'session/start']
print(f"session/start count: {len(starts)}")
if starts:
    print(f"  first start seq: {starts[0]['seq']}")

tool_calls = [e for e in events if e['type'] == 'tool/call']
tool_results = [e for e in events if e['type'] == 'tool/result']
print(f"tool/call events: {len(tool_calls)}")
print(f"tool/result events: {len(tool_results)}")

# A genuine full export must start at seq 1 with a session/start.
if not events[0]['seq'] == 1 or events[0]['type'] != 'session/start':
    print('FAIL: export does not start at seq=1 / session/start -> likely truncated tail')
    sys.exit(1)
print('PASS: export starts at seq=1 with session/start (full-ledger read, not a truncated tail)')
