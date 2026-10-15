import sys
import os
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = r"E:\agnes-harness\dev-notes\第三方数据\figtest\data"
os.makedirs(BASE, exist_ok=True)

targets = {
    "winequality-red.csv": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
    "winequality-white.csv": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
    "owid_co2_per_country.csv": "https://ourworldindata.org/grapher/annual-co2-emissions-per-country.csv?v=1&csvType=full&useColumnShortNames=false",
}
for name, url in targets.items():
    path = os.path.join(BASE, name)
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"OK {name} {len(r.content)} bytes")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}")
