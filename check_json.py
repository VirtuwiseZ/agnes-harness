import json
p = r"E:\agh-test\program-design\runtime\problem_state_2013A_jupiter_flyby_run2.json"
try:
    json.load(open(p, encoding="utf-8"))
    print("valid json")
except Exception as e:
    print("INVALID:", e)
    with open(p, encoding="utf-8") as f:
        lines = f.readlines()
    ln = int(str(e).split(":")[1].split(",")[0]) if ":" in str(e) else None
    if ln:
        print("context around line", ln)
        for i in range(max(0, ln-2), min(len(lines), ln+2)):
            print(f"{i+1}: {lines[i]!r}")
