import importlib
for m in ("astropy", "sunpy", "spacepy"):
    try:
        mod = importlib.import_module(m)
        print(m, "OK", getattr(mod, "__version__", ""))
    except Exception as e:
        print(m, "MISSING", type(e).__name__, str(e)[:80])

# also test: does astropy have constants we could use?
try:
    import astropy.constants as c
    print("G:", c.G.value, c.G.unit, "| GM_sun:", c.GM_sun.value, c.GM_sun.unit)
except Exception as e:
    print("astropy.constants unavailable:", e)
