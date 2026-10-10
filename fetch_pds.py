import urllib.request, json, re

# PDS: fetch system metadata for Jovian satellite fact sheets
urls = [
    "https://pds-atlas.nmsu.edu/jovian-factsheet/satellites.html",
    "https://nssdc.gsfc.nasa.gov/planetary/factsheet/satellite_facts.html",
    "https://ssd.jpl.nasa.gov/sat.html",
]
for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 physics-agent"})
        with urllib.request.urlopen(req, timeout=30) as r:
            t = r.read().decode("utf-8", "replace")
        print("OK", u, "len", len(t))
    except Exception as e:
        print("FAIL", u, type(e).__name__, str(e)[:100])
