import json, urllib.request, re

base = "https://en.wikipedia.org/wiki/"
names = ["Io_(moon)", "Europa_(moon)", "Ganymede_(moon)", "Callisto_(moon)", "Jupiter"]
out = {}
for name in names:
    url = base + name
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "physics-agent/1.0 (structured data fetch)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", "replace")
        out[name] = {"url": url, "http_status": 200, "length": len(text), "text": text}
    except Exception as e:
        out[name] = {"url": url, "error": str(e)}
        print("FAILED", name, str(e)[:120])

for name, d in out.items():
    if "text" in d:
        fn = "E:/agh-test/" + name.replace("(", "_").replace(")", "").replace(".", "_") + ".html"
        with open(fn, "w", encoding="utf-8") as f:
            f.write(d["text"])
        print("saved", fn, "len", d["length"])
