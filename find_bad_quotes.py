import json
p = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
raw = open(p, encoding="utf-8").read()
# Find every unescaped double-quote that lies INSIDE a JSON string value by locating
# the a5 line and counting quotes outside of proper escaping.
import re
line23 = [l for l in raw.splitlines() if "a5-NEW" in l][0]
# crude: find all `"` occurrences and check the one(s) that break pairing
count = 0
in_str = False
problem_positions = []
for i, ch in enumerate(line23):
    if ch == "\\":
        continue
    if ch == '"':
        count += 1
        if count > 2:  # after the opening key-quote + closing-key-quote, any MORE quotes must be escaped \"
            problem_positions.append(i)
print("total double-quote chars on a5 line:", count)
print("positions beyond 2 (unescaped-inner-quote suspects):", problem_positions)
for pos in problem_positions[:5]:
    print(f"  ...{line23[max(0,pos-40):pos+40]!r}")
