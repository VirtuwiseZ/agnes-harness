import sys
import os
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

base = r"E:\agnes-harness\dev-notes\第三方数据\figtest\data"
os.makedirs(base, exist_ok=True)

url = ("https://power.larc.nasa.gov/api/temporal/daily/regional?"
       "latitude-min=34&latitude-max=38&longitude-min=138&longitude-max=142&"
       "parameters=T2M&community=SB&start=20240701&end=20240731&format=CSV")
r = requests.get(url, timeout=120)
r.raise_for_status()
path = os.path.join(base, "nasa_power_t2m_tokyo_202407.csv")
with open(path, "wb") as f:
    f.write(r.content)
print("OK", path, len(r.content), "bytes")
print("first 5 lines:")
print("\n".join(r.text.splitlines()[:5]))
