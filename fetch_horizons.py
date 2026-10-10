import urllib.request, json
urls = [
    "https://ssd.jpl.nasa.gov/api/horizons.api?format=json&OBJ_DATA=YES&MAKE_EPHEM=NO&COMMAND='599'",
    "https://ssd-api.jpl.nasa.gov/horizons.api?format=json&OBJ_DATA=YES&MAKE_EPHEM=NO&COMMAND='599'",
]
for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "physics-agent/1.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read().decode("utf-8"))
            print("OK", u, "->", json.dumps(data)[:600])
    except Exception as e:
        print("FAIL", u, "->", type(e).__name__, str(e)[:150])
