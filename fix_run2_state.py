p = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
raw = open(p, encoding="utf-8").read()

old1 = '"a5-NEW-this-run (geometry, stated precisely, not inherited): For a DECCELERATION maneuver'
new1 = '"a5_this_run_geometry": "For a DECCELERATION maneuver'
old2 = '"a6-NEW-this-run (chained construction, explicit): a two-encounter maneuver'
new2 = '"a6_this_run_chained": "a two-encounter maneuver'

if old1 in raw:
    raw = raw.replace(old1, new1)
    print("fixed a5 key")
if old2 in raw:
    raw = raw.replace(old2, new2)
    print("fixed a6 key")

open(p, "w", encoding="utf-8").write(raw)

import json
try:
    json.load(open(p, encoding="utf-8"))
    print("VALID JSON now")
except Exception as e:
    print("still invalid:", e)
